from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from fastapi import Request
from fastapi.responses import JSONResponse


class CustomHTTPException(HTTPException):
    def __init__(self, status_code: int, msg: str, data: Any = None) -> None:
        super().__init__(status_code=status_code)
        self.msg = msg
        self.data = data


async def custom_http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, CustomHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.status_code, "msg": exc.msg, "data": exc.data},
        )

    return JSONResponse(status_code=500, content={"code": 500, "msg": "Internal Server Error", "data": None})
