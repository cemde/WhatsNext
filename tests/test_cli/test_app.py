"""Tests for CLI main application."""

from typer.testing import CliRunner

from whatsnext.cli import __version__, app

runner = CliRunner()


class TestMainApp:
    """Tests for the main CLI application."""

    def test_help(self):
        """Test help output."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "WhatsNext" in result.stdout
        assert "projects" in result.stdout
        assert "tasks" in result.stdout
        assert "jobs" in result.stdout
        assert "queue" in result.stdout
        assert "clients" in result.stdout
        assert "worker" in result.stdout
        assert "status" in result.stdout
        assert "init" in result.stdout

    def test_version(self):
        """Test version output."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.stdout

    def test_no_args_shows_help(self):
        """Test that no arguments shows help."""
        result = runner.invoke(app)
        # no_args_is_help=True causes exit code 2 (usage error) with help output
        assert result.exit_code == 2
        assert "Usage:" in result.stdout


class TestProjectsSubcommand:
    """Tests for the projects subcommand."""

    def test_projects_help(self):
        """Test projects help output."""
        result = runner.invoke(app, ["projects", "--help"])
        assert result.exit_code == 0
        assert "ls" in result.stdout
        assert "show" in result.stdout
        assert "create" in result.stdout
        assert "delete" in result.stdout
        assert "archive" in result.stdout


class TestTasksSubcommand:
    """Tests for the tasks subcommand."""

    def test_tasks_help(self):
        """Test tasks help output."""
        result = runner.invoke(app, ["tasks", "--help"])
        assert result.exit_code == 0
        assert "ls" in result.stdout
        assert "show" in result.stdout
        assert "create" in result.stdout
        assert "delete" in result.stdout


class TestJobsSubcommand:
    """Tests for the jobs subcommand."""

    def test_jobs_help(self):
        """Test jobs help output."""
        result = runner.invoke(app, ["jobs", "--help"])
        assert result.exit_code == 0
        assert "show" in result.stdout
        assert "add" in result.stdout
        assert "add-batch" in result.stdout
        assert "delete" in result.stdout
        assert "retry" in result.stdout
        assert "deps" in result.stdout


class TestQueueSubcommand:
    """Tests for the queue subcommand."""

    def test_queue_help(self):
        """Test queue help output."""
        result = runner.invoke(app, ["queue", "--help"])
        assert result.exit_code == 0
        assert "ls" in result.stdout
        assert "stats" in result.stdout
        assert "clear" in result.stdout


class TestClientsSubcommand:
    """Tests for the clients subcommand."""

    def test_clients_help(self):
        """Test clients help output."""
        result = runner.invoke(app, ["clients", "--help"])
        assert result.exit_code == 0
        assert "ls" in result.stdout
        assert "show" in result.stdout
        assert "deactivate" in result.stdout
        assert "delete" in result.stdout


class TestInitCommand:
    """Tests for the init command."""

    def test_init_help(self):
        """Test init help output."""
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "--server" in result.stdout
        assert "--port" in result.stdout
        assert "--project" in result.stdout
        assert "--force" in result.stdout


class TestWorkerCommand:
    """Tests for the worker command."""

    def test_worker_help(self):
        """Test worker help output."""
        result = runner.invoke(app, ["worker", "--help"])
        assert result.exit_code == 0
        assert "--project" in result.stdout
        assert "--name" in result.stdout
        assert "--cpus" in result.stdout
        assert "--formatter" in result.stdout
        assert "--poll-interval" in result.stdout
        assert "--once" in result.stdout


class TestStatusCommand:
    """Tests for the status command."""

    def test_status_help(self):
        """Test status help output."""
        result = runner.invoke(app, ["status", "--help"])
        assert result.exit_code == 0
        assert "--project" in result.stdout
        assert "--server" in result.stdout
        assert "--json" in result.stdout
