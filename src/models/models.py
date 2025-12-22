from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.declarative import declared_attr
from src.core.db.session import Base

# Base class for all models


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
    return relationship(
        "Organization",
        foreign_keys=[cls.organization_id],
    )




# ==============================
# Concrete Models
# ==============================

class Organization(Base, AuditMixin):
    __tablename__ = "organization"
    type: Mapped[str] = mapped_column(nullable=False) 
    # Users
    users = relationship("User", back_populates="organization")

    # Ships (created by shippers)
  
    ships = relationship("Ship", back_populates="shipper")
    # Ship items 
    ship_items = relationship(
    "ShipItem",
    back_populates="transporter",
    foreign_keys="ShipItem.transporter_id",
)

    # Assets
    trucks = relationship("Truck")
    drivers = relationship("Driver")
    containers = relationship("Container")
    gps_devices = relationship("GPSDevice")
    # Documents & finance
    documents = relationship("Document", back_populates="organization")
    payments = relationship("Payment")
    price_quotes = relationship("PriceQuote")



class User(Base, AuditMixin, TenantMixin):
    __tablename__ = "users"

    user_type: Mapped[str] = mapped_column(nullable=False)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)

    backoffice = relationship("BackOffice", uselist=False, back_populates="user")
    transporter_user = relationship("TransporterUser", uselist=False, back_populates="user")
    shipper_user = relationship("ShipperUser", uselist=False, back_populates="user")
    organization = relationship("Organization", back_populates="users")



class BackOffice(Base):
    __tablename__ = "backoffice"
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)
    user = relationship("User", back_populates="backoffice")


class TransporterUser(Base):
    __tablename__ = "transporter_user"
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)
    user = relationship("User", back_populates="transporter_user")


class ShipperUser(Base):
    __tablename__ = "shipper_user"
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)
    user = relationship("User", back_populates="shipper_user")


class Ship(Base, AuditMixin):
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

    truck_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("truck.id"))
    driver_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("driver.id"))

    truck = relationship("Truck", back_populates="documents")
    driver = relationship("Driver", back_populates="documents")
    organization = relationship("Organization", back_populates="documents")

