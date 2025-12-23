"""
Admin API endpoints for CS user management and system configuration.

Protected by admin-only authentication dependency.
"""
from datetime import datetime, timezone
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from src.core.db.session import get_db
from src.core.dependencies import get_current_admin_user
from src.core.exceptions import CustomHTTPException
from src.models.models import User, SystemConfig, Organization
from src.schemas.admin import (
    CreateCSUserRequest,
    UpdateCSUserRequest,
    CSUserResponse,
    AdminUserResponse,
    ConfigItemRequest,
    ConfigItemResponse,
)
from src.schemas.onboarding import MessageResponse

router = APIRouter(prefix="/admin", tags=["admin"])


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


def validate_config_value(config_key: str, config_value: Any) -> None:
    """
    Validate config values based on key.
    Enforce reasonable bounds for known config keys.
    """
    if config_key == "proximity_radius_km":
        if not isinstance(config_value, (int, float)) or config_value <= 0:
            raise CustomHTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                msg="proximity_radius_km must be a positive number"
            )
    elif config_key == "commission_percent":
        if not isinstance(config_value, (int, float)) or not (0 <= config_value <= 100):
            raise CustomHTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                msg="commission_percent must be between 0 and 100"
            )
    elif config_key == "penalty_rate":
        if not isinstance(config_value, (int, float)) or config_value < 0:
            raise CustomHTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                msg="penalty_rate must be a non-negative number"
            )


