from pydantic import BaseModel, EmailStr

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