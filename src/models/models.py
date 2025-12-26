from datetime import datetime, date
from typing import Optional
from sqlalchemy import Numeric, String
from src.core.db.session import Base
from sqlalchemy import Column, Integer, Boolean, Date, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import Enum as SAEnum

from src.domain.enums.document import DocumentStatusEnum, DocumentTypeEnum
from src.domain.enums.driver import DriverStatusEnum
from src.domain.enums.organization import OrganizationTypeEnum
from src.domain.enums.truck import TruckStatusEnum, TruckTypeEnum,TruckAxleTypeEnum
from src.domain.enums.user import UserStatusEnum, UserTypeEnum
from src.domain.enums.container import ContainerSizeEnum
from src.domain.enums.price_quote import PriceQuoteStatusEnum


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


class Organization(Base, AuditMixin):
    __tablename__ = "organization"

    type: Mapped[OrganizationTypeEnum] = mapped_column(
        SAEnum(OrganizationTypeEnum, native_enum=False, length=50),
        nullable=False
    )
    name: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))


class User(Base, AuditMixin):
    __tablename__ = "user"

    user_type: Mapped[UserTypeEnum] = mapped_column(
        SAEnum(UserTypeEnum, native_enum=False, length=50),
        nullable=False
    )
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[UserStatusEnum] = mapped_column(
        SAEnum(UserStatusEnum, native_enum=False, length=50),
        nullable=False,
        default=UserStatusEnum.ACTIVE,
    )

    organization_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("organization.id"),
        nullable=True,
    )

    organization = relationship("Organization")

    # Relationships
    backoffice = relationship("BackOffice", back_populates="user", uselist=False)
    transporter_user = relationship("TransporterUser", back_populates="user", uselist=False)
    shipper_user = relationship("ShipperUser", back_populates="user", uselist=False)

class BackOffice(Base):
    __tablename__ = "backoffice_user"
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), primary_key=True)
    user = relationship("User", back_populates="backoffice")

class TransporterUser(Base):
    __tablename__ = "transporter_user"
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), primary_key=True)
    user = relationship("User", back_populates="transporter_user")

class ShipperUser(Base):
    __tablename__ = "shipper_user"
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), primary_key=True)
    user = relationship("User", back_populates="shipper_user")

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

    # Enums (assuming you use StrEnum for string values)
    status: Mapped[TruckStatusEnum] = mapped_column(
        SAEnum(TruckStatusEnum, native_enum=False, length=50),
        nullable=False,
        default=TruckStatusEnum.INACTIVE,
    )

    truck_type: Mapped[TruckTypeEnum] = mapped_column(
        SAEnum(TruckTypeEnum, native_enum=False, length=50),
        nullable=False,
    )

    # Unique identifiers – make them explicit strings with appropriate lengths/indexes
    vin: Mapped[str] = mapped_column(
        String(17),  # VIN is always exactly 17 characters
        unique=True,
        nullable=False,  # VIN should never be null for a real truck
        index=True,
    )

    plate_number: Mapped[str] = mapped_column(
        String(20),  # Accommodates formats like "ABC-123" or international plates
        unique=True,
        nullable=False,  # Plate is required for registered trucks
        index=True,
    )

    registration_date: Mapped[date] = mapped_column(Date, nullable=False)

    gov_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    make: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    year: Mapped[Optional[int]] = mapped_column(nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    capacity_quintal: Mapped[int] = mapped_column(nullable=False)

    libre_key: Mapped[Optional[str]] = mapped_column(nullable=True)

    gps_device_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("gps_device.id"))
    gps_device = relationship("GPSDevice", foreign_keys=[gps_device_id], uselist=False)
    documents = relationship("Document", back_populates="truck")


class Driver(Base, AuditMixin, TenantMixin):
    __tablename__ = "driver"
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    phone_number: Mapped[Optional[str]] = mapped_column(String(20),unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    driver_license_number: Mapped[Optional[str]] = mapped_column(String(100),unique=True, nullable=False)
    status: Mapped[DriverStatusEnum] = mapped_column(
        SAEnum(DriverStatusEnum, native_enum=False, length=50),
        nullable=False,
        default=DriverStatusEnum.ACTIVE,
    )
    documents = relationship("Document", back_populates="driver")


class Container(Base, AuditMixin, TenantMixin):
    __tablename__ = "container"
    pass


class GPSDevice(Base, AuditMixin, TenantMixin):
    __tablename__ = "gps_device"
    
    external_device_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    imei_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    device_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    device_model: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    expire_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[Optional[bool]] = mapped_column(Boolean, default=True, nullable=True)


class PriceQuote(Base, AuditMixin, TenantMixin):
    __tablename__ = "price_quote"
    origin: Mapped[str] = mapped_column(String(100), nullable=False)
    destination: Mapped[str] = mapped_column(String(100), nullable=False)
    gross_weight_min: Mapped[int] = mapped_column(Integer, nullable=False)
    gross_weight_max: Mapped[int] = mapped_column(Integer, nullable=False)
    truck_type: Mapped[TruckTypeEnum] = mapped_column(
        SAEnum(TruckTypeEnum, native_enum=False, length=50),
        nullable=False,
    )
    container_size: Mapped[ContainerSizeEnum] = mapped_column(
        SAEnum(ContainerSizeEnum, native_enum=False, length=50),
        nullable=False,
    )
    axle_type: Mapped[TruckAxleTypeEnum] = mapped_column(
        SAEnum(TruckAxleTypeEnum, native_enum=False, length=50),
        nullable=True,
    )
    price_etb: Mapped[float] = mapped_column(Numeric(12,2), nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_to: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[PriceQuoteStatusEnum] = mapped_column(
        SAEnum(PriceQuoteStatusEnum, native_enum=False, length=50),
        nullable=False,
        default=PriceQuoteStatusEnum.DRAFT,
    )

class Document(Base, AuditMixin, TenantMixin):
    __tablename__ = "document"
    # document_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Fixed: now a proper column
    document_type: Mapped[DocumentTypeEnum] = mapped_column(
        SAEnum(DocumentTypeEnum, native_enum=False, length=50),
        nullable=False
    )
    status: Mapped[DocumentStatusEnum] = mapped_column(
        SAEnum(DocumentStatusEnum, native_enum=False, length=50),
        nullable=False,
        default=DocumentStatusEnum.PENDING
    )
    file_path: Mapped[str] = mapped_column(nullable=False)
    # Polymorphic ownership (separate from tenant organization)
    truck_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("truck.id"), nullable=True)
    driver_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("driver.id"), nullable=True)
    direct_organization_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("organization.id"), nullable=True)

    truck = relationship("Truck", back_populates="documents")
    driver = relationship("Driver", back_populates="documents")
    direct_organization = relationship("Organization", foreign_keys=[direct_organization_id])
    # tenant "organization" relationship + organization_id column come from TenantMixin (mandatory)
