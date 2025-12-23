from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean, func, Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from enum import Enum
from sqlalchemy.ext.declarative import declared_attr

class Base(DeclarativeBase):
    pass

# Abstract mixin for audit fields + created_by / updated_by
class AuditMixin:
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

# Mixin for models that belong to an Organization (multi-tenant scope)
class TenantMixin:
    @declared_attr
    def organization_id(cls) -> Mapped[int]:
        return mapped_column(Integer, ForeignKey("organization.id"), nullable=False)

    @declared_attr
    def organization(cls):
        # Explicitly specify the foreign key to avoid ambiguity when multiple FKs to Organization exist
        return relationship("Organization", foreign_keys=[cls.organization_id])

# Enums
class OrganizationType(str, Enum):
    SHIPPER = "Shipper"
    TRANSPORTER = "Transporter"


class UserType(str, Enum):
    BACKOFFICE = "backoffice"
    SHIPPER = "shipper"
    TRANSPORTER = "transporter"
    ADMIN = "admin"
    CS = "cs"


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
    user_type: Mapped[str] = mapped_column(String(50), nullable=False)  # backoffice|shipper|transporter|admin|cs
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default="active")  # active|suspended
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


class SystemConfig(Base):
    __tablename__ = "system_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    config_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    config_value: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("user.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    updater: Mapped[Optional["User"]] = relationship("User", foreign_keys=[updated_by])


class Ship(Base, AuditMixin, TenantMixin):
    __tablename__ = "ship"
    shipper_id: Mapped[int] = mapped_column(Integer, ForeignKey("organization.id"), nullable=False)
    shipper = relationship("Organization", foreign_keys=[shipper_id])
    ship_items = relationship("ShipItem", back_populates="ship")
    ship_documents = relationship("ShipDocument", back_populates="ship")

class ShipItem(Base, AuditMixin, TenantMixin):
    __tablename__ = "ship_item"
    ship_id: Mapped[int] = mapped_column(Integer, ForeignKey("ship.id"), nullable=False)
    truck_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("truck.id"))
    driver_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("driver.id"))
    container_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("container.id"))
    transporter_id: Mapped[int] = mapped_column(Integer, ForeignKey("organization.id"), nullable=False)
    ship = relationship("Ship", back_populates="ship_items")
    truck = relationship("Truck")
    driver = relationship("Driver")
    container = relationship("Container")
    transporter = relationship("Organization", foreign_keys=[transporter_id])
    ship_item_documents = relationship("ShipItemDocument", back_populates="ship_item")
    location_logs = relationship("LocationLog", back_populates="ship_item")
    payments = relationship("Payment", back_populates="ship_item")

class ShipDocument(Base, AuditMixin):
    __tablename__ = "ship_document"
    ship_id: Mapped[int] = mapped_column(Integer, ForeignKey("ship.id"), nullable=False)
    ship = relationship("Ship", back_populates="ship_documents")

class ShipItemDocument(Base, AuditMixin, TenantMixin):
    __tablename__ = "ship_item_document"
    ship_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("ship_item.id"), nullable=False)
    ship_item = relationship("ShipItem", back_populates="ship_item_documents")


class LocationLog(Base, AuditMixin, TenantMixin):
    __tablename__ = "location_log"
    ship_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("ship_item.id"), nullable=False)
    ship_item = relationship("ShipItem", back_populates="location_logs")

class Payment(Base, AuditMixin, TenantMixin):
    __tablename__ = "payment"
    ship_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("ship_item.id"), nullable=False)
    ship_item = relationship("ShipItem", back_populates="payments")

class Truck(Base, AuditMixin, TenantMixin):
    __tablename__ = "truck"
    gps_device_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("gps_device.id"))
    gps_device = relationship("GPSDevice", uselist=False)
    documents = relationship("Document", back_populates="truck")

class Driver(Base, AuditMixin, TenantMixin):
    __tablename__ = "driver"
    documents = relationship("Document", back_populates="driver")

class Container(Base, AuditMixin, TenantMixin):
    __tablename__ = "container"
    pass

class GPSDevice(Base, AuditMixin, TenantMixin):
    __tablename__ = "gps_device"
    pass

class PriceQuote(Base, AuditMixin, TenantMixin):
    __tablename__ = "price_quote"
    pass

class Document(Base, AuditMixin, TenantMixin):
    __tablename__ = "document"
    document_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Fixed: now a proper column
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    # Polymorphic ownership (separate from tenant organization)
    truck_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("truck.id"), nullable=True)
    driver_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("driver.id"), nullable=True)
    direct_organization_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("organization.id"), nullable=True)

    truck = relationship("Truck", back_populates="documents")
    driver = relationship("Driver", back_populates="documents")
    direct_organization = relationship("Organization", foreign_keys=[direct_organization_id])
    # tenant "organization" relationship + organization_id column come from TenantMixin (mandatory)