"""Tests for server middleware."""

import asyncio
import time
from unittest.mock import MagicMock, patch

import pytest

from whatsnext.api.server.middleware import (
    AuthenticationMiddleware,
    RateLimitMiddleware,
    get_api_key_dependency,
)


class TestGetApiKeyDependency:
    """Tests for get_api_key_dependency function."""

    @patch("whatsnext.api.server.middleware.settings")
    def test_no_api_keys_returns_no_auth(self, mock_settings):
        """Test that no auth is required when no API keys configured."""
        mock_settings.get_api_keys.return_value = []

        dependency = get_api_key_dependency()

        # The returned function should be a no-op
        assert dependency is not None
        assert callable(dependency)

    @patch("whatsnext.api.server.middleware.settings")
    def test_with_api_keys_returns_verifier(self, mock_settings):
        """Test that verifier is returned when API keys configured."""
        mock_settings.get_api_keys.return_value = ["key1", "key2"]

        dependency = get_api_key_dependency()

        assert dependency is not None
        assert callable(dependency)

    @patch("whatsnext.api.server.middleware.settings")
    def test_no_auth_returns_none(self, mock_settings):
        """Test no-auth dependency returns None."""
        mock_settings.get_api_keys.return_value = []

        dependency = get_api_key_dependency()
        result = asyncio.run(dependency())

        assert result is None

    @patch("whatsnext.api.server.middleware.settings")
    def test_valid_api_key(self, mock_settings):
        """Test valid API key passes."""
        mock_settings.get_api_keys.return_value = ["valid-key"]

        dependency = get_api_key_dependency()
        result = asyncio.run(dependency(api_key="valid-key"))

        assert result == "valid-key"

    @patch("whatsnext.api.server.middleware.settings")
    def test_missing_api_key(self, mock_settings):
        """Test missing API key raises 401."""
        from fastapi import HTTPException

        mock_settings.get_api_keys.return_value = ["valid-key"]

        dependency = get_api_key_dependency()

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(dependency(api_key=None))

        assert exc_info.value.status_code == 401

    @patch("whatsnext.api.server.middleware.settings")
    def test_invalid_api_key(self, mock_settings):
        """Test invalid API key raises 403."""
        from fastapi import HTTPException

        mock_settings.get_api_keys.return_value = ["valid-key"]

        dependency = get_api_key_dependency()

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(dependency(api_key="invalid-key"))

        assert exc_info.value.status_code == 403


class TestRateLimitMiddleware:
    """Tests for RateLimitMiddleware."""

    def test_init(self):
        """Test middleware initialization."""
        mock_app = MagicMock()

        middleware = RateLimitMiddleware(mock_app, requests_per_minute=100)

        assert middleware.requests_per_minute == 100
        assert middleware.window_size == 60

    def test_get_client_ip_from_client(self):
        """Test getting client IP from request.client."""
        mock_app = MagicMock()
        middleware = RateLimitMiddleware(mock_app)

        mock_request = MagicMock()
        mock_request.headers.get.return_value = None
        mock_request.client.host = "192.168.1.1"

        ip = middleware._get_client_ip(mock_request)

        assert ip == "192.168.1.1"

    def test_get_client_ip_from_forwarded(self):
        """Test getting client IP from X-Forwarded-For."""
        mock_app = MagicMock()
        middleware = RateLimitMiddleware(mock_app)

        mock_request = MagicMock()
        mock_request.headers.get.return_value = "10.0.0.1, 192.168.1.1"

        ip = middleware._get_client_ip(mock_request)

        assert ip == "10.0.0.1"

    def test_get_client_ip_unknown(self):
        """Test getting client IP when no info available."""
        mock_app = MagicMock()
        middleware = RateLimitMiddleware(mock_app)

        mock_request = MagicMock()
        mock_request.headers.get.return_value = None
        mock_request.client = None

        ip = middleware._get_client_ip(mock_request)

        assert ip == "unknown"

    def test_clean_old_requests(self):
        """Test cleaning old request timestamps."""
        mock_app = MagicMock()
        middleware = RateLimitMiddleware(mock_app)

        current_time = time.time()
        middleware.request_times["127.0.0.1"] = [
            current_time - 100,  # old, should be removed
            current_time - 30,  # recent, should stay
            current_time - 10,  # recent, should stay
        ]

        middleware._clean_old_requests("127.0.0.1", current_time)

        assert len(middleware.request_times["127.0.0.1"]) == 2

    def test_dispatch_rate_limit_disabled(self):
        """Test dispatch when rate limiting is disabled."""
        mock_app = MagicMock()
        middleware = RateLimitMiddleware(mock_app, requests_per_minute=0)

        mock_request = MagicMock()

        async def mock_call_next(req):
            return "response"

        result = asyncio.run(middleware.dispatch(mock_request, mock_call_next))

        assert result == "response"

    def test_dispatch_under_limit(self):
        """Test dispatch when under rate limit."""
        mock_app = MagicMock()
        middleware = RateLimitMiddleware(mock_app, requests_per_minute=100)

        mock_request = MagicMock()
        mock_request.headers.get.return_value = None
        mock_request.client.host = "127.0.0.1"

        async def mock_call_next(req):
            return "response"

        result = asyncio.run(middleware.dispatch(mock_request, mock_call_next))

        assert result == "response"

    def test_dispatch_over_limit(self):
        """Test dispatch when over rate limit."""
        mock_app = MagicMock()
        middleware = RateLimitMiddleware(mock_app, requests_per_minute=2)

        mock_request = MagicMock()
        mock_request.headers.get.return_value = None
        mock_request.client.host = "127.0.0.1"

        # Pre-fill request times to exceed limit
        current_time = time.time()
        middleware.request_times["127.0.0.1"] = [current_time, current_time]

        async def mock_call_next(req):
            return "response"

        result = asyncio.run(middleware.dispatch(mock_request, mock_call_next))

        assert result.status_code == 429


