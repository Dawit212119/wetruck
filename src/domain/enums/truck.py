from __future__ import annotations
from enum import Enum


class TruckStatusEnum(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    OUT_OF_SERVICE = "out_of_service"


class TruckTypeEnum(Enum):
    FLATBED = "flatbed"
    TRAILER = "trailer"


class TruckAxleTypeEnum(Enum):
    SINGLE = "single"
    DOUBLE = "double"
    TRIPLE = "triple"