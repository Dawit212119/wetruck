from __future__ import annotations

from aws_lambda_powertools import Logger
from src.core.settings.settings import settings
logger: Logger = Logger(service=f"backend-{settings.env}")
