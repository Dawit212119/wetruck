from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.core.app_logging import logger

def format_validation_errors(errors):
    field_errors = {}

    for err in errors:
        field = err["loc"][-1]
        field_errors[field] = err["msg"]

    return field_errors


def error_response(message: str, code: str, status_code: int) -> dict:
    return {
        "error": message,
        "code": code,
        "status_code": status_code,
    }


class CustomHTTPException(HTTPException):
    def __init__(
        self,
        status_code: int,
        message: str,
        code: str = "CUSTOM_ERROR",
    ):
        super().__init__(status_code=status_code)
        self.message = message
        self.code = code

async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        "HTTPException",
        extra={"path": request.url.path, "status_code": exc.status_code},
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            message=str(exc.detail),
            code="HTTP_EXCEPTION",
            status_code=exc.status_code,
        ),
    )



async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.info(
        "Validation error",
        extra={"path": request.url.path, "errors": exc.errors()},
    )

    base_response = error_response(
        message="Validation failed",
        code="VALIDATION_ERROR",
        status_code=422,
    )

    base_response["fields"] = format_validation_errors(exc.errors())

    return JSONResponse(
        status_code=422,
        content=base_response,
    )


async def custom_exception_handler(request: Request, exc: CustomHTTPException):
    logger.error(
        exc.message,
        extra={"path": request.url.path, "code": exc.code},
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            message=exc.message,
            code=exc.code,
            status_code=exc.status_code,
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.critical(
        "Unhandled exception",
        exc_info=True,
        extra={"path": request.url.path},
    )

    return JSONResponse(
        status_code=500,
        content=error_response(
            message="Internal Server Error",
            code="INTERNAL_ERROR",
            status_code=500,
        ),
    )
