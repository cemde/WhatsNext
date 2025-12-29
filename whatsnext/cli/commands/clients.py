"""Client/worker management commands."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..config import get_config, get_server_from_config

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("ls")
def list_clients(
    host: Optional[str] = typer.Option(None, "--server", "-s", help="Server host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
    all_clients: bool = typer.Option(False, "--all", "-a", help="Show all clients including inactive"),
    limit: int = typer.Option(50, "--limit", "-n", help="Maximum number of clients to show"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List connected clients/workers."""
    import json

    import requests

    config = get_config(config_file)
    server = get_server_from_config(config, host, port)

    try:
        response = requests.get(
            f"{server.url}/clients/",
            params={"limit": limit, "active_only": not all_clients},
        )
        response.raise_for_status()
        clients = response.json()
    except requests.RequestException as e:
        console.print(f"[red]Error connecting to server: {e}[/red]")
        raise typer.Exit(1)

    if json_output:
        console.print(json.dumps(clients, indent=2, default=str))
        return

    if not clients:
        console.print("[dim]No clients connected[/dim]")
        return

    table = Table(title="Connected Clients")
    table.add_column("ID", style="dim", max_width=20)
    table.add_column("Name", style="cyan")
    table.add_column("Entity")
    table.add_column("CPUs", justify="right")
    table.add_column("Accels", justify="right")
    table.add_column("Active")
    table.add_column("Last Heartbeat", style="dim")

    for client in clients:
        is_active = client.get("is_active", False)
        active_style = "green" if is_active else "red"
        table.add_row(
            client["id"][:16] + "..." if len(client["id"]) > 16 else client["id"],
            client.get("name", "-"),
            client.get("entity", "-"),
            str(client.get("available_cpu", 0)),
            str(client.get("available_accelerators", 0)),
            f"[{active_style}]{'Yes' if is_active else 'No'}[/{active_style}]",
            client.get("last_heartbeat", "-")[:19] if client.get("last_heartbeat") else "-",
        )

    console.print(table)
    console.print(f"[dim]Showing {len(clients)} client(s)[/dim]")


@app.command("show")
def show_client(
    client_id: str = typer.Argument(..., help="Client ID"),
    host: Optional[str] = typer.Option(None, "--server", "-s", help="Server host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show details for a specific client."""
    import json

    import requests

    config = get_config(config_file)
    server = get_server_from_config(config, host, port)

    try:
        response = requests.get(f"{server.url}/clients/{client_id}")
        response.raise_for_status()
        client = response.json()
    except requests.RequestException as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    if json_output:
        console.print(json.dumps(client, indent=2, default=str))
        return

    is_active = client.get("is_active", False)
    active_style = "green" if is_active else "red"

    console.print(f"\n[bold cyan]Client: {client.get('name', client['id'])}[/bold cyan]")
    console.print("─" * 50)
    console.print(f"ID:             {client['id']}")
    console.print(f"Name:           {client.get('name', '-')}")
    console.print(f"Entity:         {client.get('entity', '-')}")
    console.print(f"Description:    {client.get('description') or '-'}")
    console.print(f"Available CPUs: {client.get('available_cpu', 0)}")
    console.print(f"Accelerators:   {client.get('available_accelerators', 0)}")
    console.print(f"Active:         [{active_style}]{'Yes' if is_active else 'No'}[/{active_style}]")
    console.print(f"Last Heartbeat: {client.get('last_heartbeat', '-')}")
    console.print(f"Registered:     {client.get('created_at', '-')}")


@app.command("deactivate")
def deactivate_client(
    client_id: str = typer.Argument(..., help="Client ID"),
    host: Optional[str] = typer.Option(None, "--server", "-s", help="Server host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
):
    """Mark a client as inactive."""
    import requests

    config = get_config(config_file)
    server = get_server_from_config(config, host, port)

    try:
        response = requests.post(f"{server.url}/clients/{client_id}/deactivate")
        response.raise_for_status()
    except requests.RequestException as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Deactivated client:[/green] {client_id}")


@app.command("delete")
def delete_client(
    client_id: str = typer.Argument(..., help="Client ID"),
    host: Optional[str] = typer.Option(None, "--server", "-s", help="Server host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a client registration."""
    import requests
    from rich.prompt import Confirm

    if not force:
        if not Confirm.ask(f"[yellow]Delete client {client_id}?[/yellow]"):
            raise typer.Abort()

    config = get_config(config_file)
    server = get_server_from_config(config, host, port)

    try:
        response = requests.delete(f"{server.url}/clients/{client_id}")
        response.raise_for_status()
    except requests.RequestException as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Deleted client:[/green] {client_id}")
