"""
Onboarding / Company Setup API endpoints

Note: OTP verification is handled elsewhere; this module assumes CS/admin
creates organizations and users. These endpoints are non-blocking helpers
for company setup wizards.
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.core.db.session import get_db
from src.core.exceptions import CustomHTTPException
from src.models.models import (
    User, 
    Organization, 
    OnboardingStep, 
    OrgUser,
    Base
)
from src.schemas.onboarding import (
    RegistrationRequest,
    ProfileBasicsStepRequest,
    PaymentPreferncesStepRequest,
    RoutePreferencesStepRequest,
    TutorialStepRequest,
    OnboardingStepResponse,
    OnboardingStatusResponse,
    MessageResponse,
    AddUserToOrganizationRequest,
    BulkAddUsersRequest
)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


def hash_password(password: str) -> str:
    """
    Hash password using bcrypt.
    TODO: Replace with proper bcrypt implementation:
    import bcrypt
    return bcrypt.hashpw((password + PEPPER).encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    """
    import hashlib
    # Temporary implementation - MUST be replaced with bcrypt for production
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(raw_password: str, hashed_password: str) -> bool:
    """
    Verify password.
    TODO: Replace with proper bcrypt verification
    """
    import hashlib
    # Temporary implementation - MUST be replaced with bcrypt for production
    return hashlib.sha256(raw_password.encode()).hexdigest() == hashed_password


def now_utc() -> datetime:
    """Get current UTC datetime"""
    return datetime.utcnow()


@router.post("/register", response_model=MessageResponse)
def register(request: RegistrationRequest, db: Session = Depends(get_db)):
    """
    Internal helper to create organization + first user (used by CS/admin tools).
    No OTP verification is performed here.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise CustomHTTPException(
            status_code=status.HTTP_409_CONFLICT,
            msg="User already exists"
        )
    
    # Create organization (first user creates org)
    organization = Organization(
        type=request.role.capitalize(),  # Shipper, Transporter, etc.
        name=f"{request.role} Organization",  # Default name
        company_email=request.company_email,
        company_phone=request.company_phone,
        created_at=now_utc(),
        updated_at=now_utc()
    )
    db.add(organization)
    db.flush()
    
    # Create user
    user = User(
        user_type=request.role,
        username=request.email,  # Using email as username
        password=hash_password(request.password),
        email=request.email,
        phone=request.phone,
        organization_id=organization.id,
        created_at=now_utc(),
        updated_at=now_utc()
    )
    db.add(user)
    db.flush()
    
    # Create OrgUser record for the first user (primary user)
    org_user = OrgUser(
        organization_id=organization.id,
        user_id=user.id,
        role="owner",  # First user is owner
        permissions=None,
        status="active",
        created_by=None,  # Created by CS/admin
        created_at=now_utc(),
        updated_at=now_utc()
    )
    db.add(org_user)
    
    # Create onboarding_steps record
    onboarding_step = OnboardingStep(
        organization_id=organization.id,
        role=request.role,
        current_step="profile_basics",
        completed_steps=[],
        step_data={},
        status="in_progress",
        is_complete=False,
        created_at=now_utc(),
        updated_at=now_utc()
    )
    db.add(onboarding_step)
    
    db.commit()
    
    return MessageResponse(
        code=status.HTTP_201_CREATED,
        msg="User registered successfully",
        data={"user_id": user.id, "organization_id": organization.id}
    )


@router.post("/steps/profile-basics", response_model=MessageResponse)
def complete_profile_basics(request: ProfileBasicsStepRequest, organization_id: int, db: Session = Depends(get_db)):
    """
    Complete profile basics step (organization-level)
    """
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="Organization not found"
        )

    onboarding_step = db.query(OnboardingStep).filter(OnboardingStep.organization_id == organization_id).first()
    if not onboarding_step:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="Onboarding step not found"
        )
    
    # Update step data
    completed_steps = list(onboarding_step.completed_steps) if onboarding_step.completed_steps else []
    if "profile_basics" not in completed_steps:
        completed_steps.append("profile_basics")
    
    step_data = dict(onboarding_step.step_data) if onboarding_step.step_data else {}
    step_data["profile_basics"] = request.step_data.model_dump()
    
    onboarding_step.completed_steps = completed_steps
    onboarding_step.step_data = step_data
    onboarding_step.current_step = "payment_preferences"
    onboarding_step.updated_at = now_utc()
    
    # Update organization onboarding status
    organization.onboarding_step = "payment_preferences"
    organization.updated_at = now_utc()
    
    db.commit()
    
    return MessageResponse(
        code=status.HTTP_200_OK,
        msg="Profile basics completed"
    )


