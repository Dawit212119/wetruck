from datetime import datetime
from typing import Optional,List,Dict,Any
from sqlalchemy import Column, Integer, DateTime, ForeignKey, func, Enum as SAEnum, String, Boolean, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.declarative import declared_attr
from enum import Enum
from sqlalchemy import TypeDecorator
import json
from sqlalchemy.dialects.postgresql import JSONB



class OrgRole(Enum):
    OWNER="owner"
    ADMIN="admin"
    MEMBER="member"
    VIEWER="viewer"

class OrgUserStatus(Enum):
    ACTIVE="active"
    INACTIVE="inactive"
    SUSPENDED="suspended"
    PENDING="pending"
class UserType(Enum):
    BACKOFFICE="backoffice"
    SHIPPER="shipper" 
    TRANSPORTER="transporter" 

# Base class for all models
class Base(DeclarativeBase):
    pass

# Abstract mixin for audit fields + created_by / updated_by
class AuditMixin:
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # These will typically reference your User table (or a simplified "created_by_user_id")
    # created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("user.id"), nullable=True)
    # updated_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("user.id"), nullable=True)

    # @declared_attr
    # def created_by_user(cls):
    #     return relationship("User", foreign_keys=[cls.created_by])

    # @declared_attr
    # def updated_by_user(cls):
    #     return relationship("User", foreign_keys=[cls.updated_by])


# Mixin for models that belong to an Organization (multi-tenant scope)
class TenantMixin:
    @declared_attr
    def organization_id(cls) -> Mapped[int]:
        return mapped_column(Integer, ForeignKey("organization.id"), nullable=False)

    @declared_attr
    def organization(cls):
        return relationship("Organization", back_populates=cls.__tablename__ + "s")


# ==============================
# Concrete Models
# ==============================

class Organization(Base, AuditMixin):
    __tablename__ = "organization"

    type: Mapped[str] = mapped_column(nullable=False)  # e.g., 'Shipper', 'Transporter'
    name: Mapped[Optional[str]]=mapped_column(String(255))
    company_email:Mapped[Optional[str]]=mapped_column(String(255))
    compnay_phone:Mapped[Optional[str]]=mapped_column(String(50))
    #  this will be refine after in to enum later
    onboarding_status:Mapped[str]=mapped_column(String(50),default="in_progress")
    onboarding_step:Mapped[Optional[str]]=mapped_column(String(50))
    onboarding_completed_at:Mapped[Optional[datetime]]=mapped_column(DateTime(timezone=True))

    org_users: Mapped[list["OrgUser"]]=relationship("OrgUser",back_populates="organization")
   


    # Back-populated relationships will be added in other models


class User(Base, AuditMixin, TenantMixin):
    __tablename__ = "user"

    user_type: Mapped[UserType] = mapped_column(SAEnum(UserType, name="user_type_enum"), nullable=False)  # BackOffice, Transporter, Shipper
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    # Relationships added in specialized user tables below


class BackOffice(Base):
    __tablename__ = "backoffice"
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), primary_key=True)
    user = relationship("User", back_populates="backoffice")

class OnboardingStatus(Enum):
    COMPLETE="complete"
    INPROGRESS="in_progress"


class OnboardingStep(Base,AuditMixin):
    __tablename__="onboarding_steps"

    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    organization_id:Mapped[int]=mapped_column(Integer,ForeignKey("organization.id"),nullable=False)
    organization=relationship("organization",foreign_keys=[organization_id])
    role: Mapped[str]=mapped_column(String(255),nullable=False)   # may be we dont need this field
    current_step: Mapped[Optional[str]]=mapped_column(String(50))
    completed_steps:Mapped[list[str]]=mapped_column(JSONB)
    step_data:Mapped[Optional[Dict[str,Any]]]=mapped_column(JSONB)
    completed_at:Mapped[Optional[datetime]]=mapped_column(DateTime(timezone=True))
    is_complete:Mapped[bool]=mapped_column(Boolean,default=False)
    status:Mapped[OnboardingStatus]=mapped_column(SAEnum(OnboardingStatus,name="onboard_status_enum"))
    organization:Mapped["Organization"]=relationship("Organization",foreign_keys=[organization_id])

class OrgUser(Base,AuditMixin):
    __tablename__="org_user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organization.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)
    organization: Mapped["Organization"] = relationship("Organization", foreign_keys=[organization_id])
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    role: Mapped[Optional[OrgRole]] = mapped_column(SAEnum(OrgRole, name="org_role_enum"), nullable=True)      #  will be enum
    permissions: Mapped[Optional[Dict[str,Any]]] = mapped_column(JSONB)
    status: Mapped[OrgUserStatus] = mapped_column(SAEnum(OrgUserStatus, name="org_user_status_enum"), default="active")  
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
        
    __table_args__ = (
    UniqueConstraint("organization_id", "user_id", name="uq_org_user"),
)


class Ship(Base, AuditMixin, TenantMixin):
    __tablename__ = "ship"

    shipper_id: Mapped[int] = mapped_column(Integer, ForeignKey("organization.id"), nullable=False)
    shipper = relationship("Organization", foreign_keys=[shipper_id], back_populates="ships")

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
    transporter = relationship("Organization", foreign_keys=[transporter_id], back_populates="ship_items")

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
    pass  # owner_id replaced by TenantMixin.organization_id


class GPSDevice(Base, AuditMixin, TenantMixin):
    __tablename__ = "gps_device"
    pass


class PriceQuote(Base, AuditMixin, TenantMixin):
    __tablename__ = "price_quote"
    pass


class Document(Base, AuditMixin, TenantMixin):
    __tablename__ = "document"

    document_type: Mapped[Optional[str]]
    file_path: Mapped[str] = mapped_column(nullable=False)

    # Polymorphic ownership
    truck_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("truck.id"))
    driver_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("driver.id"))
    organization_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("organization.id"))

    truck = relationship("Truck", back_populates="documents")
    driver = relationship("Driver", back_populates="documents")
    organization = relationship("Organization", back_populates="documents")
