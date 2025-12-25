from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from src.core.exception.database_exceptions import DatabaseException
from src.middlewares.request_logging import RequestLoggingMiddleware
from src.middlewares.security_headers import SecurityHeadersMiddleware
from src.api.router import api_router
from src.core.exceptions import (
    CustomHTTPException,
    database_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    custom_exception_handler,
    unhandled_exception_handler,
)
from src.core.settings.env import Environment
from src.core.settings.settings import settings
from src.middlewares.request_logging import RequestLoggingMiddleware
from src.middlewares.security_headers import SecurityHeadersMiddleware


SWAGGER_DIR = Path(__file__).resolve().parent / "static" / "swagger"
use_local_swagger = SWAGGER_DIR.exists()

# If local swagger assets are present, serve them to avoid proxy/CSP issues.
swagger_kwargs = {}
if use_local_swagger:
    swagger_kwargs = {
        "swagger_ui_bundle_js_url": "/static/swagger/swagger-ui-bundle.js",
        "swagger_ui_standalone_preset_js_url": "/static/swagger/swagger-ui-standalone-preset.js",
        "swagger_ui_css_url": "/static/swagger/swagger-ui.css",
    }

app = FastAPI(
    title="Platform Backend API",
    description="B2B Freight App - Organization-level Onboarding API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    **swagger_kwargs,
)

if use_local_swagger:
    app.mount("/static/swagger", StaticFiles(directory=SWAGGER_DIR), name="swagger")
if settings.env in (Environment.DEV, Environment.LOCAL):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://dev-transporter.wetruck.ai",
            "https://dev-shipper.wetruck.ai",
            "https://dev-driver.wetruck.ai",
            "https://dev-bd.wetruck.ai",
            "http://dev.web.wetruck.ai:8991",
            "http://dev.web.wetruck.ai:8992",
            "http://dev.web.wetruck.ai:8993",
            "http://dev.web.wetruck.ai:8994",
            "http://localhost:8991",
            "http://dev.web.wetruck.ai:8991",
            "http://127.0.0.1:8000",
            "http://localhost:8992",
            "http://localhost:8993",
            "http://localhost:8994",
            "http://localhost:5173",
            "http://localhost:3000",        # ← ADD THIS LINE
            "http://127.0.0.1:3000", 
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

elif settings.env == Environment.PROD:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://transporter.wetruck.ai",
            "https://shipper.wetruck.ai",
            "https://driver.wetruck.ai",
            "https://bd.wetruck.ai",
            "https://www.wetruck.ai",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://www.wetruck.ai",
            "http://dev.web.wetruck.ai",
            "http://dev.web.wetruck.ai:8991",
            "http://dev.web.wetruck.ai:3000",
            "http://localhost:8991",
            "http://localhost:8992",
            "http://localhost:8993",
            "http://localhost:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# -------------------------
# Middleware
# -------------------------

# Logs method, path, IP, status code
app.add_middleware(RequestLoggingMiddleware)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(SecurityHeadersMiddleware)

# -------------------------
# Global Exception Handlers
# -------------------------
app.add_exception_handler(CustomHTTPException, custom_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.add_exception_handler(
    DatabaseException,
    database_exception_handler,
)
# -------------------------
# Routes
# -------------------------
app.include_router(api_router)
