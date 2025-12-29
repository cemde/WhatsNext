"""Authentication testing command."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from ..config import get_config, get_server_from_config

console = Console()


def test_auth(
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", help="API key to test"),
    host: Optional[str] = typer.Option(None, "--server", "-s", help="Server host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
):
    """Test authentication with the server.

    Verifies that:
    1. The server is reachable
    2. The API key (if required) is valid
    3. You can access protected endpoints

    Examples:
        # Test with API key from command line
        whatsnext test-auth --api-key my-secret-key

        # Test with server that doesn't require auth
        whatsnext test-auth --server localhost --port 8000
    """
    import requests

    config = get_config(config_file)
    server = get_server_from_config(config, host, port)

    console.print(f"\n[bold]Testing connection to {server.url}[/bold]\n")

    # Step 1: Basic connectivity (unauthenticated endpoint)
    console.print("[dim]Step 1:[/dim] Testing basic connectivity...")
    try:
        response = requests.get(f"{server.url}/", timeout=5)
        if response.status_code == 200:
            console.print("  [green]OK[/green] - Server is reachable")
        else:
            console.print(f"  [red]FAIL[/red] - Unexpected status: {response.status_code}")
            raise typer.Exit(1)
    except requests.ConnectionError:
        console.print(f"  [red]FAIL[/red] - Cannot connect to {server.url}")
        console.print("  [dim]Is the server running?[/dim]")
        raise typer.Exit(1)
    except requests.Timeout:
        console.print("  [red]FAIL[/red] - Connection timed out")
        raise typer.Exit(1)

    # Step 2: Database connectivity (unauthenticated endpoint)
    console.print("[dim]Step 2:[/dim] Testing database connectivity...")
    try:
        response = requests.get(f"{server.url}/checkdb", timeout=5)
        if response.status_code == 200:
            console.print("  [green]OK[/green] - Database is connected")
        else:
            console.print(f"  [yellow]WARN[/yellow] - Database check returned: {response.status_code}")
    except requests.RequestException as e:
        console.print(f"  [yellow]WARN[/yellow] - Database check failed: {e}")

    # Step 3: Check if authentication is required
    console.print("[dim]Step 3:[/dim] Checking if authentication is required...")
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key

    try:
        # Try to access projects endpoint (requires auth if enabled)
        response = requests.get(f"{server.url}/projects/", headers=headers, timeout=5)

        if response.status_code == 200:
            if api_key:
                console.print("  [green]OK[/green] - API key is valid")
            else:
                console.print("  [green]OK[/green] - No authentication required (open API)")

            # Show some stats
            projects = response.json()
            console.print(f"  [dim]Found {len(projects)} project(s)[/dim]")

        elif response.status_code == 401:
            if api_key:
                console.print("  [red]FAIL[/red] - API key is invalid or expired")
                console.print("  [dim]Check that your API key matches one configured on the server[/dim]")
                raise typer.Exit(1)
            else:
                console.print("  [yellow]AUTH REQUIRED[/yellow] - Server requires an API key")
                console.print("  [dim]Use --api-key to provide your API key[/dim]")
                raise typer.Exit(1)

        elif response.status_code == 403:
            console.print("  [red]FAIL[/red] - Access forbidden (API key may lack permissions)")
            raise typer.Exit(1)

        elif response.status_code == 429:
            console.print("  [yellow]RATE LIMITED[/yellow] - Too many requests")
            retry_after = response.headers.get("Retry-After", "unknown")
            console.print(f"  [dim]Try again in {retry_after} seconds[/dim]")
            raise typer.Exit(1)

        else:
            console.print(f"  [yellow]WARN[/yellow] - Unexpected status: {response.status_code}")

    except requests.RequestException as e:
        console.print(f"  [red]FAIL[/red] - Request failed: {e}")
        raise typer.Exit(1)

    # Step 4: Test write access (if authenticated)
    console.print("[dim]Step 4:[/dim] Testing API access...")
    try:
        # Try to list clients (another protected endpoint)
        response = requests.get(f"{server.url}/clients/", headers=headers, timeout=5)
        if response.status_code == 200:
            clients = response.json()
            console.print("  [green]OK[/green] - Full API access confirmed")
            console.print(f"  [dim]Found {len(clients)} registered client(s)[/dim]")
        else:
            console.print(f"  [yellow]WARN[/yellow] - Limited access (status: {response.status_code})")
    except requests.RequestException:
        console.print("  [yellow]WARN[/yellow] - Could not verify full API access")

    # Summary
    console.print("\n[bold green]Authentication test passed![/bold green]")
    console.print(f"\nServer: {server.url}")
    if api_key:
        # Show masked key
        masked = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else "****"
        console.print(f"API Key: {masked}")
    else:
        console.print("API Key: [dim]Not required[/dim]")

    if config.config_path:
        console.print(f"Config: {config.config_path}")

    console.print()
