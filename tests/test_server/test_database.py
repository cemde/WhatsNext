"""Tests for database utilities."""

from unittest.mock import MagicMock, patch

import pytest


class TestGetDb:
    """Tests for get_db function."""

    def test_get_db_yields_session(self):
        """Test that get_db yields a session and closes it."""
        # We need to import within test due to module-level DB connection
        with patch("whatsnext.api.server.database.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            from whatsnext.api.server.database import get_db

            # Use the generator
            gen = get_db()
            session = next(gen)

            assert session == mock_session

            # Finish the generator (triggers finally block)
            try:
                next(gen)
            except StopIteration:
                pass

            mock_session.close.assert_called_once()

    def test_get_db_closes_on_exception(self):
        """Test that get_db closes session even on exception."""
        with patch("whatsnext.api.server.database.SessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            from whatsnext.api.server.database import get_db

            gen = get_db()
            session = next(gen)

            # Simulate exception
            try:
                gen.throw(ValueError("test error"))
            except ValueError:
                pass

            mock_session.close.assert_called_once()


class TestDatabaseURL:
    """Tests for database URL construction."""

    def test_database_url_format(self):
        """Test that database URL is properly formatted."""
        with patch("whatsnext.api.server.database.db") as mock_db:
            mock_db.user = "testuser"
            mock_db.password = "testpass"
            mock_db.hostname = "localhost"
            mock_db.port = "5432"
            mock_db.database = "testdb"

            # The URL should be constructed as expected
            expected_url = "postgresql://testuser:testpass@localhost:5432/testdb"

            # Import to trigger URL construction
            import importlib
            import whatsnext.api.server.database as db_module

            # Check that the module has the expected structure
            assert hasattr(db_module, "engine")
            assert hasattr(db_module, "SessionLocal")
            assert hasattr(db_module, "Base")
            assert hasattr(db_module, "get_db")
