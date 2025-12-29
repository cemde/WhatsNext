"""Job management commands."""

from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console

from ..config import get_config, get_server_from_config

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("show")
def show_job(
    job_id: int = typer.Argument(..., help="Job ID"),
    host: Optional[str] = typer.Option(None, "--server", "-s", help="Server host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show details for a specific job."""
    import json

    import requests

    config = get_config(config_file)
    server = get_server_from_config(config, host, port)

    try:
        response = requests.get(f"{server.url}/jobs/{job_id}")
        response.raise_for_status()
        job = response.json()
    except requests.RequestException as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    # Get dependencies
    try:
        deps_response = requests.get(f"{server.url}/jobs/{job_id}/dependencies")
        deps_response.raise_for_status()
        deps = deps_response.json()
    except requests.RequestException:
        deps = None

    if json_output:
        output = {"job": job, "dependencies": deps}
        console.print(json.dumps(output, indent=2, default=str))
        return

    status_styles = {
        "PENDING": "blue",
        "QUEUED": "cyan",
        "RUNNING": "yellow",
        "COMPLETED": "green",
        "FAILED": "red",
        "BLOCKED": "magenta",
    }
    status = job.get("status", "UNKNOWN")
    style = status_styles.get(status, "dim")

    console.print(f"\n[bold cyan]Job: {job['name']}[/bold cyan] (ID: {job['id']})")
    console.print("─" * 50)
    console.print(f"Task ID:     {job.get('task_id', '-')}")
    console.print(f"Project ID:  {job.get('project_id', '-')}")
    console.print(f"Status:      [{style}]{status}[/{style}]")
    console.print(f"Priority:    {job.get('priority', 0)}")
    console.print(f"Created:     {job.get('created_at', '-')}")
    console.print(f"Updated:     {job.get('updated_at', '-')}")

    params = job.get("parameters", {})
    if params:
        console.print("\n[bold]Parameters:[/bold]")
        for key, value in params.items():
            console.print(f"  {key}: {value}")

    if deps and deps.get("dependencies"):
        console.print("\n[bold]Dependencies:[/bold]")
        for dep in deps["dependencies"]:
            dep_status = dep.get("status", "UNKNOWN")
            dep_style = status_styles.get(dep_status, "dim")
            console.print(f"  └─ [{dep_style}]{dep_status}[/{dep_style}] {dep['job_name']} (ID: {dep['job_id']})")


@app.command("add")
def add_job(
    task: str = typer.Argument(..., help="Task name"),
    project: Optional[str] = typer.Option(None, "--project", "-P", help="Project name"),
    name: Optional[str] = typer.Option(None, "--name", help="Job name (defaults to task name)"),
    param: Optional[List[str]] = typer.Option(None, "--param", help="Parameter in key=value format (can be repeated)"),
    priority: int = typer.Option(0, "--priority", help="Job priority (higher = more urgent)"),
    depends: Optional[List[int]] = typer.Option(None, "--depends", "-d", help="Dependent job ID (can be repeated)"),
    host: Optional[str] = typer.Option(None, "--server", "-s", help="Server host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
):
    """Add a job to the queue."""
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

    # Get task ID
    try:
        task_response = requests.get(f"{server.url}/tasks/name/{task}", params={"project_id": project_id})
        task_response.raise_for_status()
        task_id = task_response.json()["id"]
    except requests.RequestException as e:
        console.print(f"[red]Error finding task '{task}': {e}[/red]")
        raise typer.Exit(1)

    # Parse parameters
    parameters = {}
    if param:
        for p in param:
            if "=" in p:
                key, value = p.split("=", 1)
                # Try to parse as number or bool
                try:
                    if "." in value:
                        parameters[key] = float(value)
                    else:
                        parameters[key] = int(value)
                except ValueError:
                    if value.lower() in ("true", "false"):
                        parameters[key] = value.lower() == "true"
                    else:
                        parameters[key] = value
            else:
                console.print(f"[yellow]Warning: Ignoring invalid parameter '{p}' (expected key=value)[/yellow]")

    # Build depends dict
    depends_dict = {}
    if depends:
        for i, dep_id in enumerate(depends):
            depends_dict[str(i)] = str(dep_id)

    # Create job
    job_name = name or task
    try:
        response = requests.post(
            f"{server.url}/jobs/",
            json={
                "name": job_name,
                "project_id": project_id,
                "task_id": task_id,
                "parameters": parameters,
                "priority": priority,
                "depends": depends_dict,
            },
        )
        response.raise_for_status()
        job = response.json()
    except requests.RequestException as e:
        console.print(f"[red]Error creating job: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Added job:[/green] {job['name']} (ID: {job['id']})")


@app.command("add-batch")
def add_batch(
    file: Path = typer.Argument(..., help="YAML or JSON file with job definitions"),
    project: Optional[str] = typer.Option(None, "--project", "-P", help="Project name"),
    host: Optional[str] = typer.Option(None, "--server", "-s", help="Server host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
):
    """Add multiple jobs from a YAML/JSON file.

    File format:
    ```yaml
    jobs:
      - name: train-v1
        task: train
        parameters:
          lr: 0.01
        priority: 5
      - name: train-v2
        task: train
        parameters:
          lr: 0.001
    ```
    """
    import json

    import requests
    import yaml

    if not file.exists():
        console.print(f"[red]File not found: {file}[/red]")
        raise typer.Exit(1)

    # Load file
    with open(file) as f:
        if file.suffix in (".yaml", ".yml"):
            data = yaml.safe_load(f)
        else:
            data = json.load(f)

    jobs_data = data.get("jobs", [])
    if not jobs_data:
        console.print("[yellow]No jobs found in file[/yellow]")
        return

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

    # Get task IDs
    task_ids = {}

    # Build batch items
    batch_items = []
    for job_data in jobs_data:
        task_name = job_data.get("task")
        if not task_name:
            console.print(f"[yellow]Skipping job without task: {job_data}[/yellow]")
            continue

        # Cache task ID lookup
        if task_name not in task_ids:
            try:
                task_response = requests.get(f"{server.url}/tasks/name/{task_name}", params={"project_id": project_id})
                task_response.raise_for_status()
                task_ids[task_name] = task_response.json()["id"]
            except requests.RequestException:
                console.print(f"[yellow]Task '{task_name}' not found, skipping[/yellow]")
                continue

        batch_items.append(
            {
                "name": job_data.get("name", task_name),
                "task_id": task_ids[task_name],
                "parameters": job_data.get("parameters", {}),
                "priority": job_data.get("priority", 0),
                "depends": job_data.get("depends", {}),
            }
        )

    if not batch_items:
        console.print("[yellow]No valid jobs to add[/yellow]")
        return

    # Submit batch
    try:
        response = requests.post(
            f"{server.url}/projects/{project_id}/jobs/batch",
            json={"jobs": batch_items},
        )
        response.raise_for_status()
        result = response.json()
    except requests.RequestException as e:
        console.print(f"[red]Error adding batch: {e}[/red]")
        raise typer.Exit(1)

    created = result.get("created", 0)
    job_ids = result.get("job_ids", [])
    console.print(f"[green]Added {created} job(s)[/green]")
    if job_ids:
        console.print(f"[dim]IDs: {min(job_ids)}-{max(job_ids)}[/dim]")


@app.command("delete")
def delete_job(
    job_id: int = typer.Argument(..., help="Job ID"),
    host: Optional[str] = typer.Option(None, "--server", "-s", help="Server host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a job."""
    import requests
    from rich.prompt import Confirm

    if not force:
        if not Confirm.ask(f"[yellow]Delete job {job_id}?[/yellow]"):
            raise typer.Abort()

    config = get_config(config_file)
    server = get_server_from_config(config, host, port)

    try:
        response = requests.delete(f"{server.url}/jobs/{job_id}")
        response.raise_for_status()
    except requests.RequestException as e:
        console.print(f"[red]Error deleting job: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Deleted job:[/green] {job_id}")


@app.command("retry")
def retry_job(
    job_id: int = typer.Argument(..., help="Job ID"),
    host: Optional[str] = typer.Option(None, "--server", "-s", help="Server host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
):
    """Retry a failed job by setting its status back to PENDING."""
    import requests

    config = get_config(config_file)
    server = get_server_from_config(config, host, port)

    # Get current job data
    try:
        response = requests.get(f"{server.url}/jobs/{job_id}")
        response.raise_for_status()
        job = response.json()
    except requests.RequestException as e:
        console.print(f"[red]Error finding job: {e}[/red]")
        raise typer.Exit(1)

    if job.get("status") not in ("FAILED", "BLOCKED"):
        console.print(f"[yellow]Job {job_id} is not in FAILED or BLOCKED state (current: {job.get('status')})[/yellow]")
        raise typer.Exit(1)

    # Update status to PENDING
    try:
        response = requests.put(
            f"{server.url}/jobs/{job_id}",
            json={
                "name": job["name"],
                "project_id": job["project_id"],
                "task_id": job["task_id"],
                "parameters": job.get("parameters", {}),
                "priority": job.get("priority", 0),
                "depends": job.get("depends", {}),
                "status": "PENDING",
            },
        )
        response.raise_for_status()
    except requests.RequestException as e:
        console.print(f"[red]Error retrying job: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Retried job:[/green] {job_id} (status: PENDING)")


@app.command("deps")
def show_dependencies(
    job_id: int = typer.Argument(..., help="Job ID"),
    host: Optional[str] = typer.Option(None, "--server", "-s", help="Server host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show dependencies for a job."""
    import json

    import requests

    config = get_config(config_file)
    server = get_server_from_config(config, host, port)

    try:
        response = requests.get(f"{server.url}/jobs/{job_id}/dependencies")
        response.raise_for_status()
        deps = response.json()
    except requests.RequestException as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    if json_output:
        console.print(json.dumps(deps, indent=2, default=str))
        return

    status_styles = {
        "PENDING": "blue",
        "QUEUED": "cyan",
        "RUNNING": "yellow",
        "COMPLETED": "green",
        "FAILED": "red",
        "BLOCKED": "magenta",
    }

    job_status = deps.get("status", "UNKNOWN")
    job_style = status_styles.get(job_status, "dim")

    console.print(f"\n[bold]Job {deps['job_id']}: {deps['job_name']}[/bold]")
    console.print(f"Status: [{job_style}]{job_status}[/{job_style}]")

    dependencies = deps.get("dependencies", [])
    if not dependencies:
        console.print("[dim]No dependencies[/dim]")
    else:
        console.print(f"\nDependencies ({len(dependencies)}):")
        for dep in dependencies:
            dep_status = dep.get("status", "UNKNOWN")
            dep_style = status_styles.get(dep_status, "dim")
            console.print(f"  └─ [{dep_style}]{dep_status:12}[/{dep_style}] {dep['job_name']} (ID: {dep['job_id']})")

    console.print(f"\nAll completed: {'[green]Yes[/green]' if deps.get('all_completed') else '[yellow]No[/yellow]'}")
    console.print(f"Has failed:    {'[red]Yes[/red]' if deps.get('has_failed') else '[green]No[/green]'}")
