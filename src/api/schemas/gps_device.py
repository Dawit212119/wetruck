from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime
from src.api.schemas.generic import PaginatedResponse


class GPSDeviceBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    external_device_id: str = Field(..., max_length=255)
    imei_number: str = Field(..., max_length=50)
    device_name: Optional[str] = Field(None, max_length=255)
    device_model: Optional[str] = Field(None, max_length=255)
    expire_date: datetime
    last_synced_at: datetime
    status: Optional[bool] = Field(default=True)


class GPSDeviceCreate(GPSDeviceBase):
    truck_id: int = Field(..., description="Truck ID to bind the GPS device to")


class GPSDeviceUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    external_device_id: Optional[str] = Field(None, max_length=255)
    imei_number: Optional[str] = Field(None, max_length=50)
    device_name: Optional[str] = Field(None, max_length=255)
    device_model: Optional[str] = Field(None, max_length=255)
    expire_date: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None
    status: Optional[bool] = None
    truck_id: Optional[int] = None  # Use 0 to unlink, or truck_id to assign


class GPSDeviceResponse(GPSDeviceBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GPSDevicePaginatedResponse(PaginatedResponse):
    items: List[GPSDeviceResponse]



