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
from src.repositories.gps_device_repository import GPSDeviceRepository
from src.api.dependencies.gps_dependencies import get_gps_device_repo

router = APIRouter()

# Get repository with organization_id from current user context
get_gps_device_repository = get_gps_device_repo(organization_id=None)


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_gps_device(
    req: GPSDeviceCreate,
    repo: GPSDeviceRepository = Depends(get_gps_device_repository)
):
    """
    Create a GPS device and optionally bind it to a truck.
    """
    data = req.model_dump(exclude={"truck_id"})
    if req.truck_id:
        data["truck_id"] = req.truck_id
    
    device = repo.create_device_with_truck_binding(data)
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

    items, total, page, per_page, pages = repo.list_paginated(
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
    if not device:
        raise HTTPException(status_code=404, detail="GPS device not found")
    return GPSDeviceResponse.model_validate(device).model_dump()


@router.put("/{id}")
def update_gps_device(
    id: int,
    req: GPSDeviceUpdate,
    repo: GPSDeviceRepository = Depends(get_gps_device_repository)
):
    """
    Update GPS device metadata.
    If truck_id changed, reassign safely.
    """
    update_data = req.model_dump(exclude_unset=True, exclude={"truck_id"})
    if "truck_id" in req.model_dump(exclude_unset=True):
        update_data["truck_id"] = req.truck_id
    
    device = repo.update_device(id, update_data)
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

