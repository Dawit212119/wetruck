from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr

from src.api.schemas.generic import PaginatedResponse
from src.domain.enums.organization import OrganizationTypeEnum

class OrganizationBase(BaseModel):
    type: OrganizationTypeEnum
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    type: Optional[OrganizationTypeEnum] = None
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class OrganizationRead(OrganizationBase):
    id: int
    deleted: bool = False
    created_at: datetime
    updated_at: datetime


class OrganizationPaginatedResponse(PaginatedResponse):
    items: List[OrganizationRead]