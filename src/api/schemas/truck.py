from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

from enum import Enum
from enum import IntEnum


class TruckStatusEnum(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    OUT_OF_SERVICE = "out_of_service"


class TruckTypeEnum(Enum):
    FLATBED = "flatbed"
    TRAILER = "trailer"


class TruckBase(BaseModel):
    status: TruckStatusEnum
    truck_type: TruckTypeEnum
    vin: str = Field(..., max_length=17)
    plate_number: str = Field(..., max_length=20)
    registration_date: date
    gov_id: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    color: Optional[str] = None
    capacity_quintal: int
    libre_key: Optional[str] = None
    gps_device_id: Optional[int] = None

class TruckCreate(TruckBase):
    pass

class TruckUpdate(BaseModel):
    status: Optional[TruckStatusEnum] = None
    truck_type: Optional[TruckTypeEnum] = None
    vin: Optional[str] = None
    plate_number: Optional[str] = None
    registration_date: Optional[date] = None
    gov_id: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    color: Optional[str] = None
    capacity_quintal: Optional[int] = None
    libre_key: Optional[str] = None
    gps_device_id: Optional[int] = None

class TruckRead(TruckBase):
    id: int
    # add relationships if needed, e.g., gps_device: Optional[GPSDeviceRead]

    class Config:
        from_attributes = True  # for ORM mode