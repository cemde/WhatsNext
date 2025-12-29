"""WhatsNext CLI - Command line interface for job queue management."""

from typing import Optional

import typer
from rich.console import Console

from .commands import auth, clients, db, init, jobs, projects, queue, status, tasks, worker

__version__ = "0.0.2"

# Create main app
app = typer.Typer(
    name="whatsnext",
    help="WhatsNext - Job queue and task management CLI",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Register sub-commands
app.add_typer(projects.app, name="projects", help="Manage projects")
app.add_typer(tasks.app, name="tasks", help="Manage tasks")
app.add_typer(jobs.app, name="jobs", help="Manage jobs")
app.add_typer(queue.app, name="queue", help="View and manage the job queue")
app.add_typer(clients.app, name="clients", help="View connected clients")
app.add_typer(db.app, name="db", help="Database migrations (server-side)")
app.command(name="init")(init.init_config)
app.command(name="worker")(worker.start_worker)
app.command(name="status")(status.show_status)
app.command(name="test-auth")(auth.test_auth)

# Global console for output
console = Console()


def version_callback(value: bool):
    """Show version and exit."""
    if value:
        console.print(f"whatsnext version {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """WhatsNext - Job queue and task management system.

    Use 'whatsnext COMMAND --help' for more information on a command.
    """
    pass


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