@router.post("/steps/payment-preferences", response_model=MessageResponse)
def complete_payment_preferences(request: PaymentPreferncesStepRequest, organization_id: int, db: Session = Depends(get_db)):
    """
    Complete payment preferences step
    """
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="Organization not found"
        )
    
    onboarding_step = db.query(OnboardingStep).filter(OnboardingStep.organization_id == organization_id).first()
    if not onboarding_step:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="Onboarding step not found"
        )
    
    # Update step data - handle JSONB properly
    completed_steps = list(onboarding_step.completed_steps) if onboarding_step.completed_steps else []
    if "payment_preferences" not in completed_steps:
        completed_steps.append("payment_preferences")
    
    step_data = dict(onboarding_step.step_data) if onboarding_step.step_data else {}
    step_data["payment_preferences"] = request.step_data.model_dump()
    
    onboarding_step.completed_steps = completed_steps
    onboarding_step.step_data = step_data
    onboarding_step.current_step = "route_preferences"
    onboarding_step.updated_at = now_utc()
    
    # Update organization onboarding status
    organization.onboarding_step = "route_preferences"
    organization.updated_at = now_utc()
    
    db.commit()
    
    return MessageResponse(
        code=status.HTTP_200_OK,
        msg="Payment preferences completed"
    )


@router.post("/steps/route-preferences", response_model=MessageResponse)
def complete_route_preferences(request: RoutePreferencesStepRequest, organization_id: int, db: Session = Depends(get_db)):
    """
    Complete route preferences step
    """
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="Organization not found"
        )
    
    onboarding_step = db.query(OnboardingStep).filter(OnboardingStep.organization_id == organization_id).first()
    if not onboarding_step:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="Onboarding step not found"
        )
    
    # Update step data - handle JSONB properly
    completed_steps = list(onboarding_step.completed_steps) if onboarding_step.completed_steps else []
    if "route_preferences" not in completed_steps:
        completed_steps.append("route_preferences")
    
    step_data = dict(onboarding_step.step_data) if onboarding_step.step_data else {}
    step_data["route_preferences"] = request.step_data.model_dump()
    
    onboarding_step.completed_steps = completed_steps
    onboarding_step.step_data = step_data
    onboarding_step.current_step = "tutorial"
    onboarding_step.updated_at = now_utc()
    
    # Update organization onboarding status
    organization.onboarding_step = "tutorial"
    organization.updated_at = now_utc()
    
    db.commit()
    
    return MessageResponse(
        code=status.HTTP_200_OK,
        msg="Route preferences completed"
    )


@router.post("/steps/tutorial", response_model=MessageResponse)
def complete_tutorial(request: TutorialStepRequest, organization_id: int, db: Session = Depends(get_db)):
    """
    Complete tutorial step (final step for shipper)
    """
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="Organization not found"
        )
    
    onboarding_step = db.query(OnboardingStep).filter(OnboardingStep.organization_id == organization_id).first()
    if not onboarding_step:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="Onboarding step not found"
        )
    
    # Update step data - handle JSONB properly
    completed_steps = list(onboarding_step.completed_steps) if onboarding_step.completed_steps else []
    if "tutorial" not in completed_steps:
        completed_steps.append("tutorial")
    
    step_data = dict(onboarding_step.step_data) if onboarding_step.step_data else {}
    tutorial_data = request.step_data.model_dump()
    if not tutorial_data.get("completed_at"):
        tutorial_data["completed_at"] = now_utc().isoformat()
    step_data["tutorial"] = tutorial_data
    
    onboarding_step.completed_steps = completed_steps
    onboarding_step.step_data = step_data
    onboarding_step.status = "complete"
    onboarding_step.is_complete = True
    onboarding_step.completed_at = now_utc()
    onboarding_step.updated_at = now_utc()
    
    # Update organization onboarding status
    organization.onboarding_status = "complete"
    organization.onboarding_completed_at = now_utc()
    organization.onboarding_step = "tutorial"
    organization.updated_at = now_utc()
    
    db.commit()
    
    return MessageResponse(
        code=status.HTTP_200_OK,
        msg="Tutorial completed. Onboarding finished!"
    )


@router.get("/status/{organization_id}", response_model=OnboardingStatusResponse)
def get_onboarding_status(organization_id: int, db: Session = Depends(get_db)):
    """
    Get current onboarding status for an organization
    """
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="Organization not found"
        )
    
    onboarding_step = db.query(OnboardingStep).filter(OnboardingStep.organization_id == organization_id).first()
    
    current_step_response = None
    if onboarding_step:
        current_step_response = OnboardingStepResponse(
            id=onboarding_step.id,
            organization_id=onboarding_step.organization_id,
            role=onboarding_step.role,
            current_step=onboarding_step.current_step,
            completed_steps=onboarding_step.completed_steps,
            status=onboarding_step.status,
            is_complete=onboarding_step.is_complete,
            created_at=onboarding_step.created_at,
            updated_at=onboarding_step.updated_at
        )
    
    return OnboardingStatusResponse(
        organization_id=org.id,
        onboarding_status=org.onboarding_status,
        onboarding_step=org.onboarding_step,
        onboarding_completed_at=org.onboarding_completed_at,
        current_onboarding_step=current_step_response
    )


