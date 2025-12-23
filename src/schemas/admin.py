from typing import Optional, Any, List
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


# CS User Management Schemas
class CreateCSUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UpdateCSUserRequest(BaseModel):
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|suspended)$")
    password: Optional[str] = Field(None, min_length=8, description="Password must be at least 8 characters")


class CSUserResponse(BaseModel):
    id: int
    email: str
    username: str
    phone: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    user_type: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AdminUserResponse(BaseModel):
    id: int
    email: str
    username: str
    phone: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    user_type: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# System Config Schemas
class ConfigItemRequest(BaseModel):
    config_key: str
    config_value: Any = Field(..., description="Config value (can be number, string, object, etc.)")


class ConfigItemResponse(BaseModel):
    id: int
    config_key: str
    config_value: Any
    version: int
    updated_by: Optional[int]
    updated_at: datetime

    class Config:
        from_attributes = True


