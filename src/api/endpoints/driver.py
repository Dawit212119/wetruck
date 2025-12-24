from fastapi import APIRouter, Depends, Query, status
from src.schemas.driver import DriverCreate, DriverUpdate, DriverResponse
from src.schemas.onboarding import MessageResponse
from src.repositories.dependencies import get_repository
from src.repositories.driver_repository import DriverRepository
from src.core.security.dependencies import transporter_only
from src.core.exceptions import CustomHTTPException

router = APIRouter(prefix="/drivers", tags=["drivers"], dependencies=[Depends(transporter_only)])
get_driver_repo = get_repository(DriverRepository)


@router.get("/", response_model=MessageResponse)
async def list_drivers(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max number of items to return"),
    repo: DriverRepository = Depends(get_driver_repo)
):
    drivers = await repo.list(skip=skip, limit=limit)
    serialized = [DriverResponse.model_validate(driver) for driver in drivers]

    return MessageResponse(
        code=status.HTTP_200_OK,
        msg="Drivers retrieved successfully",
        data={"drivers": serialized, "skip": skip, "limit": limit, "count": len(serialized)}
    )


@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_driver(
    payload: DriverCreate,
    repo: DriverRepository = Depends(get_driver_repo)
):
    if await repo.is_already_exist(
        license_number=payload.driver_license_number,
        phone_number=payload.phone_number,
        email=payload.email
    ):
        raise CustomHTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Driver already exists",
            code="DRIVER_DUPLICATE"
        )

    driver = await repo.create(payload.model_dump())
    serialized = DriverResponse.model_validate(driver)

    return MessageResponse(
        code=status.HTTP_201_CREATED,
        msg="Driver created successfully",
        data={"driver": serialized}
    )


@router.get("/{id}", response_model=MessageResponse)
async def get_driver(
    id: int,
    repo: DriverRepository = Depends(get_driver_repo)
):
    driver = await repo.get(id)
    if not driver:
        raise CustomHTTPException(
            status.HTTP_404_NOT_FOUND,
            "Driver not found",
            code="DRIVER_NOT_FOUND"
        )

    serialized = DriverResponse.model_validate(driver)

    return MessageResponse(
        code=status.HTTP_200_OK,
        msg="Driver retrieved successfully",
        data={"driver": serialized}
    )


@router.patch("/{id}", response_model=MessageResponse)
async def update_driver(
    id: int,
    payload: DriverUpdate,
    repo: DriverRepository = Depends(get_driver_repo)
):
    existing = await repo.is_already_exist(
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

    driver = await repo.update(id, payload.model_dump(exclude_unset=True))
    if not driver:
        raise CustomHTTPException(
            status.HTTP_404_NOT_FOUND,
            "Driver not found",
            code="DRIVER_NOT_FOUND"
        )

    serialized = DriverResponse.model_validate(driver)

    return MessageResponse(
        code=status.HTTP_200_OK,
        msg="Driver updated successfully",
        data={"driver": serialized}
    )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_driver(
    id: int,
    repo: DriverRepository = Depends(get_driver_repo)
):
    ok = await repo.soft_delete(id)
    if not ok:
        raise CustomHTTPException(
            status.HTTP_404_NOT_FOUND,
            "Driver not found",
            code="DRIVER_NOT_FOUND"
        )

    return  # 204 must not return body
