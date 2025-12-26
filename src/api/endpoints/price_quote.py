from fastapi import APIRouter, Depends, Query, status
from typing import Optional
from datetime import timedelta
from src.domain.enums.container import ContainerSizeEnum
from src.domain.enums.truck import TruckAxleTypeEnum, TruckTypeEnum
from src.repositories.dependencies import get_tenant_aware_repository
from src.repositories.price_quote_repository import PriceQuoteRepository
from src.core.security.dependencies import transporter_only
from src.core.exceptions import CustomHTTPException
from src.api.schemas.price_quote import (
    PriceQuoteCreate, PriceQuoteUpdate, PriceQuoteResponse, PriceQuotePaginatedResponse
)
from src.api.schemas.generic import GenericCUDResponse
from src.core.api_utils import build_filters
from src.domain.enums.price_quote import PriceQuoteStatusEnum

router = APIRouter(dependencies=[Depends(transporter_only)])
get_quote_repo = get_tenant_aware_repository(PriceQuoteRepository)

@router.get("/", response_model=PriceQuotePaginatedResponse)
def list_quotes(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),

    origin: Optional[str] = None,
    destination: Optional[str] = None,
    status: Optional[PriceQuoteStatusEnum] = None,
    truck_type: Optional[TruckTypeEnum] = None,
    container_size: Optional[ContainerSizeEnum] = None,
    axle_type: Optional[TruckAxleTypeEnum] = None,
    repo: PriceQuoteRepository = Depends(get_quote_repo),
):
    filters = build_filters(
        origin=origin,
        destination=destination,
        status=status.value if status else None,
        truck_type=truck_type.value if truck_type else None,
        container_size=container_size.value if container_size else None,
        axle_type=axle_type.value if axle_type else None,
    )

    items, total, page, per_page, pages = repo.paginated_list(page=page, per_page=per_page, filters=filters)

    return PriceQuotePaginatedResponse(
        status=True,
        message="Price quotes fetched successfully",
        items=items,
        total=total,
        page=page,
        pages=pages,
        per_page=per_page
    )

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_quote(payload: PriceQuoteCreate, repo: PriceQuoteRepository = Depends(get_quote_repo)):
    # ---- BUSINESS RULES ----
    if payload.price_etb <= 0:
        raise CustomHTTPException(status.HTTP_400_BAD_REQUEST, "Quote value must be greater than 0", code="QUOTE_INVALID_PRICE")
    if payload.valid_to - payload.valid_from > timedelta(days=7):
        raise CustomHTTPException(status.HTTP_400_BAD_REQUEST, "Quote validity period must be less than 7 days", code="QUOTE_INVALID_PERIOD")
    if payload.origin == payload.destination:
        raise CustomHTTPException(status.HTTP_400_BAD_REQUEST, "Destination cannot be the same as origin", code="QUOTE_INVALID_ROUTE")
    if payload.gross_weight_max < payload.gross_weight_min:
        raise CustomHTTPException(status.HTTP_400_BAD_REQUEST, "gross_weight_max must be >= gross_weight_min", code="QUOTE_INVALID_WEIGHT")

    quote = repo.create(payload.model_dump())
    return GenericCUDResponse(status=True, success_message="Quote created successfully", result=PriceQuoteResponse.model_validate(quote))

@router.get("/{id}")
def get_quote(id: int, repo: PriceQuoteRepository = Depends(get_quote_repo)):
    quote = repo.get(id)
    if not quote:
        raise CustomHTTPException(status.HTTP_404_NOT_FOUND, "Quote not found", code="QUOTE_NOT_FOUND")
    return GenericCUDResponse(status=True, success_message="Quote retrieved successfully", result=PriceQuoteResponse.model_validate(quote))

@router.patch("/{id}")
def update_quote(
    id: int,
    req: PriceQuoteUpdate,
    repo: PriceQuoteRepository = Depends(get_quote_repo)
):
    # Fetch existing quote
    quote = repo.get(id)
    if not quote:
        raise CustomHTTPException(status.HTTP_404_NOT_FOUND, "Quote not found", code="QUOTE_NOT_FOUND")

    # Block update if already active
    if quote.status == PriceQuoteStatusEnum.ACTIVE:  # enum stored as string
        raise CustomHTTPException(status.HTTP_400_BAD_REQUEST, "Cannot update an active quote", code="QUOTE_ACTIVE")

    # Extract only provided fields
    update_data = req.model_dump(exclude_unset=True)

    # BUSINESS RULES — validate only if field is sent
    if "price_etb" in update_data and update_data["price_etb"] is not None:
        if update_data["price_etb"] <= 0:
            raise CustomHTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Quote value must be greater than 0",
                code="QUOTE_INVALID_PRICE"
            )

    if "valid_from" in update_data and "valid_to" in update_data:
        if update_data["valid_from"] and update_data["valid_to"]:
            delta = update_data["valid_to"] - update_data["valid_from"]
            if delta > timedelta(days=7):
                raise CustomHTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    "Quote validity period must be less than 7 days",
                    code="QUOTE_INVALID_PERIOD"
                )

    if "origin" in update_data and "destination" in update_data:
        if update_data["origin"] and update_data["destination"]:
            if update_data["origin"] == update_data["destination"]:
                raise CustomHTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    "Destination cannot be the same as origin",
                    code="QUOTE_INVALID_ROUTE"
                )

    if "gross_weight_min" in update_data and "gross_weight_max" in update_data:
        if update_data["gross_weight_min"] and update_data["gross_weight_max"]:
            if update_data["gross_weight_max"] < update_data["gross_weight_min"]:
                raise CustomHTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    "gross_weight_max must be >= gross_weight_min",
                    code="QUOTE_INVALID_WEIGHT"
                )

    # Apply update (only provided fields)
    updated_quote = repo.update(id, update_data)

    return GenericCUDResponse(
        status=True,
        success_message="Quote updated successfully",
        result=PriceQuoteResponse.model_validate(updated_quote)
    )

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quote(id: int, repo: PriceQuoteRepository = Depends(get_quote_repo)):
    quote = repo.get(id)
    if not quote:
        raise CustomHTTPException(status.HTTP_404_NOT_FOUND, "Quote not found", code="QUOTE_NOT_FOUND")
    if quote.status == PriceQuoteStatusEnum.ACTIVE:
        raise CustomHTTPException(status.HTTP_400_BAD_REQUEST, "Cannot delete an active quote", code="QUOTE_ACTIVE")
    repo.soft_delete(id)
    return
