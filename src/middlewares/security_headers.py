from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from src.core.settings.env import Environment
from src.core.settings.settings import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response: Response = await call_next(request)

        # Always set basic hardening headers
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Permissions-Policy",
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()",  # noqa: E501
        )
        response.headers.setdefault("X-XSS-Protection", "0")

        # Set HSTS only on HTTPS and non-local envs
        is_https = request.headers.get("x-forwarded-proto", request.url.scheme) == "https"
        if is_https and settings.env in (Environment.DEV, Environment.PROD):
            # 6 months, include subdomains, allow preload if you plan to submit
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=15552000; includeSubDomains; preload",
            )

        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "object-src 'none'; "
            "img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline' https:; "
            "script-src 'self' 'unsafe-inline' https:; "
            "connect-src 'self' https:; "
            "form-action 'self'"
        )
        response.headers.setdefault("Content-Security-Policy", csp)

        return response
