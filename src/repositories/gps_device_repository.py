from sqlalchemy import select
from src.models.models import GPSDevice, Truck
from src.repositories.base_repository import BaseRepository


class GPSDeviceRepository(BaseRepository[GPSDevice]):
    model = GPSDevice

    def get_truck_by_gps_device_id(self, id) -> Truck:
        stmt = select(Truck).where(Truck.gps_device_id == id)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._apply_deleted_filter(stmt, [False])
        def action():
            return self.db.scalars(stmt).first()
        
        return self._execute(action)

    def deactivate(self, id: int) -> GPSDevice:
        """
        Deactivate a GPS device:
        - Set status to False
        - Unlink from truck
        - Never hard-delete (soft delete + deactivate)
        """
        def action():
            # Get device (this already applies tenant scope via self.get)
            device = self.get(id=id)
            # Find and unlink truck
            truck = self.get_truck_by_gps_device_id(id=id)
            
            if truck:
                #UNLINK truck
                truck.gps_device = None
            
            # Deactivate device
            device.status = False
        
            self.db.commit()
            self.db.refresh(device)
            return device
        
        return self._execute(action)