#  schemas for onboarding flow


from typing  import Optional. List,Dict, Any
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime  import datetime


# registration  schema  that are used bt  cs teams or admin  

class RegistrationRequest(BaseModel):
    email:EmailStr
    password: str=Field(
        ..., min_lenght=8,decription="Password must be at least 8 char"
        
    )