@router.get("/current-step/{organization_id}", response_model=MessageResponse)
def get_current_step(organization_id: int, db: Session = Depends(get_db)):
    """
    Get current onboarding step for an organization
    """
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="Organization not found"
        )
    
    onboarding_step = db.query(OnboardingStep).filter(OnboardingStep.organization_id == organization_id).first()
    
    if not onboarding_step:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="Onboarding step not found"
        )
    
    return MessageResponse(
        code=status.HTTP_200_OK,
        msg="Current step retrieved",
        data={
            "current_step": onboarding_step.current_step,
            "completed_steps": onboarding_step.completed_steps,
            "status": onboarding_step.status,
            "is_complete": onboarding_step.is_complete
        }
    )


@router.post("/organizations/{organization_id}/users", response_model=MessageResponse)
def add_user_to_organization(
    organization_id: int,
    request: AddUserToOrganizationRequest,
    created_by_user_id: int,  # TODO: Get from JWT token in production
    db: Session = Depends(get_db)
):
    """
    Add a new user to an existing organization (called by organization owner/primary user)
    """
    # Verify organization exists
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="Organization not found"
        )
    
    # Verify the requester is a member of the organization with appropriate permissions
    # Check if user is in the organization and has owner/manager role
    org_user = db.query(OrgUser).filter(
        OrgUser.organization_id == organization_id,
        OrgUser.user_id == created_by_user_id,
        OrgUser.status == "active"
    ).first()
    
    if not org_user or org_user.role not in ["owner", "manager"]:
        raise CustomHTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            msg="Only organization owners/managers can add users"
        )
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise CustomHTTPException(
            status_code=status.HTTP_409_CONFLICT,
            msg="User with this email already exists"
        )
    
    # Create new user
    new_user = User(
        user_type=organization.type.lower(),  # e.g., "shipper" from "Shipper"
        username=request.email,
        password=hash_password(request.password),
        email=request.email,
        phone=request.phone,
        organization_id=organization_id,
        created_at=now_utc(),
        updated_at=now_utc()
    )
    db.add(new_user)
    db.flush()
    
    # Create OrgUser record (for additional users in organization)
    new_org_user = OrgUser(
        organization_id=organization_id,
        user_id=new_user.id,
        role=request.role_in_org,
        permissions=request.permissions,
        status="active",
        created_by=created_by_user_id,
        created_at=now_utc(),
        updated_at=now_utc()
    )
    db.add(new_org_user)
    
    # Note: Onboarding steps are organization-level, so we don't create a new one
    # The organization already has its onboarding_step record
    
    db.commit()

    return MessageResponse(
        code=status.HTTP_201_CREATED,
        msg="User added to organization successfully.",
        data={
            "user_id": new_user.id,
            "organization_id": organization_id,
            "org_user_id": new_org_user.id
        }
    )


@router.post("/organizations/{organization_id}/users/bulk", response_model=MessageResponse)
def bulk_add_users_to_organization(
    organization_id: int,
    request: BulkAddUsersRequest,
    created_by_user_id: int,  # TODO: Get from JWT token in production (CS user)
    db: Session = Depends(get_db)
):
    """
    Bulk add multiple users to an organization (used by CS team)
    """
    # Verify organization exists
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="Organization not found"
        )
    
    # For CS team, we can skip permission check or check if created_by_user_id is CS
    # For now, we'll allow it if the user exists (CS should have proper auth)
    
    created_users = []
    errors = []
    
    for user_request in request.users:
        try:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == user_request.email).first()
            if existing_user:
                errors.append({
                    "email": user_request.email,
                    "error": "User with this email already exists"
                })
                continue
            
            # Create new user
            new_user = User(
                user_type=organization.type.lower(),
                username=user_request.email,
                password=hash_password(user_request.password),
                email=user_request.email,
                phone=user_request.phone,
                organization_id=organization_id,
                created_at=now_utc(),
                updated_at=now_utc()
            )
            db.add(new_user)
            db.flush()
            
            # Create OrgUser record
            new_org_user = OrgUser(
                organization_id=organization_id,
                user_id=new_user.id,
                role=user_request.role_in_org,
                permissions=user_request.permissions,
                status="active",
                created_by=created_by_user_id,
                created_at=now_utc(),
                updated_at=now_utc()
            )
            db.add(new_org_user)
            
            created_users.append({
                "user_id": new_user.id,
                "email": new_user.email,
                "org_user_id": new_org_user.id
            })
            
        except Exception as e:
            errors.append({
                "email": user_request.email,
                "error": str(e)
            })
            db.rollback()
            continue
    
    db.commit()
    
    return MessageResponse(
        code=status.HTTP_201_CREATED,
        msg=f"Bulk user creation completed. {len(created_users)} users created, {len(errors)} errors.",
        data={
            "organization_id": organization_id,
            "created_users": created_users,
            "errors": errors if errors else None
        }
    )

