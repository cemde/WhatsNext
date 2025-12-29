"""Queue viewing and management commands."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..config import get_config, get_server_from_config

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("ls")
def list_queue(
    project: Optional[str] = typer.Option(None, "--project", "-P", help="Project name"),
    status_filter: Optional[str] = typer.Option(
        None, "--status", help="Filter by status (PENDING, RUNNING, COMPLETED, FAILED, BLOCKED, or 'all')"
    ),
    task: Optional[str] = typer.Option(None, "--task", "-t", help="Filter by task name"),
    host: Optional[str] = typer.Option(None, "--server", "-s", help="Server host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
    limit: int = typer.Option(50, "--limit", "-n", help="Maximum number of jobs to show"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List jobs in the queue."""
    import json

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

    # Get jobs
    try:
        response = requests.get(f"{server.url}/jobs/", params={"project_id": project_id, "limit": limit})
        response.raise_for_status()
        jobs = response.json()
    except requests.RequestException as e:
        console.print(f"[red]Error fetching jobs: {e}[/red]")
        raise typer.Exit(1)

    # Apply filters
    if status_filter and status_filter.lower() != "all":
        jobs = [j for j in jobs if j.get("status", "").upper() == status_filter.upper()]

    if task:
        # Get task ID for filtering
        try:
            task_response = requests.get(f"{server.url}/tasks/name/{task}", params={"project_id": project_id})
            if task_response.status_code == 200:
                task_id = task_response.json()["id"]
                jobs = [j for j in jobs if j.get("task_id") == task_id]
        except requests.RequestException:
            pass

    if json_output:
        console.print(json.dumps(jobs, indent=2, default=str))
        return

    if not jobs:
        console.print(f"[dim]No jobs found in queue for '{project_name}'[/dim]")
        return

    table = Table(title=f"Queue: {project_name}")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Task ID")
    table.add_column("Status")
    table.add_column("Priority", justify="right")
    table.add_column("Created", style="dim")

    status_styles = {
        "PENDING": "blue",
        "QUEUED": "cyan",
        "RUNNING": "yellow",
        "COMPLETED": "green",
        "FAILED": "red",
        "BLOCKED": "magenta",
    }

    for job in jobs:
        status = job.get("status", "UNKNOWN")
        style = status_styles.get(status, "dim")
        table.add_row(
            str(job["id"]),
            job["name"][:30],
            str(job.get("task_id", "-")),
            f"[{style}]{status}[/{style}]",
            str(job.get("priority", 0)),
            job["created_at"][:16] if job.get("created_at") else "-",
        )

    console.print(table)
    console.print(f"[dim]Showing {len(jobs)} job(s)[/dim]")


@app.command("stats")
def queue_stats(
    project: Optional[str] = typer.Option(None, "--project", "-P", help="Project name"),
    host: Optional[str] = typer.Option(None, "--server", "-s", help="Server host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show queue statistics."""
    import json

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

    # Get all jobs for stats
    try:
        response = requests.get(f"{server.url}/jobs/", params={"project_id": project_id, "limit": 10000})
        response.raise_for_status()
        jobs = response.json()
    except requests.RequestException as e:
        console.print(f"[red]Error fetching jobs: {e}[/red]")
        raise typer.Exit(1)

    # Calculate stats
    total = len(jobs)
    by_status = {}
    by_task = {}

    for job in jobs:
        status = job.get("status", "UNKNOWN")
        by_status[status] = by_status.get(status, 0) + 1

        task_id = job.get("task_id", "unknown")
        by_task[task_id] = by_task.get(task_id, 0) + 1

    stats = {
        "total": total,
        "by_status": by_status,
        "by_task": by_task,
    }

    if json_output:
        console.print(json.dumps(stats, indent=2))
        return

    console.print(f"\n[bold]Queue Statistics: {project_name}[/bold]")
    console.print("─" * 40)
    console.print(f"Total Jobs: {total}")

    if by_status:
        console.print("\n[bold]By Status:[/bold]")
        status_styles = {
            "PENDING": "blue",
            "QUEUED": "cyan",
            "RUNNING": "yellow",
            "COMPLETED": "green",
            "FAILED": "red",
            "BLOCKED": "magenta",
        }
        for status in ["PENDING", "QUEUED", "RUNNING", "COMPLETED", "FAILED", "BLOCKED"]:
            count = by_status.get(status, 0)
            if count > 0:
                style = status_styles.get(status, "dim")
                pct = (count / total * 100) if total > 0 else 0
                bar_len = int(pct / 5)  # 20 char max bar
                bar = "█" * bar_len + "░" * (20 - bar_len)
                console.print(f"  [{style}]{status:12}[/{style}] {count:4}  {bar} {pct:5.1f}%")

    if by_task:
        console.print("\n[bold]By Task ID:[/bold]")
        for task_id, count in sorted(by_task.items(), key=lambda x: -x[1])[:10]:
            console.print(f"  Task {task_id}: {count}")


@app.command("clear")
def clear_queue(
    project: Optional[str] = typer.Option(None, "--project", "-P", help="Project name"),
    host: Optional[str] = typer.Option(None, "--server", "-s", help="Server host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Clear all pending jobs from the queue."""
    import requests
    from rich.prompt import Confirm

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

    if not force:
        if not Confirm.ask(f"[yellow]Clear all pending jobs from '{project_name}'?[/yellow]"):
            raise typer.Abort()

    try:
        response = requests.delete(f"{server.url}/projects/{project_id}/queue")
        response.raise_for_status()
        result = response.json()
    except requests.RequestException as e:
        console.print(f"[red]Error clearing queue: {e}[/red]")
        raise typer.Exit(1)

    deleted = result.get("deleted", 0)
    console.print(f"[green]Cleared {deleted} job(s) from queue[/green]")
