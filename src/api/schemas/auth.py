from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, computed_field

from src.domain.enums.user import UserStatusEnum, UserTypeEnum

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    role: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    role: str
    expires_in: int


class UserMeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    # full_name: Optional[str] = None  # Optional: computed as first_name + last_name if you want

    user_type: UserTypeEnum
    status: UserStatusEnum
    organization_id: Optional[int] = None

    created_at: datetime
    updated_at: Optional[datetime] = None

    @computed_field
    @property
    def full_name(self) -> Optional[str]:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return (self.first_name or self.last_name or None)