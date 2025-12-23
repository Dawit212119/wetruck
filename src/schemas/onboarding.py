from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


# Request Schemas
class RegistrationRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    phone: Optional[str] = None
    role: str = Field(..., pattern="^(shipper|transporter|cs|admin)$")
    company_email: Optional[EmailStr] = None
    company_phone: Optional[str] = None


class ProfileBasicsData(BaseModel):
    name: str = Field(..., min_length=1)
    phone: Optional[str] = None
    email: EmailStr
    document_urls: Optional[List[str]] = Field(default=[], description="URLs of documents (ID, license)")


class ProfileBasicsStepRequest(BaseModel):
    step_data: ProfileBasicsData


class BankAccount(BaseModel):
    bank_name: str
    account_number: str
    account_holder_name: str
    branch: Optional[str] = None


class PaymentPreferencesData(BaseModel):
    bank_accounts: List[BankAccount] = Field(..., min_items=1, description="At least one bank account required")
    payment_methods: List[str] = Field(default=["telebirr"], description="List of payment methods")


class PaymentPreferencesStepRequest(BaseModel):
    step_data: PaymentPreferencesData


class RoutePreferencesData(BaseModel):
    preferred_routes: List[str] = Field(..., description="List of preferred routes")


class RoutePreferencesStepRequest(BaseModel):
    step_data: RoutePreferencesData


class TutorialData(BaseModel):
    completed_at: Optional[datetime] = None
    score: Optional[int] = Field(None, ge=0, le=100, description="Tutorial score 0-100")


class TutorialStepRequest(BaseModel):
    step_data: TutorialData


class AddUserToOrganizationRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    phone: Optional[str] = None
    role_in_org: str = Field(..., description="Role within organization")
    permissions: Optional[Dict[str, Any]] = Field(default=None, description="Permissions for the user")


class BulkAddUsersRequest(BaseModel):
    users: List[AddUserToOrganizationRequest] = Field(..., min_items=1, description="List of users to add")


# Response Schemas
class MessageResponse(BaseModel):
    code: int
    msg: str
    data: Optional[Dict[str, Any]] = None


class OnboardingStepResponse(BaseModel):
    id: int
    organization_id: int
    role: str
    current_step: Optional[str]
    completed_steps: Optional[List[str]]
    step_data: Optional[Dict[str, Any]]
    status: str
    is_complete: bool
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class OnboardingStatusResponse(BaseModel):
    organization_id: int
    onboarding_status: str
    onboarding_step: Optional[str]
    onboarding_completed_at: Optional[datetime]
    current_onboarding_step: Optional[OnboardingStepResponse] = None
