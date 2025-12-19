from __future__ import annotations

from typing import Awaitable
from typing import Callable

from fastapi import Request
from fastapi import status
from sqlalchemy.exc import IntegrityError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.app_logging import logger
from app.core.exceptions import CustomHTTPException
from app.core.exceptions import custom_http_exception_handler


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        try:
            response = await call_next(request)
            logger.info("API Request Completed")
            return response
        except IntegrityError:
            logger.exception("IntegrityError")
            custom_exc = CustomHTTPException(status.HTTP_400_BAD_REQUEST, "Integrity error")
            return await custom_http_exception_handler(request, custom_exc)
        except RuntimeError as exc:
            logger.exception("RuntimeError")
            custom_exc = CustomHTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))
            return await custom_http_exception_handler(request, custom_exc)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unhandled exception")
            return await custom_http_exception_handler(request, exc)
