from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from src.api.schemas.generic import GenericCUDResponse, GenericResponse
from src.api.schemas.gps_device import (
    GPSDeviceCreate,
    GPSDeviceUpdate,
    GPSDeviceResponse,
    GPSDevicePaginatedResponse,
)
from src.core.api_utils import build_filters
from src.models.models import Truck, GPSDevice
from src.repositories.gps_device_repository import GPSDeviceRepository
from src.repositories.dependencies import get_tenant_aware_repository
from src.repositories.truck_repository import TruckRepository

router = APIRouter()

# Get repository with organization_id from current user JWT token
get_gps_device_repository = get_tenant_aware_repository(GPSDeviceRepository)
get_truck_repository = get_tenant_aware_repository(TruckRepository)


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_gps_device(
    req: GPSDeviceCreate,
    repo: GPSDeviceRepository = Depends(get_gps_device_repository),
    repo_truck: TruckRepository = Depends(get_truck_repository)
):
    """
    Create a GPS device and bind it to a truck.
    Validates:
    - truck_id is required
    - truck belongs to the same organization
    - truck is not already assigned to another GPS device
    """
    truck: Truck = None if req.truck_id is None else repo_truck.get(id=req.truck_id)
    data = req.model_dump(exclude={"truck_id"})
    device: GPSDevice = repo.create(data)

    if truck:
        truck.gps_device = device
        repo.commit()

    return GenericCUDResponse(
        status=True,
        success_message="GPS device created successfully",
        result=GPSDeviceResponse.model_validate(device).model_dump()
    )


@router.get("/", response_model=GPSDevicePaginatedResponse)
def list_gps_devices(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    external_device_id: Optional[str] = None,
    imei_number: Optional[str] = None,
    device_name: Optional[str] = None,
    device_model: Optional[str] = None,
    status: Optional[bool] = None,
    repo: GPSDeviceRepository = Depends(get_gps_device_repository),
):
    """
    List GPS devices with pagination and filters.
    """
    filters = build_filters(
        external_device_id=external_device_id,
        imei_number=imei_number,
        device_name=device_name,
        device_model=device_model,
        status=status,
    )

    items, total, page, per_page, pages = repo.paginated_list(
        page=page,
        per_page=per_page,
        filters=filters
    )

    return GPSDevicePaginatedResponse(
        status=True,
        message="GPS devices fetched successfully",
        items=[GPSDeviceResponse.model_validate(item).model_dump() for item in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )


@router.get("/{id}", response_model=GPSDeviceResponse)
def get_gps_device(
    id: int,
    repo: GPSDeviceRepository = Depends(get_gps_device_repository)
):
    """
    Get a single GPS device by ID.
    """
    device = repo.get(id)
    # if not device:
    #     raise HTTPException(status_code=404, detail="GPS device not found")
    return GPSDeviceResponse.model_validate(device).model_dump()


@router.put("/{id}")
def update_gps_device(
    id: int,
    req: GPSDeviceUpdate,
    repo: GPSDeviceRepository = Depends(get_gps_device_repository),
    repo_truck = Depends(get_truck_repository)
):
    """
    Update GPS device metadata.
    If truck_id changed, reassign safely.
    """
    device: GPSDevice = repo.get(id = id)
    truck: Truck = None if req.truck_id is None else repo_truck.get(id=req.truck_id)
    update_data = req.model_dump(exclude_unset=True, exclude={"truck_id"})
    device = repo.update(id, update_data)

    linked_truck: Truck = repo.get_truck_by_gps_device_id(id=id)
    if truck:
        truck.gps_device = device
        update_data["truck_id"] = req.truck_id
        if linked_truck != None and linked_truck.id != truck.id:
            linked_truck.gps_device = None
    else:
        #IF truck not set unlink gps-device
        linked_truck.gps_device = None
    
    repo.commit()
    
    return GenericCUDResponse(
        status=True,
        success_message="GPS device updated successfully",
        result=GPSDeviceResponse.model_validate(device).model_dump()
    )


@router.patch("/{id}/deactivate")
def deactivate_gps_device(
    id: int,
    repo: GPSDeviceRepository = Depends(get_gps_device_repository)
):
    """
    Deactivate a GPS device:
    - Set status to False
    - Unlink from truck
    - Never hard-delete (soft delete + deactivate)
    """
    device = repo.deactivate(id)
    return GenericCUDResponse(
        status=True,
        success_message="GPS device deactivated successfully",
        result=GPSDeviceResponse.model_validate(device).model_dump()
    )

