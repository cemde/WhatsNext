"""Project management commands."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..config import get_config, get_server_from_config

app = typer.Typer(no_args_is_help=True)
console = Console()


def get_server(host: Optional[str], port: Optional[int], config_file: Optional[Path]):
    """Get server connection from config/options."""
    config = get_config(config_file)
    return get_server_from_config(config, host, port)


@app.command("ls")
def list_projects(
    host: Optional[str] = typer.Option(None, "--server", "-s", help="Server host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
    status_filter: Optional[str] = typer.Option("ACTIVE", "--status", help="Filter by status (ACTIVE, ARCHIVED, or 'all')"),
    limit: int = typer.Option(50, "--limit", "-n", help="Maximum number of projects to show"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List all projects."""
    import json

    import requests

    config = get_config(config_file)
    server = get_server_from_config(config, host, port)

    # Build request
    params = {"limit": limit}
    if status_filter and status_filter.lower() != "all":
        params["status_filter"] = status_filter.upper()

    try:
        response = requests.get(f"{server.url}/projects/", params=params)
        response.raise_for_status()
        projects = response.json()
    except requests.RequestException as e:
        console.print(f"[red]Error connecting to server: {e}[/red]")
        raise typer.Exit(1)

    if json_output:
        console.print(json.dumps(projects, indent=2, default=str))
        return

    if not projects:
        console.print("[dim]No projects found[/dim]")
        return

    # Display as table
    table = Table(title="Projects")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Status")
    table.add_column("Description")
    table.add_column("Created", style="dim")

    for proj in projects:
        status_style = "green" if proj["status"] == "ACTIVE" else "dim"
        table.add_row(
            str(proj["id"]),
            proj["name"],
            f"[{status_style}]{proj['status']}[/{status_style}]",
            proj.get("description", "")[:40] or "-",
            proj["created_at"][:10] if proj.get("created_at") else "-",
        )

    console.print(table)
    console.print(f"[dim]Showing {len(projects)} project(s)[/dim]")


@app.command("show")
def show_project(
    name: str = typer.Argument(..., help="Project name or ID"),
    host: Optional[str] = typer.Option(None, "--server", "-s", help="Server host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show details for a specific project."""
    import json

    import requests

    config = get_config(config_file)
    server = get_server_from_config(config, host, port)

    # Try by name first, then by ID
    try:
        response = requests.get(f"{server.url}/projects/name/{name}")
        if response.status_code == 404:
            # Try as ID
            response = requests.get(f"{server.url}/projects/{name}")
        response.raise_for_status()
        project = response.json()
    except requests.RequestException as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    if json_output:
        console.print(json.dumps(project, indent=2, default=str))
        return

    # Get queue stats
    try:
        queue_response = requests.get(f"{server.url}/jobs/", params={"project_id": project["id"], "limit": 1000})
        queue_response.raise_for_status()
        jobs = queue_response.json()
    except requests.RequestException:
        jobs = []

    # Count by status
    status_counts = {}
    for job in jobs:
        s = job.get("status", "UNKNOWN")
        status_counts[s] = status_counts.get(s, 0) + 1

    # Display
    console.print(f"\n[bold cyan]Project: {project['name']}[/bold cyan]")
    console.print("─" * 40)
    console.print(f"ID:          {project['id']}")
    console.print(f"Status:      {project['status']}")
    console.print(f"Description: {project.get('description') or '-'}")
    console.print(f"Created:     {project.get('created_at', '-')}")
    console.print(f"Updated:     {project.get('updated_at', '-')}")

    if status_counts:
        console.print("\n[bold]Queue Summary:[/bold]")
        for status, count in sorted(status_counts.items()):
            style = {"COMPLETED": "green", "FAILED": "red", "RUNNING": "yellow", "PENDING": "blue"}.get(status, "dim")
            console.print(f"  [{style}]{status}:[/{style}] {count}")


@app.command("create")
def create_project(
    name: str = typer.Argument(..., help="Project name"),
    description: str = typer.Option("", "--description", "-d", help="Project description"),
    host: Optional[str] = typer.Option(None, "--server", "-s", help="Server host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
):
    """Create a new project."""
    import requests

    config = get_config(config_file)
    server = get_server_from_config(config, host, port)

    try:
        response = requests.post(
            f"{server.url}/projects/",
            json={"name": name, "description": description, "status": "ACTIVE"},
        )
        response.raise_for_status()
        project = response.json()
    except requests.RequestException as e:
        console.print(f"[red]Error creating project: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Created project:[/green] {project['name']} (ID: {project['id']})")


@app.command("delete")
def delete_project(
    name: str = typer.Argument(..., help="Project name"),
    host: Optional[str] = typer.Option(None, "--server", "-s", help="Server host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a project."""
    import requests
    from rich.prompt import Confirm

    if not force:
        if not Confirm.ask(f"[yellow]Delete project '{name}'? This cannot be undone.[/yellow]"):
            raise typer.Abort()

    config = get_config(config_file)
    server = get_server_from_config(config, host, port)

    try:
        response = requests.delete(f"{server.url}/projects/name/{name}")
        response.raise_for_status()
    except requests.RequestException as e:
        console.print(f"[red]Error deleting project: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Deleted project:[/green] {name}")


@app.command("archive")
def archive_project(
    name: str = typer.Argument(..., help="Project name"),
    host: Optional[str] = typer.Option(None, "--server", "-s", help="Server host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
):
    """Archive a project (set status to ARCHIVED)."""
    import requests

    config = get_config(config_file)
    server = get_server_from_config(config, host, port)

    # First get the project
    try:
        response = requests.get(f"{server.url}/projects/name/{name}")
        response.raise_for_status()
        project = response.json()
    except requests.RequestException as e:
        console.print(f"[red]Error finding project: {e}[/red]")
        raise typer.Exit(1)

    # Update status
    try:
        response = requests.put(
            f"{server.url}/projects/{project['id']}",
            json={"name": project["name"], "description": project.get("description", ""), "status": "ARCHIVED"},
        )
        response.raise_for_status()
    except requests.RequestException as e:
        console.print(f"[red]Error archiving project: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Archived project:[/green] {name}")
