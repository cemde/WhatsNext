"""Status dashboard command."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..config import get_config, get_server_from_config

console = Console()


def show_status(
    project: Optional[str] = typer.Option(None, "--project", "-P", help="Project name"),
    host: Optional[str] = typer.Option(None, "--server", "-s", help="Server host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show system status dashboard.

    Displays an overview of the WhatsNext system including:
    - Server connection status
    - Project queue summary
    - Active clients/workers
    """
    import json

    import requests

    config = get_config(config_file)
    server = get_server_from_config(config, host, port)

    status_data: dict = {
        "server": {"url": server.url, "status": "unknown"},
        "project": None,
        "queue": {},
        "clients": {"total": 0, "active": 0},
    }

    # Check server connectivity
    try:
        response = requests.get(f"{server.url}/projects/", params={"limit": 1}, timeout=5)
        response.raise_for_status()
        status_data["server"]["status"] = "connected"
    except requests.RequestException as e:
        status_data["server"]["status"] = "disconnected"
        status_data["server"]["error"] = str(e)
        if json_output:
            console.print(json.dumps(status_data, indent=2))
        else:
            console.print(f"[red]Cannot connect to server at {server.url}[/red]")
            console.print(f"[dim]Error: {e}[/dim]")
        raise typer.Exit(1)

    # Get project info
    project_name = project or config.project
    project_id = None

    if project_name:
        try:
            proj_response = requests.get(f"{server.url}/projects/name/{project_name}")
            proj_response.raise_for_status()
            proj_data = proj_response.json()
            project_id = proj_data["id"]
            status_data["project"] = {
                "name": proj_data["name"],
                "id": proj_data["id"],
                "status": proj_data["status"],
            }
        except requests.RequestException:
            status_data["project"] = {"name": project_name, "error": "not found"}

    # Get queue stats if we have a project
    if project_id:
        try:
            jobs_response = requests.get(f"{server.url}/jobs/", params={"project_id": project_id, "limit": 10000})
            jobs_response.raise_for_status()
            jobs = jobs_response.json()

            by_status = {}
            for job in jobs:
                s = job.get("status", "UNKNOWN")
                by_status[s] = by_status.get(s, 0) + 1

            status_data["queue"] = {
                "total": len(jobs),
                "by_status": by_status,
            }
        except requests.RequestException:
            pass

    # Get client stats
    try:
        clients_response = requests.get(f"{server.url}/clients/", params={"active_only": False, "limit": 1000})
        clients_response.raise_for_status()
        all_clients = clients_response.json()
        active_clients = [c for c in all_clients if c.get("is_active")]
        status_data["clients"] = {
            "total": len(all_clients),
            "active": len(active_clients),
        }
    except requests.RequestException:
        pass

    if json_output:
        console.print(json.dumps(status_data, indent=2))
        return

    # Display dashboard
    console.print()
    console.print(Panel("[bold]WhatsNext Status Dashboard[/bold]", style="cyan"))

    # Server status
    server_status = status_data["server"]["status"]
    server_style = "green" if server_status == "connected" else "red"
    console.print(f"\n[bold]Server:[/bold] [{server_style}]{server_status}[/{server_style}]")
    console.print(f"  URL: {server.url}")

    # Project status
    console.print("\n[bold]Project:[/bold]", end=" ")
    if status_data["project"]:
        if "error" in status_data["project"]:
            console.print(f"[red]{project_name} (not found)[/red]")
        else:
            proj_status = status_data["project"]["status"]
            proj_style = "green" if proj_status == "ACTIVE" else "dim"
            console.print(f"[cyan]{status_data['project']['name']}[/cyan] [{proj_style}]{proj_status}[/{proj_style}]")
    else:
        console.print("[dim]None configured[/dim]")

    # Queue summary
    if status_data["queue"]:
        queue = status_data["queue"]
        console.print(f"\n[bold]Queue Summary:[/bold] {queue['total']} total jobs")

        status_styles = {
            "PENDING": "blue",
            "QUEUED": "cyan",
            "RUNNING": "yellow",
            "COMPLETED": "green",
            "FAILED": "red",
            "BLOCKED": "magenta",
        }

        by_status: dict = queue.get("by_status", {})  # type: ignore[assignment]
        if by_status:
            status_order = ["RUNNING", "PENDING", "QUEUED", "BLOCKED", "COMPLETED", "FAILED"]
            status_parts = []
            for s in status_order:
                count = by_status.get(s, 0)
                if count > 0:
                    style = status_styles.get(s, "dim")
                    status_parts.append(f"[{style}]{s}: {count}[/{style}]")
            if status_parts:
                console.print("  " + " | ".join(status_parts))
    elif project_name:
        console.print("\n[bold]Queue:[/bold] [dim]No jobs[/dim]")

    # Clients summary
    clients = status_data["clients"]
    console.print(f"\n[bold]Workers:[/bold] {clients['active']} active / {clients['total']} registered")

    # Show active clients if any
    if clients["active"] > 0:
        try:
            active_response = requests.get(f"{server.url}/clients/", params={"active_only": True, "limit": 5})
            active_response.raise_for_status()
            active_list = active_response.json()

            if active_list:
                table = Table(show_header=True, header_style="dim", box=None)
                table.add_column("Name")
                table.add_column("Entity")
                table.add_column("Resources")

                for client in active_list[:5]:
                    resources = f"{client.get('available_cpu', 0)} CPU"
                    if client.get("available_accelerators", 0) > 0:
                        resources += f", {client['available_accelerators']} accel"
                    table.add_row(
                        client.get("name", client["id"][:12]),
                        client.get("entity", "-"),
                        resources,
                    )

                console.print(table)
                if len(active_list) > 5:
                    console.print(f"  [dim]... and {len(active_list) - 5} more[/dim]")
        except requests.RequestException:
            pass

    # Config info
    if config.config_path:
        console.print(f"\n[dim]Config: {config.config_path}[/dim]")

    console.print()
