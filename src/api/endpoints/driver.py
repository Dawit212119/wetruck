from fastapi import APIRouter, Depends, Query, status
from src.schemas.driver import DriverCreate, DriverUpdate, DriverResponse,DriverPaginatedResponse
from src.repositories.dependencies import get_tenant_aware_repository
from src.repositories.driver_repository import DriverRepository
from src.core.security.dependencies import transporter_only
from src.core.exceptions import CustomHTTPException
from src.api.schemas.generic import GenericCUDResponse
from src.core.api_utils import build_filters
from typing import Optional

router = APIRouter( dependencies=[Depends(transporter_only)])
get_driver_repo = get_tenant_aware_repository(DriverRepository)


@router.get("/", response_model=DriverPaginatedResponse)
def list_drivers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    phone_number: Optional[str] = None,
    email: Optional[str] = None,
    driver_license_number: Optional[str] = None,
    status: Optional[str] = None,
    repo: DriverRepository = Depends(get_driver_repo),
):
    filters = build_filters(
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        email=email,
        driver_license_number=driver_license_number,
        status=status,
    )

    items, total, page, per_page, pages = repo.paginated_list(
        page=page, per_page=per_page, filters=filters
    )

    return DriverPaginatedResponse(
        status=True,
        message="Drivers fetched successfully",
        items=items,
        total=total,
        page=page,
        pages=pages,
        per_page=per_page
    )

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_driver(
    payload: DriverCreate,
    repo: DriverRepository = Depends(get_driver_repo)
):
    if  repo.is_already_exist(
        license_number=payload.driver_license_number,
        phone_number=payload.phone_number,
        email=payload.email
    ):
        raise CustomHTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Driver already exists",
            code="DRIVER_DUPLICATE"
        )

    driver = repo.create(payload.model_dump())
    return GenericCUDResponse(
        status=True,
        success_message="Driver created successfully",
        result=DriverResponse.model_validate(driver)
    )

@router.get("/{id}")
def get_driver(
    id: int,
    repo: DriverRepository = Depends(get_driver_repo)
):
    driver = repo.get(id)
    if not driver:
        raise CustomHTTPException(
            status.HTTP_404_NOT_FOUND,
            "Driver not found",
            code="DRIVER_NOT_FOUND"
        )

    return GenericCUDResponse(
        status=True,
        success_message="Driver retrieved successfully",
        result=DriverResponse.model_validate(driver)
    )

@router.patch("/{id}")
def update_driver(
    id: int,
    payload: DriverUpdate,
    repo: DriverRepository = Depends(get_driver_repo)
):
    existing = repo.is_already_exist(
        license_number=payload.driver_license_number,
        phone_number=payload.phone_number,
        email=payload.email
    )

    if existing and existing.id != id:
        raise CustomHTTPException(
            status.HTTP_400_BAD_REQUEST,
            "License, phone number, or email already used by another driver",
            code="DRIVER_DUPLICATE"
        )

    driver = repo.update(id, payload.model_dump(exclude_unset=True))
    if not driver:
        raise CustomHTTPException(
            status.HTTP_404_NOT_FOUND,
            "Driver not found",
            code="DRIVER_NOT_FOUND"
        )

    return GenericCUDResponse(
        status=True,
        success_message="Driver updated successfully",
        result=DriverResponse.model_validate(driver)
    )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_driver(
    id: int,
    repo: DriverRepository = Depends(get_driver_repo)
):
    ok =  repo.soft_delete(id)
    if not ok:
        raise CustomHTTPException(
            status.HTTP_404_NOT_FOUND,
            "Driver not found",
            code="DRIVER_NOT_FOUND"
        )

    return  # 204 must not return body
