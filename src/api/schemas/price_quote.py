from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from src.domain.enums.truck import TruckTypeEnum, TruckAxleTypeEnum
from src.domain.enums.container import ContainerSizeEnum
from src.domain.enums.price_quote import PriceQuoteStatusEnum
from src.domain.enums.location import LocationEnum
from src.api.schemas.generic import PaginatedResponse


class PriceQuoteCreate(BaseModel):
    origin: LocationEnum
    destination: LocationEnum
    gross_weight_min: int
    gross_weight_max: int
    truck_type: TruckTypeEnum
    container_size: ContainerSizeEnum
    axle_type: Optional[TruckAxleTypeEnum] = None
    amount: float
    currency: Optional[str] = Field(None, max_length= 3)


class PriceQuoteUpdate(BaseModel):
    origin: Optional[LocationEnum] = None
    destination: Optional[LocationEnum] = None
    gross_weight_min: Optional[int] = None
    gross_weight_max: Optional[int] = None
    truck_type: Optional[TruckTypeEnum] = None
    container_size: Optional[ContainerSizeEnum] = None
    axle_type: Optional[TruckAxleTypeEnum] = None
    amount: Optional[float] = None
    currency: Optional[str] = Field(None, max_length=3)
    status: Optional[PriceQuoteStatusEnum] = None


class PriceQuoteResponse(BaseModel):
    id: int
    origin: LocationEnum
    destination: LocationEnum
    gross_weight_min: int
    gross_weight_max: int
    truck_type: TruckTypeEnum
    container_size: ContainerSizeEnum
    axle_type: Optional[TruckAxleTypeEnum] = None
    amount: float
    currency: str
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    status: PriceQuoteStatusEnum
    organization_id: int

    model_config = {
        "from_attributes": True
    }


class PriceQuotePaginatedResponse(PaginatedResponse):
    items: List[PriceQuoteResponse]
