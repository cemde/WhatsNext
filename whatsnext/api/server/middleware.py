"""Middleware for authentication, CORS, and rate limiting."""

import secrets
import time
from collections import defaultdict
from typing import Callable, Dict, List, Optional

from fastapi import HTTPException, Request, status
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .config import settings


def _constant_time_compare(provided_key: str, valid_keys: List[str]) -> bool:
    """Compare API key against valid keys using constant-time comparison.

    This prevents timing attacks that could leak information about valid keys.
    """
    # We must compare against all keys to ensure constant time
    # regardless of which key (if any) matches
    result = False
    for valid_key in valid_keys:
        if secrets.compare_digest(provided_key.encode(), valid_key.encode()):
            result = True
    return result


# API key header
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_api_key_dependency():
    """Create an API key dependency if authentication is enabled."""
    api_keys = settings.get_api_keys()

    if not api_keys:
        # Authentication disabled - return a no-op dependency
        async def no_auth():
            return None

        return no_auth

    async def verify_api_key(api_key: Optional[str] = API_KEY_HEADER):  # type: ignore[assignment]
        if api_key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required. Provide X-API-Key header.",
            )
        if not _constant_time_compare(api_key, api_keys):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API key.",
            )
        return api_key

    return verify_api_key


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using a sliding window approach."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 1 minute window
        # Store request timestamps per client IP
        self.request_times: Dict[str, List[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP from request, checking X-Forwarded-For for proxied requests."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    def _clean_old_requests(self, client_ip: str, current_time: float) -> None:
        """Remove request timestamps older than the window."""
        cutoff = current_time - self.window_size
        self.request_times[client_ip] = [t for t in self.request_times[client_ip] if t > cutoff]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting if disabled
        if self.requests_per_minute <= 0:
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        current_time = time.time()

        # Clean old requests
        self._clean_old_requests(client_ip, current_time)

        # Check rate limit
        if len(self.request_times[client_ip]) >= self.requests_per_minute:
            # Calculate retry after
            oldest_request = min(self.request_times[client_ip])
            retry_after = int(oldest_request + self.window_size - current_time) + 1

            return Response(
                content=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={"Retry-After": str(retry_after)},
            )

        # Record this request
        self.request_times[client_ip].append(current_time)

        return await call_next(request)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication.

    This provides authentication at the middleware level, which is useful
    for protecting all routes without adding dependencies to each one.
    """

    def __init__(self, app, api_keys: List[str], excluded_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.api_keys = api_keys
        self.excluded_paths = excluded_paths or ["/", "/checkdb", "/docs", "/openapi.json", "/redoc"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip authentication for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Skip if no API keys configured (auth disabled)
        if not self.api_keys:
            return await call_next(request)

        # Check for API key in header
        api_key = request.headers.get("X-API-Key")
        if api_key is None:
            return Response(
                content="API key required. Provide X-API-Key header.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        if not _constant_time_compare(api_key, self.api_keys):
            return Response(
                content="Invalid API key.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        return await call_next(request)
