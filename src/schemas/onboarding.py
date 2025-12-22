#  schemas for onboarding flow


from typing  import Optional. List,Dict, Any
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime  import datetime


# registration  schema  that are used bt  cs teams or admin  

class RegistrationRequest(BaseModel):
    email:EmailStr
    password: str = Field(..., min_length=8,decription="Password must be at least 8 char")
    role: str =Field(...,pattern="^(shipper|transporter|cs|admin)$")
    company_email:Optional[EmailStr]=Field(default=None,description="org level email")
    company_phone:Optional[str]=Field(default=None,description="org level phone #")


#   profile basics  schema .  those  user try to fill info about the company info
class ProfileBasicsData(BaseModel):
    name: str = Field(...,min_length=1)
    phone: Optional[str]=None
    email: EmailStrr
    document_urls: Optional[List[str]]=Field(default=[],description="urls of the documents (id,license)")


class ProfileBasicsStepRequest(BaseModel):
    step_data: ProfileBasicsData


#  payment select  sche,

class  BankAccount(BaseModel):
    bank_name: str
    account_number: str
    account_holder_name:str
    branch: Optional[str]=None

class PaymentPreferncesData(BaseModel):
    bank_accounts: List[BankAccount]=Field(...,min_items=1, description="At least one bank account required")
    payment_methods:List[str]=Field(default=["telebirr"],description="list of patment methinds") 
class PaymentPreferncesStepRequest(BaseModel):
    step_data: PaymentPreferncesData

#  route
class RoutePreferencesData(BaseMode):
    preferred_routes:List[str]= Field(..., description="List of preferred routes")
class RoutePreferencesStepRequest(BaseMode):

    step_data: RoutePreferencesData


# tutorial

class TutorialData(BaseModel):
    completed_at:Optional[datetime]=None
    score:Optional[int]=Field(None,ge=0,le=100)

class TutorialStepRequest(BaseMode):
    step_data: TutorialData

#  generic onboarding step response

class OnboardingStepResponse(BaseMode):
    id:int
    user_id:int
    role:str
    current_step: Optional[str]
    completed_steps:Optional[datetime]
    status:str
    is_complete: bool
    created_at: datetime
    updated_at:datetime

# onboarding status response

class OnboardingStatusResponse(BaseModel):
    user_id:int 
    onboard_status:str
    onboard_step: Optional[str]
    onboarding_completed_at: Optional[datetime]
    current_onboarding_step: Optional[OnboardingStatusResponse]


class AddUserToOrganizationRequest(BaseModel):
    email:EmailStr
    password:str= Field(..., min_length=8, description="passwd must be at least 8 char")
    phone:Optional[str]= None
    role_in_org: Optional[str]=Field(...,description="role within org")   # future will be implemented  
    permissions:Optional[Dict[str,Any]]=Field(default=None,description="permission for that user like  upload:false ")

class MessageResponse(BaseModel):
    code:int
    msg: str
    data:Optional[Dict[str,Any]]=None       

