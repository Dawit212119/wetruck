from __future__ import annotations
from enum import Enum


class PriceQuoteStatusEnum(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"