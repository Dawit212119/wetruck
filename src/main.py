from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from src.core.settings.env import Environment
from src.api import api_router
from src.core.exceptions import CustomHTTPException, custom_http_exception_handler
from src.middlewares import ExceptionHandlerMiddleware
from src.middlewares.security_headers import SecurityHeadersMiddleware
from src.core.settings.settings import settings


app = FastAPI()
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
            "http://localhost:5173"
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
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(ExceptionHandlerMiddleware)
app.add_exception_handler(CustomHTTPException, custom_http_exception_handler)
app.include_router(api_router)