class TestAuthenticationMiddleware:
    """Tests for AuthenticationMiddleware."""

    def test_init(self):
        """Test middleware initialization."""
        mock_app = MagicMock()

        middleware = AuthenticationMiddleware(mock_app, api_keys=["key1"])

        assert middleware.api_keys == ["key1"]
        assert "/" in middleware.excluded_paths
        assert "/docs" in middleware.excluded_paths

    def test_init_custom_excluded_paths(self):
        """Test middleware with custom excluded paths."""
        mock_app = MagicMock()

        middleware = AuthenticationMiddleware(mock_app, api_keys=["key1"], excluded_paths=["/custom"])

        assert middleware.excluded_paths == ["/custom"]

    def test_dispatch_excluded_path(self):
        """Test dispatch skips excluded paths."""
        mock_app = MagicMock()
        middleware = AuthenticationMiddleware(mock_app, api_keys=["key1"])

        mock_request = MagicMock()
        mock_request.url.path = "/"

        async def mock_call_next(req):
            return "response"

        result = asyncio.run(middleware.dispatch(mock_request, mock_call_next))

        assert result == "response"

    def test_dispatch_no_api_keys(self):
        """Test dispatch when no API keys configured."""
        mock_app = MagicMock()
        middleware = AuthenticationMiddleware(mock_app, api_keys=[])

        mock_request = MagicMock()
        mock_request.url.path = "/protected"

        async def mock_call_next(req):
            return "response"

        result = asyncio.run(middleware.dispatch(mock_request, mock_call_next))

        assert result == "response"

    def test_dispatch_missing_key(self):
        """Test dispatch when API key is missing."""
        mock_app = MagicMock()
        middleware = AuthenticationMiddleware(mock_app, api_keys=["valid-key"])

        mock_request = MagicMock()
        mock_request.url.path = "/protected"
        mock_request.headers.get.return_value = None

        async def mock_call_next(req):
            return "response"

        result = asyncio.run(middleware.dispatch(mock_request, mock_call_next))

        assert result.status_code == 401

    def test_dispatch_invalid_key(self):
        """Test dispatch when API key is invalid."""
        mock_app = MagicMock()
        middleware = AuthenticationMiddleware(mock_app, api_keys=["valid-key"])

        mock_request = MagicMock()
        mock_request.url.path = "/protected"
        mock_request.headers.get.return_value = "wrong-key"

        async def mock_call_next(req):
            return "response"

        result = asyncio.run(middleware.dispatch(mock_request, mock_call_next))

        assert result.status_code == 403

    def test_dispatch_valid_key(self):
        """Test dispatch when API key is valid."""
        mock_app = MagicMock()
        middleware = AuthenticationMiddleware(mock_app, api_keys=["valid-key"])

        mock_request = MagicMock()
        mock_request.url.path = "/protected"
        mock_request.headers.get.return_value = "valid-key"

        async def mock_call_next(req):
            return "response"

        result = asyncio.run(middleware.dispatch(mock_request, mock_call_next))

        assert result == "response"
