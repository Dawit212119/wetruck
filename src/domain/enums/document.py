
from __future__ import annotations
from enum import Enum


class DocumentTypeEnum(Enum):
    TRADE_LICENCE = "trade_licence"
    ID = "id"
    OTHER = "other"

class DocumentStatusEnum(Enum):
    APPROVED = "approved"
    PENDING = "pending"
    IN_ACTIVE = "in_active"