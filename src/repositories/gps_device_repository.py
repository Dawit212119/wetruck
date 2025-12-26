from typing import Dict, Any, Optional, List
import logging
from sqlalchemy import select, update, and_
from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation

from src.models.models import GPSDevice, Truck
from src.repositories.base_repository import BaseRepository
from src.core.exception.database_exceptions import DatabaseException

logger = logging.getLogger(__name__)


class GPSDeviceRepository(BaseRepository[GPSDevice]):
    model = GPSDevice

    def create_device_with_truck_binding(self, data: Dict[str, Any]) -> GPSDevice:
        """
        Create a GPS device and bind it to a truck.
        Validates:
        - external_device_id is globally unique
        - imei_number is globally unique
        - truck_id is required
        - truck belongs to same organization
        - truck is not already bound to another active GPS device
        """
        def action():
            truck_id = data.pop("truck_id", None)
            
            # Validate truck_id is provided
            if truck_id is None:
                raise DatabaseException(
                    "truck_id is required to create a GPS device.",
                    400
                )
            
            # Ensure organization_id is set
            if hasattr(self.model, "organization_id") and "organization_id" not in data:
                if self.organization_id is None:
                    raise DatabaseException(
                        "Organization ID is required to create a GPS device. Please ensure you are authenticated and belong to an organization.",
                        400
                    )
                data["organization_id"] = self.organization_id
            
            # Validate global uniqueness for external_device_id
            external_device_id = data.get("external_device_id")
            if external_device_id:
                existing = self.db.scalars(
                    select(GPSDevice).where(
                        and_(
                            GPSDevice.external_device_id == external_device_id,
                            GPSDevice.deleted.is_(False)
                        )
                    )
                ).first()
                if existing:
                    raise DatabaseException(
                        f"GPS device with external_device_id '{external_device_id}' already exists.",
                        409
                    )
            
            # Validate global uniqueness for imei_number
            imei_number = data.get("imei_number")
            if imei_number:
                existing = self.db.scalars(
                    select(GPSDevice).where(
                        and_(
                            GPSDevice.imei_number == imei_number,
                            GPSDevice.deleted.is_(False)
                        )
                    )
                ).first()
                if existing:
                    raise DatabaseException(
                        f"GPS device with imei_number '{imei_number}' already exists.",
                        409
                    )
            
            # Create the device
            device = self.model(**data)
            self.db.add(device)
            
            try:
                self.db.flush()
            except IntegrityError as e:
                # Handle unique constraint violations with specific error messages
                orig = getattr(e, "orig", None)
                if isinstance(orig, UniqueViolation):
                    constraint_name = getattr(orig.diag, "constraint_name", "") or ""
                    constraint_lower = constraint_name.lower()
                    
                    # Log for debugging
                    logger.info(f"UniqueViolation constraint_name on flush: {constraint_name}, lower: {constraint_lower}")
                    
                    # Check constraint name patterns (index names or constraint names)
                    if "external_device_id" in constraint_lower or "externaldeviceid" in constraint_lower:
                        raise DatabaseException(
                            f"GPS device with external_device_id '{external_device_id}' already exists.",
                            409
                        )
                    elif "imei_number" in constraint_lower or "imeinumber" in constraint_lower or "imei" in constraint_lower:
                        raise DatabaseException(
                            f"GPS device with imei_number '{imei_number}' already exists.",
                            409
                        )
                    else:
                        # Fallback: provide helpful message even if constraint name doesn't match
                        raise DatabaseException(
                            f"A GPS device with the same external_device_id or imei_number already exists.",
                            409
                        )
                
                # Re-raise other IntegrityErrors to be handled by _execute
                raise
            
            # Bind device to truck (truck_id is required, so this always runs)
            self._assign_to_truck_internal(device.id, truck_id)
            
            try:
                self.db.commit()
            except IntegrityError as e:
                # Handle unique constraint violations on commit
                orig = getattr(e, "orig", None)
                if isinstance(orig, UniqueViolation):
                    constraint_name = getattr(orig.diag, "constraint_name", "") or ""
                    constraint_lower = constraint_name.lower()
                    
                    # Log for debugging
                    logger.info(f"UniqueViolation constraint_name on commit: {constraint_name}, lower: {constraint_lower}")
                    
                    if "external_device_id" in constraint_lower or "externaldeviceid" in constraint_lower:
                        raise DatabaseException(
                            f"GPS device with external_device_id '{external_device_id}' already exists.",
                            409
                        )
                    elif "imei_number" in constraint_lower or "imeinumber" in constraint_lower or "imei" in constraint_lower:
                        raise DatabaseException(
                            f"GPS device with imei_number '{imei_number}' already exists.",
                            409
                        )
                    else:
                        # Fallback: provide helpful message even if constraint name doesn't match
                        raise DatabaseException(
                            f"A GPS device with the same external_device_id or imei_number already exists.",
                            409
                        )
                
                # Re-raise other IntegrityErrors to be handled by _execute
                raise
            
            self.db.refresh(device)
            return device
        
        return self._execute(action)

    def _assign_to_truck_internal(self, device_id: int, truck_id: int):
        """
        Internal method to assign device to truck with validation.
        Validates:
        - Truck exists and belongs to same organization
        - Truck is not already bound to another active device
        """
        # Verify truck exists and belongs to same organization
        truck = self.db.scalars(
            select(Truck).where(
                and_(
                    Truck.id == truck_id,
                    Truck.organization_id == self.organization_id,
                    Truck.deleted.is_(False)
                )
            )
        ).first()
        
        if not truck:
            raise DatabaseException(
                "Truck not found or does not belong to your organization.",
                404
            )
        
        # Check if truck is already bound to another active device
        if truck.gps_device_id and truck.gps_device_id != device_id:
            existing_device = self.db.scalars(
                select(GPSDevice).where(
                    and_(
                        GPSDevice.id == truck.gps_device_id,
                        GPSDevice.organization_id == self.organization_id,
                        GPSDevice.deleted.is_(False),
                        GPSDevice.status.is_(True)
                    )
                )
            ).first()
            
            if existing_device:
                raise DatabaseException(
                    "Truck is already bound to another active GPS device.",
                    409
                )
        
        # Unlink any existing device from this truck (if different)
        if truck.gps_device_id and truck.gps_device_id != device_id:
            self.db.execute(
                update(Truck)
                .where(Truck.id == truck_id)
                .values(gps_device_id=None)
            )
        
        # Link the new device
        self.db.execute(
            update(Truck)
            .where(Truck.id == truck_id)
            .values(gps_device_id=device_id)
        )

    def assign_to_truck(self, device_id: int, truck_id: int) -> GPSDevice:
        """
        Assign a GPS device to a truck.
        """
        def action():
            # Verify device exists and belongs to organization
            device = self.get(device_id)
            if not device:
                raise DatabaseException("GPS device not found.", 404)
            
            self._assign_to_truck_internal(device_id, truck_id)
            
            self.db.commit()
            self.db.refresh(device)
            return device
        
        return self._execute(action)

    def deactivate(self, device_id: int) -> GPSDevice:
        """
        Deactivate a GPS device:
        - Set status to False
        - Unlink from truck
        - Never hard-delete (soft delete + deactivate)
        """
        def action():
            # Get device (this already applies tenant scope via self.get)
            device = self.get(device_id)
            if not device:
                raise DatabaseException("GPS device not found.", 404)
            
            # Find and unlink truck
            truck = self.db.scalars(
                select(Truck).where(
                    and_(
                        Truck.gps_device_id == device_id,
                        Truck.organization_id == self.organization_id,
                        Truck.deleted.is_(False)
                    )
                )
            ).first()
            
            if truck:
                self.db.execute(
                    update(Truck)
                    .where(Truck.id == truck.id)
                    .values(gps_device_id=None)
                )
            
            # Deactivate device
            device.status = False
            self.db.commit()
            self.db.refresh(device)
            return device
        
        return self._execute(action)

    def update_device(self, id: int, data: Dict[str, Any]) -> GPSDevice:
        """
        Update device metadata.
        If truck_id changed, reassign safely.
        """
        def action():
            truck_id = data.pop("truck_id", None)
            
            # Update device fields
            device = self.update(id, data)
            if not device:
                raise DatabaseException("GPS device not found.", 404)
            
            # Handle truck reassignment if provided
            if truck_id is not None:
                if truck_id == 0:  # Unlink
                    # Find and unlink current truck
                    truck = self.db.scalars(
                        select(Truck).where(
                            and_(
                                Truck.gps_device_id == id,
                                Truck.organization_id == self.organization_id,
                                Truck.deleted.is_(False)
                            )
                        )
                    ).first()
                    if truck:
                        self.db.execute(
                            update(Truck)
                            .where(Truck.id == truck.id)
                            .values(gps_device_id=None)
                        )
                else:
                    # Assign to new truck
                    self._assign_to_truck_internal(id, truck_id)
            
            self.db.commit()
            self.db.refresh(device)
            return device
        
        return self._execute(action)

    def list_paginated(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> tuple[List[GPSDevice], int, int, int, int]:
        """
        Paginated listing with filters.
        Returns: (items, total, page, per_page, pages)
        """
        return self.paginated_list(page=page, per_page=per_page, filters=filters)
