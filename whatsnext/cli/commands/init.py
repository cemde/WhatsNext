"""Initialize .whatsnext configuration file."""

from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console
from rich.prompt import Confirm, Prompt

console = Console()


def init_config(
    server_host: Optional[str] = typer.Option(None, "--server", "-s", help="Server host"),
    server_port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port"),
    project: Optional[str] = typer.Option(None, "--project", help="Default project name"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing config"),
):
    """Initialize a new .whatsnext configuration file.

    Creates a .whatsnext file in the current directory with server and project settings.
    """
    config_path = Path.cwd() / ".whatsnext"

    if config_path.exists() and not force:
        if not Confirm.ask(f"[yellow]{config_path} already exists. Overwrite?[/yellow]"):
            raise typer.Abort()

    # Interactive prompts if not provided via options
    if server_host is None:
        server_host = Prompt.ask("Server host", default="localhost")

    if server_port is None:
        port_str = Prompt.ask("Server port", default="8000")
        server_port = int(port_str)

    if project is None:
        project = Prompt.ask("Default project name", default="")
        if not project:
            project = None

    # Build config
    config = {
        "server": {
            "host": server_host,
            "port": server_port,
        }
    }

    if project:
        config["project"] = project

    # Write config file
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    console.print(f"[green]Created {config_path}[/green]")

    # Show what was created
    console.print("\n[dim]Configuration:[/dim]")
    console.print(f"  Server: {server_host}:{server_port}")
    if project:
        console.print(f"  Project: {project}")
