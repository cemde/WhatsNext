"""Tests for CLI configuration loading."""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from whatsnext.cli.config import (
    Config,
    ServerConfig,
    find_config_file,
    get_config,
    load_config_file,
    parse_config,
)


class TestServerConfig:
    """Tests for ServerConfig dataclass."""

    def test_default_values(self):
        """Test default server config values."""
        config = ServerConfig()
        assert config.host == "localhost"
        assert config.port == 8000
        assert config.api_key is None

    def test_url_property(self):
        """Test URL generation."""
        config = ServerConfig(host="example.com", port=9000)
        assert config.url == "http://example.com:9000"


class TestConfig:
    """Tests for Config dataclass."""

    def test_default_values(self):
        """Test default config values."""
        config = Config()
        assert config.server.host == "localhost"
        assert config.server.port == 8000
        assert config.project is None
        assert config.client.entity is None
        assert config.formatter.type == "cli"
        assert config.config_path is None


class TestFindConfigFile:
    """Tests for finding config files."""

    def test_find_in_current_directory(self, tmp_path):
        """Test finding config in current directory."""
        config_file = tmp_path / ".whatsnext"
        config_file.write_text("project: test")

        with patch("whatsnext.cli.config.Path.cwd", return_value=tmp_path):
            result = find_config_file()
            assert result == config_file

    def test_find_in_git_root(self, tmp_path):
        """Test finding config in git root when not in cwd."""
        git_root = tmp_path / "repo"
        git_root.mkdir()
        config_file = git_root / ".whatsnext"
        config_file.write_text("project: test")

        with patch("whatsnext.cli.config.Path.cwd", return_value=tmp_path):
            with patch("whatsnext.cli.config.find_git_root", return_value=git_root):
                result = find_config_file()
                assert result == config_file

    def test_find_in_home(self, tmp_path):
        """Test finding config in home directory."""
        home_config = tmp_path / ".whatsnext"
        home_config.write_text("project: test")

        with patch("whatsnext.cli.config.Path.cwd", return_value=tmp_path / "other"):
            with patch("whatsnext.cli.config.find_git_root", return_value=None):
                with patch("whatsnext.cli.config.Path.home", return_value=tmp_path):
                    result = find_config_file()
                    assert result == home_config

    def test_no_config_found(self, tmp_path):
        """Test when no config file exists."""
        with patch("whatsnext.cli.config.Path.cwd", return_value=tmp_path):
            with patch("whatsnext.cli.config.find_git_root", return_value=None):
                with patch("whatsnext.cli.config.Path.home", return_value=tmp_path / "nonexistent"):
                    result = find_config_file()
                    assert result is None


class TestLoadConfigFile:
    """Tests for loading config files."""

    def test_load_yaml_config(self, tmp_path):
        """Test loading a YAML config file."""
        config_file = tmp_path / ".whatsnext"
        config_data = {"project": "myproject", "server": {"host": "example.com", "port": 9000}}
        config_file.write_text(yaml.dump(config_data))

        result = load_config_file(config_file)
        assert result["project"] == "myproject"
        assert result["server"]["host"] == "example.com"
        assert result["server"]["port"] == 9000

    def test_load_empty_config(self, tmp_path):
        """Test loading an empty config file."""
        config_file = tmp_path / ".whatsnext"
        config_file.write_text("")

        result = load_config_file(config_file)
        assert result == {}


class TestParseConfig:
    """Tests for parsing config dictionaries."""

    def test_parse_complete_config(self):
        """Test parsing a complete config dictionary."""
        data = {
            "project": "myproject",
            "server": {"host": "example.com", "port": 9000, "api_key": "secret"},
            "client": {"entity": "team1", "name": "worker1", "cpus": 4, "accelerators": 2},
            "formatter": {"type": "slurm", "slurm": {"partition": "gpu", "time": "2:00:00"}},
        }

        config = parse_config(data, Path("/tmp/.whatsnext"))

        assert config.project == "myproject"
        assert config.server.host == "example.com"
        assert config.server.port == 9000
        assert config.server.api_key == "secret"
        assert config.client.entity == "team1"
        assert config.client.name == "worker1"
        assert config.client.cpus == 4
        assert config.client.accelerators == 2
        assert config.formatter.type == "slurm"
        assert config.formatter.slurm["partition"] == "gpu"
        assert config.config_path == Path("/tmp/.whatsnext")

    def test_parse_minimal_config(self):
        """Test parsing a minimal config dictionary."""
        data = {"project": "test"}

        config = parse_config(data)

        assert config.project == "test"
        assert config.server.host == "localhost"
        assert config.server.port == 8000
        assert config.formatter.type == "cli"

    def test_parse_empty_config(self):
        """Test parsing an empty config dictionary."""
        config = parse_config({})

        assert config.project is None
        assert config.server.host == "localhost"


class TestGetConfig:
    """Tests for get_config function."""

    def test_explicit_config_file(self, tmp_path):
        """Test loading from an explicit config file."""
        config_file = tmp_path / "myconfig"
        config_file.write_text(yaml.dump({"project": "explicit"}))

        config = get_config(config_file)
        assert config.project == "explicit"
        assert config.config_path == config_file

    def test_explicit_config_file_not_found(self, tmp_path):
        """Test error when explicit config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            get_config(tmp_path / "nonexistent")

    def test_auto_discovery(self, tmp_path):
        """Test auto-discovery of config file."""
        config_file = tmp_path / ".whatsnext"
        config_file.write_text(yaml.dump({"project": "discovered"}))

        with patch("whatsnext.cli.config.find_config_file", return_value=config_file):
            config = get_config()
            assert config.project == "discovered"

    def test_default_config_when_no_file(self):
        """Test default config when no file is found."""
        with patch("whatsnext.cli.config.find_config_file", return_value=None):
            config = get_config()
            assert config.project is None
            assert config.server.host == "localhost"
            assert config.config_path is None
