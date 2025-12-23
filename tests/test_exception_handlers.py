import pytest
import json
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.datastructures import URL
from src.core.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    custom_exception_handler,
    unhandled_exception_handler,
    CustomHTTPException,
)


class DummyRequest:
    """Simulate FastAPI Request object minimally"""
    def __init__(self, path="/test"):
        self.url = URL(path)


@pytest.mark.asyncio
async def test_http_exception_handler(mocker):
    mock_logger = mocker.patch("src.core.app_logging.logger.warning")

    request = DummyRequest()
    exc = HTTPException(status_code=403, detail="Forbidden")

    response = await http_exception_handler(request, exc)
    data = json.loads(response.body.decode())

    # Assert JSON contains correct structure
    assert data["error"] == "Forbidden"
    assert data["code"] == "HTTP_EXCEPTION"
    assert data["status_code"] == 403

    # Assert logger called
    mock_logger.assert_called_once()


@pytest.mark.asyncio
async def test_validation_exception_handler(mocker):
    mock_logger = mocker.patch("src.core.app_logging.logger.info")

    request = DummyRequest()
    exc = RequestValidationError([
        {"loc": ["query", "number"], "msg": "field required", "type": "value_error"}
    ])

    response = await validation_exception_handler(request, exc)
    data = json.loads(response.body.decode())

    assert data["error"] == "Validation failed"
    assert data["code"] == "VALIDATION_ERROR"
    assert data["status_code"] == 422
    mock_logger.assert_called_once()


@pytest.mark.asyncio
async def test_custom_exception_handler(mocker):
    mock_logger = mocker.patch("src.core.app_logging.logger.error")

    request = DummyRequest()
    exc = CustomHTTPException(status_code=409, message="Conflict occurred", code="TEST_CONFLICT")

    response = await custom_exception_handler(request, exc)
    data = json.loads(response.body.decode())

    assert data["error"] == "Conflict occurred"
    assert data["code"] == "TEST_CONFLICT"
    assert data["status_code"] == 409
    mock_logger.assert_called_once()


@pytest.mark.asyncio
async def test_unhandled_exception_handler(mocker):
    mock_logger = mocker.patch("src.core.app_logging.logger.critical")

    request = DummyRequest()
    exc = Exception("Something bad")

    response = await unhandled_exception_handler(request, exc)
    data = json.loads(response.body.decode())

    assert data["error"] == "Internal Server Error"
    assert data["code"] == "INTERNAL_ERROR"
    assert data["status_code"] == 500
    mock_logger.assert_called_once()
