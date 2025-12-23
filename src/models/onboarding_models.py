"""
Onboarding models matching the specification exactly.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, Integer, DateTime, ForeignKey, String, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func
from enum import Enum

from src.core.db.session import Base


class AuditMixin:
    """Mixin for audit fields"""
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class Organization(Base, AuditMixin):
    __tablename__ = "organization"

    type: Mapped[str] = mapped_column(String(50), nullable=False)  # Shipper|Transporter
    name: Mapped[Optional[str]] = mapped_column(String(255))
    company_email: Mapped[Optional[str]] = mapped_column(String(255))
    company_phone: Mapped[Optional[str]] = mapped_column(String(50))
    onboarding_status: Mapped[str] = mapped_column(String(50), default="in_progress")  # in_progress|complete
    onboarding_step: Mapped[Optional[str]] = mapped_column(String(50))
    onboarding_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    org_users: Mapped[List["OrgUser"]] = relationship("OrgUser", back_populates="organization")
    onboarding_steps: Mapped[List["OnboardingStep"]] = relationship("OnboardingStep", back_populates="organization")


class User(Base, AuditMixin):
    __tablename__ = "user"

    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organization.id"), nullable=False)
    user_type: Mapped[str] = mapped_column(String(50), nullable=False)  # backoffice|shipper|transporter
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)  # email, unique
    password: Mapped[str] = mapped_column(String(255), nullable=False)  # hashed
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20))

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    org_user_entries: Mapped[List["OrgUser"]] = relationship("OrgUser", back_populates="user")


class OrgUser(Base, AuditMixin):
    __tablename__ = "org_user"

    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organization.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # owner|manager|dispatcher|viewer, etc.
    permissions: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(50), default="active")  # active|suspended
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("user.id"), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="org_users")
    user: Mapped["User"] = relationship("User", back_populates="org_user_entries")
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])


class OnboardingStep(Base, AuditMixin):
    __tablename__ = "onboarding_steps"

    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organization.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # shipper|transporter
    current_step: Mapped[Optional[str]] = mapped_column(String(50))  # profile_basics|payment_preferences|route_preferences|tutorial
    completed_steps: Mapped[Optional[List[str]]] = mapped_column(JSONB)  # jsonb array
    step_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)  # jsonb object; per-step payloads
    status: Mapped[str] = mapped_column(String(50), default="in_progress")  # in_progress|complete
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="onboarding_steps")

