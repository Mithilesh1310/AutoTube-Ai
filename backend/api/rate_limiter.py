import time
import logging
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

class LockoutResult(tuple):
    def __new__(cls, is_locked: bool, remaining_seconds: float):
        return super().__new__(cls, (is_locked, remaining_seconds))
    def __bool__(self):
        return bool(self[0])

class RateLimiter:
    """
    In-memory Sliding-Window Rate Limiter & Brute-Force Protection Service:
    - Tracks request frequencies per client IP and user token.
    - Locks out IPs with excessive failed authentication attempts for 15 minutes.
    """
    def __init__(self, requests_per_minute: int = 120, max_login_failures: int = 5):
        self.rpm = requests_per_minute
        self.max_login_failures = max_login_failures
        # ip -> list of timestamps
        self.request_history: Dict[str, list] = defaultdict(list)
        # ip -> (failure_count, lockout_expiry_timestamp)
        self.login_failures: Dict[str, Tuple[int, float]] = {}

    def is_rate_limited(self, client_ip: str) -> bool:
        now = time.time()
        window_start = now - 60.0

        # Purge older requests
        history = [ts for ts in self.request_history[client_ip] if ts > window_start]
        self.request_history[client_ip] = history

        if len(history) >= self.rpm:
            return True

        self.request_history[client_ip].append(now)
        return False

    async def check_rate_limit(self, client_ip: str, limit: int = None) -> bool:
        """Returns True if request is allowed, False if rate limit exceeded."""
        now = time.time()
        window_start = now - 60.0
        effective_limit = limit if limit is not None else self.rpm

        history = [ts for ts in self.request_history[client_ip] if ts > window_start]
        self.request_history[client_ip] = history

        if len(history) >= effective_limit:
            return False

        self.request_history[client_ip].append(now)
        return True

    async def is_login_locked(self, client_ip: str) -> LockoutResult:
        now = time.time()
        if client_ip in self.login_failures:
            count, expiry = self.login_failures[client_ip]
            if count >= self.max_login_failures:
                if now < expiry:
                    return LockoutResult(True, round(expiry - now, 2))
                else:
                    del self.login_failures[client_ip]
        return LockoutResult(False, 0.0)

    async def record_failed_login(self, client_ip: str) -> bool:
        """Records a failed login attempt. Returns True if client is now locked."""
        now = time.time()
        count, _ = self.login_failures.get(client_ip, (0, 0.0))
        new_count = count + 1
        expiry = now + 900.0 if new_count >= self.max_login_failures else 0.0 # 15 min lockout
        self.login_failures[client_ip] = (new_count, expiry)
        logger.warning(f"[RateLimiter] Login failure from IP '{client_ip}' ({new_count}/{self.max_login_failures})")
        return new_count >= self.max_login_failures

    record_login_failure = record_failed_login

    def record_login_success(self, client_ip: str):
        self.login_failures.pop(client_ip, None)

rate_limiter = RateLimiter()

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"

        # Check login brute force lockout
        if request.url.path.endswith("/auth/login") and request.method == "POST":
            locked_res = await rate_limiter.is_login_locked(client_ip)
            if locked_res[0]:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": f"Too many failed login attempts. IP temporarily locked for {int(locked_res[1])} seconds."}
                )

        # Check standard sliding-window rate limit
        if rate_limiter.is_rate_limited(client_ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "API rate limit exceeded (120 requests/minute). Please slow down."}
            )

        response = await call_next(request)
        return response
