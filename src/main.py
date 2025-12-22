from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from src.middlewares.request_logging import RequestLoggingMiddleware
from src.middlewares.security_headers import SecurityHeadersMiddleware
from src.core.exceptions import (
    CustomHTTPException,
    http_exception_handler,
    validation_exception_handler,
    custom_exception_handler,
    unhandled_exception_handler,
)
from src.core.settings.env import Environment
from src.core.settings.settings import settings
from src.api.router import api_router

app = FastAPI(
    title="WeTruck API",
    version="1.0.0",
    description="WeTruck Freight Operations Backend API",
    swagger_ui_parameters={
        "persistAuthorization": True,
    },
)


# CORS configuration
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
            "http://localhost:8992",
            "http://localhost:8993",
            "http://localhost:8994",
            "http://localhost:5173",
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

# -------------------------
# Routes
# -------------------------
app.include_router(api_router)
