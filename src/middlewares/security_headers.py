from __future__ import annotations

from typing import Awaitable
from typing import Callable

from fastapi import Request
from fastapi import Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.settings.settings import settings
from src.core.settings.env import Environment


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
            # Restrictive by default; loosen per feature if needed
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()",  # noqa: E501
        )
        # X-XSS-Protection is obsolete but sometimes required by scanners
        response.headers.setdefault("X-XSS-Protection", "0")

        # # Only set HSTS when served over HTTPS to avoid locking out local dev
        is_https = request.headers.get("x-forwarded-proto", request.url.scheme) == "https"
        if is_https and settings.env in (Environment.DEV, Environment.PROD):
            # 6 months, include subdomains, allow preload if you plan to submit
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=15552000; includeSubDomains; preload",
            )

        # Content Security Policy: conservative default; adjust as your frontends require
        # Allow Swagger UI CDN resources for /docs endpoint
        is_docs_endpoint = str(request.url.path).startswith("/docs") or str(request.url.path).startswith("/redoc") or str(request.url.path).startswith("/openapi.json")
        
        if is_docs_endpoint:
            # Very permissive CSP for docs endpoints - allow all resources over https and self
            # This avoids CSP blocking, but proxy issues still need to be handled separately.
            csp = (
                "default-src 'self' https:; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; "
                "style-src 'self' 'unsafe-inline' https:; "
                "img-src 'self' data: https:; "
                "font-src 'self' data: https:; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none'; "
                "form-action 'self'"
            )
        else:
            # Conservative CSP for other endpoints
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
        # Don't override if upstream already set a custom CSP
        response.headers.setdefault("Content-Security-Policy", csp)

        return response
