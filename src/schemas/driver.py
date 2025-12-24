from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class DriverCreate(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    phone_number: str = Field(..., min_length=9, max_length=15)
    email: EmailStr
    driver_license_number: str = Field(..., min_length=1, max_length=100)

class DriverUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=2, max_length=50)
    last_name: Optional[str] = Field(None, min_length=2, max_length=50)
    phone_number: Optional[str] = Field(None, min_length=9, max_length=15)
    email: Optional[EmailStr] = None
    driver_license_number: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[str] = None

class DriverResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    phone_number: str
    email: str
    driver_license_number: str
    organization_id: int
    status: str

    model_config = {
        "from_attributes": True
    }