# CS User Management Endpoints
@router.post("/cs-users", response_model=CSUserResponse, status_code=status.HTTP_201_CREATED)
async def create_cs_user(
    request: CreateCSUserRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new CS user (user_type=cs).
    """
    # Check if email already exists
    result = await db.execute(select(User).filter(User.email == request.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise CustomHTTPException(
            status_code=status.HTTP_409_CONFLICT,
            msg="User with this email already exists"
        )
    
    # Get or create a system organization for admin/CS users
    # In a real system, you might have a dedicated system org
    org_result = await db.execute(
        select(Organization).filter(Organization.type == "System").limit(1)
    )
    system_org = org_result.scalar_one_or_none()
    
    if not system_org:
        # Create a system organization if it doesn't exist
        system_org = Organization(
            type="System",
            name="System",
            onboarding_status="complete",
            created_at=now_utc(),
            updated_at=now_utc()
        )
        db.add(system_org)
        await db.flush()
    
    now = now_utc()
    
    # Create CS user
    cs_user = User(
        organization_id=system_org.id,
        user_type="cs",
        username=request.email,
        password=hash_password(request.password),
        email=request.email,
        phone=request.phone,
        first_name=request.first_name,
        last_name=request.last_name,
        status="active",
        created_at=now,
        updated_at=now
    )
    db.add(cs_user)
    await db.commit()
    await db.refresh(cs_user)
    
    return CSUserResponse(
        id=cs_user.id,
        email=cs_user.email,
        username=cs_user.username,
        phone=cs_user.phone,
        first_name=cs_user.first_name,
        last_name=cs_user.last_name,
        user_type=cs_user.user_type,
        status=cs_user.status,
        created_at=cs_user.created_at,
        updated_at=cs_user.updated_at
    )


@router.get("/cs-users", response_model=List[CSUserResponse])
async def list_cs_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List CS users with pagination.
    """
    result = await db.execute(
        select(User)
        .filter(User.user_type == "cs")
        .offset(skip)
        .limit(limit)
        .order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    
    return [
        CSUserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            phone=user.phone,
            first_name=user.first_name,
            last_name=user.last_name,
            user_type=user.user_type,
            status=user.status,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        for user in users
    ]


@router.get("/cs-users/{user_id}", response_model=CSUserResponse)
async def get_cs_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single CS user by ID.
    """
    result = await db.execute(
        select(User).filter(and_(User.id == user_id, User.user_type == "cs"))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="CS user not found"
        )
    
    return CSUserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        phone=user.phone,
        first_name=user.first_name,
        last_name=user.last_name,
        user_type=user.user_type,
        status=user.status,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.put("/cs-users/{user_id}", response_model=CSUserResponse)
async def update_cs_user(
    user_id: int,
    request: UpdateCSUserRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a CS user (phone, names, status, password).
    """
    result = await db.execute(
        select(User).filter(and_(User.id == user_id, User.user_type == "cs"))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="CS user not found"
        )
    
    # Update fields
    if request.phone is not None:
        user.phone = request.phone
    if request.first_name is not None:
        user.first_name = request.first_name
    if request.last_name is not None:
        user.last_name = request.last_name
    if request.status is not None:
        user.status = request.status
    if request.password is not None:
        user.password = hash_password(request.password)
    
    user.updated_at = now_utc()
    
    await db.commit()
    await db.refresh(user)
    
    return CSUserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        phone=user.phone,
        first_name=user.first_name,
        last_name=user.last_name,
        user_type=user.user_type,
        status=user.status,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.delete("/cs-users/{user_id}", response_model=MessageResponse)
async def delete_cs_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a CS user by setting status to suspended.
    """
    result = await db.execute(
        select(User).filter(and_(User.id == user_id, User.user_type == "cs"))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="CS user not found"
        )
    
    user.status = "suspended"
    user.updated_at = now_utc()
    
    await db.commit()
    
    return MessageResponse(
        code=status.HTTP_200_OK,
        msg=f"CS user {user_id} has been suspended"
    )


# Admin User Endpoints (Optional)
@router.get("/admin-users", response_model=List[AdminUserResponse])
async def list_admin_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List admin users (read-only).
    """
    result = await db.execute(
        select(User)
        .filter(User.user_type == "admin")
        .offset(skip)
        .limit(limit)
        .order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    
    return [
        AdminUserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            phone=user.phone,
            first_name=user.first_name,
            last_name=user.last_name,
            user_type=user.user_type,
            status=user.status,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        for user in users
    ]


# System Config Endpoints
@router.get("/config", response_model=List[ConfigItemResponse])
async def list_config_items(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all system config items.
    """
    result = await db.execute(
        select(SystemConfig).order_by(SystemConfig.config_key)
    )
    configs = result.scalars().all()
    
    return [
        ConfigItemResponse(
            id=config.id,
            config_key=config.config_key,
            config_value=config.config_value,
            version=config.version,
            updated_by=config.updated_by,
            updated_at=config.updated_at
        )
        for config in configs
    ]


@router.get("/config/{config_key}", response_model=ConfigItemResponse)
async def get_config_item(
    config_key: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single config item by key.
    """
    result = await db.execute(
        select(SystemConfig).filter(SystemConfig.config_key == config_key)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg=f"Config key '{config_key}' not found"
        )
    
    return ConfigItemResponse(
        id=config.id,
        config_key=config.config_key,
        config_value=config.config_value,
        version=config.version,
        updated_by=config.updated_by,
        updated_at=config.updated_at
    )


@router.put("/config/{config_key}", response_model=ConfigItemResponse)
async def upsert_config_item(
    config_key: str,
    request: ConfigItemRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upsert a config item. Increments version and sets updated_by to current admin.
    """
    # Validate config value
    validate_config_value(config_key, request.config_value)
    
    # Get existing config
    result = await db.execute(
        select(SystemConfig).filter(SystemConfig.config_key == config_key)
    )
    config = result.scalar_one_or_none()
    
    now = now_utc()
    
    if config:
        # Update existing
        config.config_value = request.config_value
        config.version += 1
        config.updated_by = current_admin.id
        config.updated_at = now
    else:
        # Create new
        config = SystemConfig(
            config_key=config_key,
            config_value=request.config_value,
            version=1,
            updated_by=current_admin.id,
            updated_at=now
        )
        db.add(config)
    
    await db.commit()
    await db.refresh(config)
    
    return ConfigItemResponse(
        id=config.id,
        config_key=config.config_key,
        config_value=config.config_value,
        version=config.version,
        updated_by=config.updated_by,
        updated_at=config.updated_at
    )

