"""
Onboarding / Company Setup API endpoints

Organization-level onboarding for B2B freight app.
CS/admin creates organizations and users; org users log in and fill company setup (non-blocking).
"""
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.db.session import get_db
from src.core.exceptions import CustomHTTPException
from src.models.models import (
    User,
    Organization,
    OnboardingStep,
    OrgUser,
)
from src.schemas.onboarding import (
    RegistrationRequest,
    ProfileBasicsStepRequest,
    PaymentPreferencesStepRequest,
    RoutePreferencesStepRequest,
    TutorialStepRequest,
    OnboardingStepResponse,
    OnboardingStatusResponse,
    MessageResponse,
    AddUserToOrganizationRequest,
    BulkAddUsersRequest,
)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


def hash_password(password: str) -> str:
    """
    Hash password using bcrypt.
    TODO: Replace with proper bcrypt implementation for production
    """
    import hashlib
    # Temporary implementation - MUST be replaced with bcrypt for production
    return hashlib.sha256(password.encode()).hexdigest()


def now_utc() -> datetime:
    """Get current UTC datetime"""
    return datetime.now(timezone.utc)


@router.post("/register", response_model=MessageResponse)
async def register(request: RegistrationRequest, db: AsyncSession = Depends(get_db)):
    """
    Internal helper (CS/admin): create organization + first user.
    Creates organization, user, org_user (role="owner"), and onboarding_steps record.
    """
    # Check if user already exists
    result = await db.execute(select(User).filter(User.email == request.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise CustomHTTPException(
            status_code=status.HTTP_409_CONFLICT,
            msg="User already exists"
        )

    now = now_utc()

    # Create organization
    organization = Organization(
        type=request.role.capitalize(),  # Shipper, Transporter, etc.
        name=f"{request.role} Organization",  # Default name
        company_email=request.company_email,
        company_phone=request.company_phone,
        onboarding_status="in_progress",
        onboarding_step="profile_basics",
        created_at=now,
        updated_at=now
    )
    db.add(organization)
    await db.flush()

    # Create user
    user = User(
        organization_id=organization.id,
        user_type=request.role,
        username=request.email,
        password=hash_password(request.password),
        email=request.email,
        phone=request.phone,
        created_at=now,
        updated_at=now
    )
    db.add(user)
    await db.flush()

    # Create org_user (role="owner")
    org_user = OrgUser(
        organization_id=organization.id,
        user_id=user.id,
        role="owner",
        permissions=None,
        status="active",
        created_by=None,  # Created by CS/admin
        created_at=now,
        updated_at=now
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
        created_at=now,
        updated_at=now
    )
    db.add(onboarding_step)

    await db.commit()

    return MessageResponse(
        code=status.HTTP_201_CREATED,
        msg="User registered successfully",
        data={"user_id": user.id, "organization_id": organization.id}
    )


@router.post("/organizations/{organization_id}/users", response_model=MessageResponse)
async def add_user_to_organization(
    organization_id: int,
    request: AddUserToOrganizationRequest,
    created_by_user_id: int = Query(..., description="User ID creating this user (from JWT in production)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Add single user to organization (requires org owner/manager).
    Creates user and org_user entries.
    """
    # Check if organization exists
    org_result = await db.execute(select(Organization).filter(Organization.id == organization_id))
    organization = org_result.scalar_one_or_none()
    if not organization:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="Organization not found"
        )

    # Check if user already exists
    result = await db.execute(select(User).filter(User.email == request.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise CustomHTTPException(
            status_code=status.HTTP_409_CONFLICT,
            msg="User with this email already exists"
        )

    now = now_utc()

    # Create user
    user = User(
        organization_id=organization_id,
        user_type=organization.type.lower(),
        username=request.email,
        password=hash_password(request.password),
        email=request.email,
        phone=request.phone,
        created_at=now,
        updated_at=now
    )
    db.add(user)
    await db.flush()

    # Create org_user
    org_user = OrgUser(
        organization_id=organization_id,
        user_id=user.id,
        role=request.role_in_org,
        permissions=request.permissions,
        status="active",
        created_by=created_by_user_id,
        created_at=now,
        updated_at=now
    )
    db.add(org_user)
    await db.commit()

    return MessageResponse(
        code=status.HTTP_201_CREATED,
        msg="User added to organization successfully",
        data={"user_id": user.id, "org_user_id": org_user.id}
    )


@router.post("/organizations/{organization_id}/users/bulk", response_model=MessageResponse)
async def bulk_add_users_to_organization(
    organization_id: int,
    request: BulkAddUsersRequest,
    created_by_user_id: int = Query(..., description="User ID creating these users (CS user)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk add users to organization (CS).
    Creates multiple user + org_user entries; returns successes/errors.
    """
    # Check if organization exists
    org_result = await db.execute(select(Organization).filter(Organization.id == organization_id))
    organization = org_result.scalar_one_or_none()
    if not organization:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="Organization not found"
        )

    created_users = []
    errors = []
    now = now_utc()

    for user_request in request.users:
        try:
            # Check if user already exists
            result = await db.execute(select(User).filter(User.email == user_request.email))
            existing_user = result.scalar_one_or_none()
            if existing_user:
                errors.append({
                    "email": user_request.email,
                    "error": "User with this email already exists"
                })
                continue

            # Create new user
            new_user = User(
                organization_id=organization_id,
                user_type=organization.type.lower(),
                username=user_request.email,
                password=hash_password(user_request.password),
                email=user_request.email,
                phone=user_request.phone,
                created_at=now,
                updated_at=now
            )
            db.add(new_user)
            await db.flush()

            # Create OrgUser record
            new_org_user = OrgUser(
                organization_id=organization_id,
                user_id=new_user.id,
                role=user_request.role_in_org,
                permissions=user_request.permissions,
                status="active",
                created_by=created_by_user_id,
                created_at=now,
                updated_at=now
            )
            db.add(new_org_user)
            await db.flush()

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
            await db.rollback()
            continue

    await db.commit()

    return MessageResponse(
        code=status.HTTP_201_CREATED,
        msg="Bulk user creation completed",
        data={
            "created": created_users,
            "errors": errors,
            "total_requested": len(request.users),
            "total_created": len(created_users),
            "total_errors": len(errors)
        }
    )


@router.post("/steps/profile-basics", response_model=MessageResponse)
async def complete_profile_basics(
    request: ProfileBasicsStepRequest,
    organization_id: int = Query(..., description="Organization ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Complete profile basics step (organization-level).
    Updates completed_steps, step_data.profile_basics, sets current_step="payment_preferences",
    updates organization.onboarding_step.
    """
    # Check organization exists
    org_result = await db.execute(select(Organization).filter(Organization.id == organization_id))
    organization = org_result.scalar_one_or_none()
    if not organization:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="Organization not found"
        )

    # Get onboarding step
    step_result = await db.execute(
        select(OnboardingStep).filter(OnboardingStep.organization_id == organization_id)
    )
    onboarding_step = step_result.scalar_one_or_none()
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

    await db.commit()

    return MessageResponse(
        code=status.HTTP_200_OK,
        msg="Profile basics completed"
    )


@router.post("/steps/payment-preferences", response_model=MessageResponse)
async def complete_payment_preferences(
    request: PaymentPreferencesStepRequest,
    organization_id: int = Query(..., description="Organization ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Complete payment preferences step (organization-level).
    Updates completed_steps, step_data.payment_preferences, sets current_step="route_preferences".
    """
    # Check organization exists
    org_result = await db.execute(select(Organization).filter(Organization.id == organization_id))
    organization = org_result.scalar_one_or_none()
    if not organization:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="Organization not found"
        )

    # Get onboarding step
    step_result = await db.execute(
        select(OnboardingStep).filter(OnboardingStep.organization_id == organization_id)
    )
    onboarding_step = step_result.scalar_one_or_none()
    if not onboarding_step:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="Onboarding step not found"
        )

    # Update step data
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

    await db.commit()

    return MessageResponse(
        code=status.HTTP_200_OK,
        msg="Payment preferences completed"
    )


@router.post("/steps/route-preferences", response_model=MessageResponse)
async def complete_route_preferences(
    request: RoutePreferencesStepRequest,
    organization_id: int = Query(..., description="Organization ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Complete route preferences step (organization-level).
    Updates completed_steps, step_data.route_preferences, sets current_step="tutorial".
    """
    # Check organization exists
    org_result = await db.execute(select(Organization).filter(Organization.id == organization_id))
    organization = org_result.scalar_one_or_none()
    if not organization:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="Organization not found"
        )

    # Get onboarding step
    step_result = await db.execute(
        select(OnboardingStep).filter(OnboardingStep.organization_id == organization_id)
    )
    onboarding_step = step_result.scalar_one_or_none()
    if not onboarding_step:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="Onboarding step not found"
        )

    # Update step data
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

    await db.commit()

    return MessageResponse(
        code=status.HTTP_200_OK,
        msg="Route preferences completed"
    )


@router.post("/steps/tutorial", response_model=MessageResponse)
async def complete_tutorial(
    request: TutorialStepRequest,
    organization_id: int = Query(..., description="Organization ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Complete tutorial step (organization-level).
    Updates completed_steps, step_data.tutorial, sets status="complete",
    organization.onboarding_status="complete", organization.onboarding_step="tutorial".
    """
    # Check organization exists
    org_result = await db.execute(select(Organization).filter(Organization.id == organization_id))
    organization = org_result.scalar_one_or_none()
    if not organization:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="Organization not found"
        )

    # Get onboarding step
    step_result = await db.execute(
        select(OnboardingStep).filter(OnboardingStep.organization_id == organization_id)
    )
    onboarding_step = step_result.scalar_one_or_none()
    if not onboarding_step:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="Onboarding step not found"
        )

    now = now_utc()

    # Update step data
    completed_steps = list(onboarding_step.completed_steps) if onboarding_step.completed_steps else []
    if "tutorial" not in completed_steps:
        completed_steps.append("tutorial")

    step_data = dict(onboarding_step.step_data) if onboarding_step.step_data else {}
    step_data["tutorial"] = request.step_data.model_dump()

    onboarding_step.completed_steps = completed_steps
    onboarding_step.step_data = step_data
    onboarding_step.current_step = "tutorial"
    onboarding_step.status = "complete"
    onboarding_step.is_complete = True
    onboarding_step.completed_at = now
    onboarding_step.updated_at = now

    # Update organization onboarding status
    organization.onboarding_status = "complete"
    organization.onboarding_step = "tutorial"
    organization.onboarding_completed_at = now
    organization.updated_at = now

    await db.commit()

    return MessageResponse(
        code=status.HTTP_200_OK,
        msg="Tutorial completed. Onboarding finished!"
    )


@router.get("/status/{organization_id}", response_model=OnboardingStatusResponse)
async def get_onboarding_status(
    organization_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get current onboarding status for an organization.
    Returns org onboarding status + current step.
    """
    # Get organization
    org_result = await db.execute(select(Organization).filter(Organization.id == organization_id))
    organization = org_result.scalar_one_or_none()
    if not organization:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="Organization not found"
        )

    # Get onboarding step
    step_result = await db.execute(
        select(OnboardingStep).filter(OnboardingStep.organization_id == organization_id)
    )
    onboarding_step = step_result.scalar_one_or_none()

    current_step_response = None
    if onboarding_step:
        current_step_response = OnboardingStepResponse(
            id=onboarding_step.id,
            organization_id=onboarding_step.organization_id,
            role=onboarding_step.role,
            current_step=onboarding_step.current_step,
            completed_steps=onboarding_step.completed_steps,
            step_data=onboarding_step.step_data,
            status=onboarding_step.status,
            is_complete=onboarding_step.is_complete,
            completed_at=onboarding_step.completed_at,
            created_at=onboarding_step.created_at,
            updated_at=onboarding_step.updated_at
        )

    return OnboardingStatusResponse(
        organization_id=organization.id,
        onboarding_status=organization.onboarding_status,
        onboarding_step=organization.onboarding_step,
        onboarding_completed_at=organization.onboarding_completed_at,
        current_onboarding_step=current_step_response
    )


@router.get("/current-step/{organization_id}", response_model=MessageResponse)
async def get_current_step(
    organization_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get current onboarding step for an organization (non-blocking; for progress UI).
    """
    # Get organization
    org_result = await db.execute(select(Organization).filter(Organization.id == organization_id))
    organization = org_result.scalar_one_or_none()
    if not organization:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="Organization not found"
        )

    # Get onboarding step
    step_result = await db.execute(
        select(OnboardingStep).filter(OnboardingStep.organization_id == organization_id)
    )
    onboarding_step = step_result.scalar_one_or_none()

    if not onboarding_step:
        return MessageResponse(
            code=status.HTTP_404_NOT_FOUND,
            msg="Onboarding step not found",
            data=None
        )

    return MessageResponse(
        code=status.HTTP_200_OK,
        msg="Current step retrieved",
        data={
            "current_step": onboarding_step.current_step,
            "completed_steps": onboarding_step.completed_steps,
            "status": onboarding_step.status,
            "is_complete": onboarding_step.is_complete,
            "organization_onboarding_status": organization.onboarding_status,
            "organization_onboarding_step": organization.onboarding_step
        }
    )
