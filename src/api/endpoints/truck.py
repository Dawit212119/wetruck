# api/truck_router.py
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional
# from sqlalchemy.orm import Session
from src.api.schemas.generic import GenericCUDResponse, GenericResponse
from src.api.schemas.truck import TruckCreate, TruckPaginatedResponse, TruckStatusEnum, TruckTypeEnum, TruckUpdate, TruckRead
# from src.models.models import Truck
from src.core.api_utils import build_filters
from src.repositories.dependencies import get_repository
from src.repositories.truck_repository import TruckRepository
# from dependencies import get_db, get_current_organization_id  # your auth/tenant dependency

router = APIRouter()

get_truck_repo = get_repository(4,TruckRepository)

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_truck(
    req: TruckCreate,
    repo: TruckRepository = Depends(get_truck_repo)
):
    return GenericCUDResponse(
        status=True,
        success_message="Truck created successfully",
        result=TruckRead.model_validate(repo.create(req.model_dump())).model_dump()
    )

@router.get("/{id}", response_model=TruckRead)
def get_truck(
    id: int,
    repo: TruckRepository = Depends(get_truck_repo)
):
    truck = repo.get(id)
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    return truck

@router.patch("/{id}")
def update(
    id: int,
    req: TruckUpdate,
    repo: TruckRepository = Depends(get_truck_repo)
):
    update_data = req.model_dump(exclude_unset=True)
    return GenericCUDResponse(
        status=True,
        success_message="Updated successfully",
        result=TruckRead.model_validate(repo.update(id, update_data))
    )

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_truck(
    id: int,
    repo: TruckRepository = Depends(get_truck_repo)
):
    success = repo.soft_delete(id)
    if not success:
        raise HTTPException(status_code=404, detail="Truck not found or already deleted")
    return None

@router.get("/", response_model=TruckPaginatedResponse)
def list_trucks(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    # Filters - all optional
    status: Optional[TruckStatusEnum] = None,
    truck_type: Optional[TruckTypeEnum] = None,
    vin: Optional[str] = None,
    plate_number: Optional[str] = None,
    make: Optional[str] = None,
    model: Optional[str] = None,
    year: Optional[int] = None,
    color: Optional[str] = None,
    capacity_quintal: Optional[int] = None,
    registration_date: Optional[date] = None,
    gov_id: Optional[str] = None,
    gps_device_id: Optional[int] = None,
    repo: TruckRepository = Depends(get_truck_repo),
):
    filters = build_filters(
        status=status,
        truck_type=truck_type,
        vin=vin,
        plate_number=plate_number,
        make=make,
        model=model,
        year=year,
        color=color,
        capacity_quintal=capacity_quintal,
        registration_date=registration_date,
        gov_id=gov_id,
        gps_device_id=gps_device_id,
    )

    items, total, page, per_page, pages = repo.paginated_list(page=page, per_page=per_page, filters=filters)

    return TruckPaginatedResponse(
        status=True,
        message="Trucks fetched successfully",
        items=items,
        total=total,
        page=page,
        pages=pages,
        per_page=per_page
    )