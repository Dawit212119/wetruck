from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from src.domain.enums.truck import  TruckTypeEnum,TruckAxleTypeEnum
from src.domain.enums.container import ContainerSizeEnum
from src.domain.enums.price_quote import PriceQuoteStatusEnum
from src.api.schemas.generic import PaginatedResponse


class PriceQuoteCreate(BaseModel):
    origin: str = Field(..., min_length=2, max_length=100)
    destination: str = Field(..., min_length=2, max_length=100)
    gross_weight_min: int
    gross_weight_max: int
    container_size: ContainerSizeEnum
    truck_type: TruckTypeEnum
    axle_type: Optional[TruckAxleTypeEnum] = None
    price_etb: float
    valid_from: datetime
    valid_to: datetime
    status: PriceQuoteStatusEnum

class PriceQuoteUpdate(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    gross_weight_min: Optional[int] = None
    gross_weight_max: Optional[int] = None
    container_size: Optional[ContainerSizeEnum] = None
    truck_type: Optional[TruckTypeEnum] = None
    axle_type: Optional[TruckAxleTypeEnum] = None
    price_etb: Optional[float] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    status: Optional[PriceQuoteStatusEnum] = None

class PriceQuoteResponse(BaseModel):
    id: int
    origin: str
    destination: str
    gross_weight_min: int
    gross_weight_max: int
    container_size: ContainerSizeEnum
    truck_type: TruckTypeEnum
    axle_type: Optional[TruckAxleTypeEnum] = None
    price_etb: float
    valid_from: datetime
    valid_to: datetime
    status: PriceQuoteStatusEnum
    organization_id: int

    model_config = {
        "from_attributes": True
    }

class PriceQuotePaginatedResponse(PaginatedResponse):
    items: List[PriceQuoteResponse]
