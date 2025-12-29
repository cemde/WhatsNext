"""Tests for the init command."""

import os
import tempfile
from pathlib import Path

import yaml
from typer.testing import CliRunner

from whatsnext.cli import app

runner = CliRunner()


class TestInitCommand:
    """Tests for the init command functionality."""

    def test_init_creates_config_file(self):
        """Test that init creates a .whatsnext file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            # Provide all options to skip interactive prompts (empty string for project skips it)
            result = runner.invoke(
                app,
                ["init", "--server", "localhost", "--port", "8000"],
                input="\n",  # Empty project name
            )

            assert result.exit_code == 0
            config_file = Path(tmpdir) / ".whatsnext"
            assert config_file.exists()

    def test_init_with_options(self):
        """Test init with custom options."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            result = runner.invoke(
                app,
                ["init", "--server", "example.com", "--port", "9000", "--project", "myproject"],
            )

            assert result.exit_code == 0

            config_file = Path(tmpdir) / ".whatsnext"
            with open(config_file) as f:
                config = yaml.safe_load(f)

            assert config["server"]["host"] == "example.com"
            assert config["server"]["port"] == 9000
            assert config["project"] == "myproject"

    def test_init_refuses_overwrite_without_force(self):
        """Test that init refuses to overwrite existing config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            config_file = Path(tmpdir) / ".whatsnext"
            config_file.write_text("existing: config")

            # Say 'n' to the overwrite prompt
            result = runner.invoke(app, ["init", "--server", "localhost", "--port", "8000"], input="n\n")

            assert result.exit_code == 1
            # Original content preserved
            assert config_file.read_text() == "existing: config"

    def test_init_force_overwrites(self):
        """Test that init --force overwrites existing config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            config_file = Path(tmpdir) / ".whatsnext"
            config_file.write_text("existing: config")

            result = runner.invoke(
                app,
                ["init", "--force", "--server", "localhost", "--port", "8000", "--project", "newproject"],
            )

            assert result.exit_code == 0

            with open(config_file) as f:
                config = yaml.safe_load(f)

            assert config["project"] == "newproject"
            assert "existing" not in config

    def test_init_shows_created_message(self):
        """Test that init shows a success message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            result = runner.invoke(
                app,
                ["init", "--server", "localhost", "--port", "8000"],
                input="\n",  # Empty project name
            )

            assert result.exit_code == 0
            assert "Created" in result.stdout or ".whatsnext" in result.stdout
