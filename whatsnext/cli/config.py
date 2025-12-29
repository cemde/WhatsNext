"""Configuration file loading for WhatsNext CLI."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

import yaml

if TYPE_CHECKING:
    from whatsnext import Project


@dataclass
class ServerConfig:
    """Server connection configuration."""

    host: str = "localhost"
    port: int = 8000
    api_key: Optional[str] = None

    @property
    def url(self) -> str:
        """Get the full server URL."""
        return f"http://{self.host}:{self.port}"


@dataclass
class ClientConfig:
    """Worker client configuration."""

    entity: Optional[str] = None
    name: Optional[str] = None
    cpus: Optional[int] = None
    accelerators: Optional[int] = None


@dataclass
class FormatterConfig:
    """Formatter configuration."""

    type: str = "cli"
    slurm: Dict[str, Any] = field(default_factory=dict)
    runai: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Config:
    """Complete CLI configuration."""

    server: ServerConfig = field(default_factory=ServerConfig)
    project: Optional[str] = None
    client: ClientConfig = field(default_factory=ClientConfig)
    formatter: FormatterConfig = field(default_factory=FormatterConfig)

    # Track where config was loaded from
    config_path: Optional[Path] = None


def find_git_root() -> Optional[Path]:
    """Find the git repository root directory."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def find_config_file() -> Optional[Path]:
    """Find the .whatsnext config file using cascading resolution.

    Resolution order:
    1. .whatsnext in current directory
    2. .whatsnext in git repository root
    3. ~/.whatsnext in user home
    """
    # 1. Current directory
    cwd_config = Path.cwd() / ".whatsnext"
    if cwd_config.exists():
        return cwd_config

    # 2. Git repository root
    git_root = find_git_root()
    if git_root:
        git_config = git_root / ".whatsnext"
        if git_config.exists():
            return git_config

    # 3. User home directory
    home_config = Path.home() / ".whatsnext"
    if home_config.exists():
        return home_config

    return None


def load_config_file(path: Path) -> Dict[str, Any]:
    """Load configuration from a YAML file."""
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    return data


def parse_config(data: Dict[str, Any], config_path: Optional[Path] = None) -> Config:
    """Parse configuration dictionary into Config object."""
    server_data = data.get("server", {})
    server = ServerConfig(
        host=server_data.get("host", "localhost"),
        port=server_data.get("port", 8000),
        api_key=server_data.get("api_key"),
    )

    client_data = data.get("client", {})
    client = ClientConfig(
        entity=client_data.get("entity"),
        name=client_data.get("name"),
        cpus=client_data.get("cpus"),
        accelerators=client_data.get("accelerators"),
    )

    formatter_data = data.get("formatter", {})
    formatter = FormatterConfig(
        type=formatter_data.get("type", "cli"),
        slurm=formatter_data.get("slurm", {}),
        runai=formatter_data.get("runai", {}),
    )

    return Config(
        server=server,
        project=data.get("project"),
        client=client,
        formatter=formatter,
        config_path=config_path,
    )


def get_config(config_file: Optional[Path] = None) -> Config:
    """Get configuration, optionally from a specific file.

    Args:
        config_file: Optional explicit config file path. If None, uses cascading resolution.

    Returns:
        Config object with loaded settings.
    """
    if config_file:
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
        data = load_config_file(config_file)
        return parse_config(data, config_file)

    # Try to find config file
    found_config = find_config_file()
    if found_config:
        data = load_config_file(found_config)
        return parse_config(data, found_config)

    # Return default config if no file found
    return Config()


def get_server_from_config(
    config: Config,
    host: Optional[str] = None,
    port: Optional[int] = None,
) -> ServerConfig:
    """Get server configuration with optional overrides.

    Args:
        config: Configuration object.
        host: Optional host override.
        port: Optional port override.

    Returns:
        ServerConfig with the resolved settings.
    """
    final_host = host or config.server.host
    final_port = port or config.server.port

    return ServerConfig(host=final_host, port=final_port, api_key=config.server.api_key)


def get_project_from_config(
    config: Config,
    project_name: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
) -> "Project":
    """Get a Project instance from config, with optional overrides.

    Args:
        config: Configuration object.
        project_name: Optional project name override.
        host: Optional host override.
        port: Optional port override.

    Returns:
        Project instance.

    Raises:
        typer.BadParameter: If no project specified.
    """
    import typer

    from whatsnext import Server

    final_project = project_name or config.project
    if not final_project:
        raise typer.BadParameter("No project specified. Use --project or set 'project' in .whatsnext")

    server_config = get_server_from_config(config, host, port)
    server = Server(server_config.host, server_config.port)
    project = server.get_project(final_project)
    if project is None:
        raise typer.BadParameter(f"Project '{final_project}' not found on server")
    return project
