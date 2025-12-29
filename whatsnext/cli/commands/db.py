"""Database migration commands."""

import subprocess
from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(no_args_is_help=True)
console = Console()


def get_alembic_ini_path() -> Path:
    """Find the alembic.ini file."""
    # Look for alembic.ini relative to the package installation
    # or in the current directory
    candidates = [
        Path.cwd() / "alembic.ini",
        Path(__file__).parent.parent.parent.parent.parent / "alembic.ini",
    ]

    for path in candidates:
        if path.exists():
            return path

    console.print("[red]Error:[/red] Could not find alembic.ini")
    console.print("Make sure you're running from the project root or have alembic.ini in the current directory.")
    raise typer.Exit(1)


def run_alembic(args: list[str]) -> int:
    """Run an alembic command."""
    alembic_ini = get_alembic_ini_path()
    cmd = ["alembic", "-c", str(alembic_ini)] + args

    try:
        result = subprocess.run(cmd, capture_output=False)
        return result.returncode
    except FileNotFoundError:
        console.print("[red]Error:[/red] Alembic not installed.")
        console.print("Install with: pip install whatsnext[server]")
        raise typer.Exit(1)


@app.command(name="upgrade")
def upgrade(
    revision: str = typer.Argument("head", help="Target revision (default: head = latest)"),
) -> None:
    """Apply database migrations.

    Examples:
        whatsnext db upgrade        # Apply all pending migrations
        whatsnext db upgrade head   # Same as above
        whatsnext db upgrade +1     # Apply next migration only
    """
    console.print(f"[bold]Upgrading database to revision: {revision}[/bold]\n")
    returncode = run_alembic(["upgrade", revision])
    if returncode == 0:
        console.print("\n[green]Database upgraded successfully.[/green]")
    else:
        raise typer.Exit(returncode)


@app.command(name="downgrade")
def downgrade(
    revision: str = typer.Argument("-1", help="Target revision (default: -1 = previous)"),
) -> None:
    """Rollback database migrations.

    Examples:
        whatsnext db downgrade      # Rollback one migration
        whatsnext db downgrade -1   # Same as above
        whatsnext db downgrade base # Rollback all migrations
    """
    console.print(f"[bold]Downgrading database to revision: {revision}[/bold]\n")
    returncode = run_alembic(["downgrade", revision])
    if returncode == 0:
        console.print("\n[yellow]Database downgraded successfully.[/yellow]")
    else:
        raise typer.Exit(returncode)


@app.command(name="status")
def status() -> None:
    """Show current database migration status.

    Shows which migrations have been applied and which are pending.
    """
    console.print("[bold]Database Migration Status[/bold]\n")
    run_alembic(["current", "--verbose"])


@app.command(name="history")
def history() -> None:
    """Show migration history.

    Lists all available migrations and their status.
    """
    console.print("[bold]Migration History[/bold]\n")
    run_alembic(["history", "--verbose"])


@app.command(name="stamp")
def stamp(
    revision: str = typer.Argument(..., help="Revision to stamp (e.g., 'head' or '0001')"),
) -> None:
    """Mark database as being at a specific revision without running migrations.

    This is useful for:
    - Existing databases that already have the schema
    - Recovering from failed migrations
    - Setting up a baseline

    Examples:
        whatsnext db stamp head   # Mark as fully migrated
        whatsnext db stamp 0001   # Mark as at initial migration
    """
    console.print(f"[bold]Stamping database at revision: {revision}[/bold]\n")
    returncode = run_alembic(["stamp", revision])
    if returncode == 0:
        console.print(f"\n[green]Database stamped at revision {revision}.[/green]")
    else:
        raise typer.Exit(returncode)


@app.command(name="init")
def init_db(
    stamp_existing: bool = typer.Option(
        False,
        "--stamp",
        help="Stamp existing database instead of creating tables",
    ),
) -> None:
    """Initialize the database.

    For new databases: Creates all tables by running migrations.
    For existing databases: Use --stamp to mark as migrated.

    Examples:
        whatsnext db init          # New database: run all migrations
        whatsnext db init --stamp  # Existing database: just stamp
    """
    if stamp_existing:
        console.print("[bold]Stamping existing database...[/bold]\n")
        returncode = run_alembic(["stamp", "head"])
        if returncode == 0:
            console.print("\n[green]Existing database marked as up-to-date.[/green]")
        else:
            raise typer.Exit(returncode)
    else:
        console.print("[bold]Initializing new database...[/bold]\n")
        returncode = run_alembic(["upgrade", "head"])
        if returncode == 0:
            console.print("\n[green]Database initialized successfully.[/green]")
        else:
            raise typer.Exit(returncode)
