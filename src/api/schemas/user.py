from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, validator
from enum import Enum

from src.domain.enums.user import UserStatusEnum, UserTypeEnum


class UserRegisterBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8)
    email: EmailStr
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    user_type: UserTypeEnum
    status: Optional[UserStatusEnum] = UserStatusEnum.ACTIVE 

    # Only required for TRANSPORTER and SHIPPER
    organization_id: Optional[int] = None

    @validator("organization_id")
    def validate_organization_id(cls, v, values):
        user_type = values.get("user_type")
        if user_type in (UserTypeEnum.TRANSPORTER, UserTypeEnum.SHIPPER):
            if v is None:
                raise ValueError("organization_id is required for TRANSPORTER and SHIPPER users")
        if user_type == UserTypeEnum.BACKOFFICE and v is not None:
            # Optional: allow backoffice to have org, or forbid it
            # Here we allow it (e.g., super admin in a specific org)
            pass
        return v

class UserRegisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    user_type: UserTypeEnum
    organization_id: Optional[int]
    created_at: datetime


from pydantic import BaseModel, ConfigDict


# ---------- Base ----------
class UserProfileBase(BaseModel):
    user_id: int


# ---------- Read schemas ----------
class BackOfficeUserBase(UserProfileBase):
    model_config = ConfigDict(from_attributes=True)


class TransporterUserBase(UserProfileBase):
    model_config = ConfigDict(from_attributes=True)


class ShipperUserBase(UserProfileBase):
    model_config = ConfigDict(from_attributes=True)
