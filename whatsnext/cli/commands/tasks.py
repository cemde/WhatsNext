"""Task management commands."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..config import get_config, get_server_from_config

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("ls")
def list_tasks(
    project: Optional[str] = typer.Option(None, "--project", "-P", help="Project name (uses config default if not set)"),
    host: Optional[str] = typer.Option(None, "--server", "-s", help="Server host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
    limit: int = typer.Option(50, "--limit", "-n", help="Maximum number of tasks to show"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List tasks in a project."""
    import json

    import requests

    config = get_config(config_file)
    server = get_server_from_config(config, host, port)

    # Get project ID
    project_name = project or config.project
    if not project_name:
        console.print("[red]No project specified. Use --project or set 'project' in .whatsnext[/red]")
        raise typer.Exit(1)

    try:
        proj_response = requests.get(f"{server.url}/projects/name/{project_name}")
        proj_response.raise_for_status()
        proj_data = proj_response.json()
        project_id = proj_data["id"]
    except requests.RequestException as e:
        console.print(f"[red]Error finding project: {e}[/red]")
        raise typer.Exit(1)

    # Get tasks
    try:
        response = requests.get(f"{server.url}/tasks/", params={"project_id": project_id, "limit": limit})
        response.raise_for_status()
        tasks = response.json()
    except requests.RequestException as e:
        console.print(f"[red]Error fetching tasks: {e}[/red]")
        raise typer.Exit(1)

    if json_output:
        console.print(json.dumps(tasks, indent=2, default=str))
        return

    if not tasks:
        console.print(f"[dim]No tasks found in project '{project_name}'[/dim]")
        return

    table = Table(title=f"Tasks in '{project_name}'")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("CPU Req.", justify="right")
    table.add_column("Accel. Req.", justify="right")
    table.add_column("Created", style="dim")

    for task in tasks:
        table.add_row(
            str(task["id"]),
            task["name"],
            str(task.get("required_cpu", 1)),
            str(task.get("required_accelerators", 0)),
            task["created_at"][:10] if task.get("created_at") else "-",
        )

    console.print(table)


@app.command("show")
def show_task(
    name: str = typer.Argument(..., help="Task name or ID"),
    project: Optional[str] = typer.Option(None, "--project", "-P", help="Project name"),
    host: Optional[str] = typer.Option(None, "--server", "-s", help="Server host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show details for a specific task."""
    import json

    import requests

    config = get_config(config_file)
    server = get_server_from_config(config, host, port)

    project_name = project or config.project

    # Try by ID first
    try:
        response = requests.get(f"{server.url}/tasks/{name}")
        if response.status_code == 404 and project_name:
            # Try by name with project filter
            proj_response = requests.get(f"{server.url}/projects/name/{project_name}")
            proj_response.raise_for_status()
            project_id = proj_response.json()["id"]
            response = requests.get(f"{server.url}/tasks/name/{name}", params={"project_id": project_id})
        response.raise_for_status()
        task = response.json()
    except requests.RequestException as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    if json_output:
        console.print(json.dumps(task, indent=2, default=str))
        return

    console.print(f"\n[bold cyan]Task: {task['name']}[/bold cyan]")
    console.print("─" * 40)
    console.print(f"ID:                  {task['id']}")
    console.print(f"Project ID:          {task['project_id']}")
    console.print(f"Required CPUs:       {task.get('required_cpu', 1)}")
    console.print(f"Required Accelerators: {task.get('required_accelerators', 0)}")
    if task.get("command_template"):
        console.print(f"Command Template:    {task['command_template']}")
    console.print(f"Created:             {task.get('created_at', '-')}")


@app.command("create")
def create_task(
    name: str = typer.Argument(..., help="Task name"),
    project: Optional[str] = typer.Option(None, "--project", "-P", help="Project name"),
    cpu: int = typer.Option(1, "--cpu", help="Required CPUs"),
    accelerators: int = typer.Option(0, "--accelerators", "--accel", help="Required accelerators"),
    host: Optional[str] = typer.Option(None, "--server", "-s", help="Server host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
):
    """Create a new task in a project."""
    import requests

    config = get_config(config_file)
    server = get_server_from_config(config, host, port)

    project_name = project or config.project
    if not project_name:
        console.print("[red]No project specified. Use --project or set 'project' in .whatsnext[/red]")
        raise typer.Exit(1)

    # Get project ID
    try:
        proj_response = requests.get(f"{server.url}/projects/name/{project_name}")
        proj_response.raise_for_status()
        project_id = proj_response.json()["id"]
    except requests.RequestException as e:
        console.print(f"[red]Error finding project: {e}[/red]")
        raise typer.Exit(1)

    # Create task
    try:
        response = requests.post(
            f"{server.url}/tasks/",
            json={
                "name": name,
                "project_id": project_id,
                "required_cpu": cpu,
                "required_accelerators": accelerators,
            },
        )
        response.raise_for_status()
        task = response.json()
    except requests.RequestException as e:
        console.print(f"[red]Error creating task: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Created task:[/green] {task['name']} (ID: {task['id']})")


@app.command("delete")
def delete_task(
    task_id: int = typer.Argument(..., help="Task ID"),
    host: Optional[str] = typer.Option(None, "--server", "-s", help="Server host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a task."""
    import requests
    from rich.prompt import Confirm

    if not force:
        if not Confirm.ask(f"[yellow]Delete task {task_id}?[/yellow]"):
            raise typer.Abort()

    config = get_config(config_file)
    server = get_server_from_config(config, host, port)

    try:
        response = requests.delete(f"{server.url}/tasks/{task_id}")
        response.raise_for_status()
    except requests.RequestException as e:
        console.print(f"[red]Error deleting task: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Deleted task:[/green] {task_id}")
