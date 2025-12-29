"""Worker command to process jobs."""

import socket
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from ..config import get_config, get_project_from_config, get_server_from_config

console = Console()


def start_worker(
    project: Optional[str] = typer.Option(None, "--project", "-P", help="Project name"),
    name: Optional[str] = typer.Option(None, "--name", help="Worker name (default: hostname)"),
    entity: Optional[str] = typer.Option(None, "--entity", "-e", help="Entity/team name"),
    cpus: Optional[int] = typer.Option(None, "--cpus", help="Available CPUs"),
    accelerators: Optional[int] = typer.Option(None, "--accelerators", "--accel", help="Available accelerators"),
    formatter_type: Optional[str] = typer.Option(None, "--formatter", "-f", help="Formatter type: cli, slurm, runai"),
    poll_interval: int = typer.Option(30, "--poll-interval", help="Seconds between polling when queue is empty"),
    once: bool = typer.Option(False, "--once", help="Process one job and exit"),
    host: Optional[str] = typer.Option(None, "--server", "-s", help="Server host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
):
    """Start a worker to process jobs from the queue.

    The worker will continuously fetch and execute jobs until interrupted (Ctrl+C).
    """
    from whatsnext import Client, Formatter
    from whatsnext.api.client.formatter import CLIFormatter, RUNAIFormatter, SlurmFormatter

    config = get_config(config_file)

    # Resolve worker settings (CLI > config > defaults)
    worker_name = name or config.client.name or socket.gethostname()
    worker_entity = entity or config.client.entity or "default"
    worker_cpus = cpus if cpus is not None else (config.client.cpus or 0)
    worker_accelerators = accelerators if accelerators is not None else (config.client.accelerators or 0)

    # Get project
    project_name = project or config.project
    if not project_name:
        console.print("[red]No project specified. Use --project or set 'project' in .whatsnext[/red]")
        raise typer.Exit(1)

    try:
        proj = get_project_from_config(config, project_name, host, port)
    except Exception as e:
        console.print(f"[red]Error connecting to project: {e}[/red]")
        raise typer.Exit(1)

    # Create formatter
    fmt_type = formatter_type or config.formatter.type or "cli"

    if fmt_type == "cli":
        formatter: Formatter = CLIFormatter()
    elif fmt_type == "slurm":
        slurm_config = config.formatter.slurm or {}
        formatter = SlurmFormatter(
            partition=slurm_config.get("partition", "default"),
            time=slurm_config.get("time", "1:00:00"),
            nodes=slurm_config.get("nodes", 1),
            cpus_per_task=slurm_config.get("cpus_per_task", 1),
            mem=slurm_config.get("mem", "4G"),
            gpus=slurm_config.get("gpus"),
        )
    elif fmt_type == "runai":
        runai_config = config.formatter.runai or {}
        formatter = RUNAIFormatter(
            project=runai_config.get("project", "default"),
            image=runai_config.get("image", "python:3.11"),
            gpu=runai_config.get("gpu", 0),
            cpu=runai_config.get("cpu", 1),
            memory=runai_config.get("memory", "4Gi"),
            working_dir=runai_config.get("working_dir"),
            environment=runai_config.get("environment", {}),
        )
    else:
        console.print(f"[red]Unknown formatter type: {fmt_type}[/red]")
        raise typer.Exit(1)

    # Create client
    client = Client(
        entity=worker_entity,
        name=worker_name,
        description=f"CLI worker on {socket.gethostname()}",
        project=proj,
        formatter=formatter,
        available_cpu=worker_cpus,
        available_accelerators=worker_accelerators,
        register_with_server=True,
    )

    # Display startup info
    server = get_server_from_config(config, host, port)
    console.print(f"\n[bold cyan]Starting worker: {worker_name}[/bold cyan]")
    console.print(f"Entity:      {worker_entity}")
    console.print(f"Project:     {project_name}")
    console.print(f"Server:      {server.url}")
    console.print(f"Formatter:   {fmt_type}")
    console.print(f"Resources:   {worker_cpus} CPUs, {worker_accelerators} accelerators")
    if once:
        console.print("[dim]Mode: single job[/dim]")
    else:
        console.print(f"[dim]Mode: continuous (poll interval: {poll_interval}s)[/dim]")
    console.print()

    # Run worker
    try:
        if once:
            # Process single job
            resource = client.allocate_resource(cpu=1, accelerator=[])
            try:
                job = proj.fetch_job(
                    available_cpu=worker_cpus if worker_cpus > 0 else 0,
                    available_accelerators=worker_accelerators if worker_accelerators > 0 else 0,
                )
                if job:
                    console.print(f"[yellow]Processing:[/yellow] {job.name} (ID: {job.id})")
                    exit_code = job.run(resource)
                    if exit_code == 0:
                        console.print(f"[green]Completed:[/green] {job.name}")
                    else:
                        console.print(f"[red]Failed:[/red] {job.name} (exit code: {exit_code})")
                else:
                    console.print("[dim]No jobs available[/dim]")
            finally:
                client.free_resource(resource)
        else:
            # Continuous processing
            use_filter = worker_cpus > 0 or worker_accelerators > 0
            jobs_processed = client.work(
                poll_interval=poll_interval,
                run_forever=True,
                use_resource_filter=use_filter,
            )
            console.print(f"\n[bold]Processed {jobs_processed} job(s)[/bold]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]")
    except Exception as e:
        console.print(f"[red]Worker error: {e}[/red]")
        raise typer.Exit(1)
