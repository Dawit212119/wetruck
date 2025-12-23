from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean, func, Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from enum import Enum


class Base(DeclarativeBase):
    pass


# Enums
class OrganizationType(str, Enum):
    SHIPPER = "Shipper"
    TRANSPORTER = "Transporter"


class UserType(str, Enum):
    BACKOFFICE = "backoffice"
    SHIPPER = "shipper"
    TRANSPORTER = "transporter"


class OrgRole(str, Enum):
    OWNER = "owner"
    MANAGER = "manager"
    DISPATCHER = "dispatcher"
    VIEWER = "viewer"


class OrgUserStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


class OnboardingStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"


class OnboardingStepType(str, Enum):
    PROFILE_BASICS = "profile_basics"
    PAYMENT_PREFERENCES = "payment_preferences"
    ROUTE_PREFERENCES = "route_preferences"
    TUTORIAL = "tutorial"


# Models
class Organization(Base):
    __tablename__ = "organization"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # Shipper|Transporter
    name: Mapped[Optional[str]] = mapped_column(String(255))
    company_email: Mapped[Optional[str]] = mapped_column(String(255))
    company_phone: Mapped[Optional[str]] = mapped_column(String(50))
    onboarding_status: Mapped[str] = mapped_column(String(50), default="in_progress")
    onboarding_step: Mapped[Optional[str]] = mapped_column(String(50))
    onboarding_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="organization")
    org_users: Mapped[List["OrgUser"]] = relationship("OrgUser", back_populates="organization")
    onboarding_steps: Mapped[List["OnboardingStep"]] = relationship("OnboardingStep", back_populates="organization")


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organization.id"), nullable=False)
    user_type: Mapped[str] = mapped_column(String(50), nullable=False)  # backoffice|shipper|transporter
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="users")
    org_users: Mapped[List["OrgUser"]] = relationship(
        "OrgUser", 
        back_populates="user",
        primaryjoin="User.id == OrgUser.user_id"  # Explicitly specify join condition to disambiguate from created_by FK
    )


class OrgUser(Base):
    __tablename__ = "org_user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organization.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # owner|manager|dispatcher|viewer
    permissions: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(50), default="active")  # active|suspended
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("user.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="org_users")
    user: Mapped["User"] = relationship("User", back_populates="org_users", foreign_keys=[user_id])
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])


class OnboardingStep(Base):
    __tablename__ = "onboarding_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organization.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # shipper|transporter
    current_step: Mapped[Optional[str]] = mapped_column(String(50))  # profile_basics|payment_preferences|route_preferences|tutorial
    completed_steps: Mapped[Optional[List[str]]] = mapped_column(JSONB)
    step_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(50), default="in_progress")  # in_progress|complete
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="onboarding_steps")
