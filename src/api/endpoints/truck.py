# api/truck_router.py
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from src.api.schemas.truck import TruckCreate, TruckStatusEnum, TruckTypeEnum, TruckUpdate, TruckRead
from src.repositories.dependencies import get_repository
from src.repositories.truck_repository import TruckRepository
# from dependencies import get_db, get_current_organization_id  # your auth/tenant dependency

router = APIRouter()

get_truck_repo = get_repository(4,TruckRepository)

@router.post("/", response_model=TruckRead, status_code=status.HTTP_201_CREATED)
def create_truck(
    truck_in: TruckCreate,
    repo: TruckRepository = Depends(get_truck_repo)
):
    truck_dict = truck_in.model_dump()
    return repo.create(truck_dict)

@router.get("/{truck_id}", response_model=TruckRead)
def get_truck(
    truck_id: int,
    repo: TruckRepository = Depends(get_truck_repo)
):
    truck = repo.get(truck_id)
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    return truck

@router.patch("/{truck_id}", response_model=TruckRead)
def update_truck(
    truck_id: int,
    truck_in: TruckUpdate,
    repo: TruckRepository = Depends(get_truck_repo)
):
    update_data = truck_in.model_dump(exclude_unset=True)
    truck = repo.update(truck_id, update_data)
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    return truck

@router.delete("/{truck_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_truck(
    truck_id: int,
    repo: TruckRepository = Depends(get_truck_repo)
):
    success = repo.soft_delete(truck_id)
    if not success:
        raise HTTPException(status_code=404, detail="Truck not found or already deleted")
    return None

@router.get("/")
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
    filters = {
        "status": status,
        "truck_type": truck_type,
        "vin": vin,
        "plate_number": plate_number,
        "make": make,
        "model": model,
        "year": year,
        "color": color,
        "capacity_quintal": capacity_quintal,
        "registration_date": registration_date,
        "gov_id": gov_id,
        "gps_device_id": gps_device_id,
    }

    return repo.paginated_list(page=page, per_page=per_page, filters=filters)