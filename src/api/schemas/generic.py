from pydantic import BaseModel, ConfigDict, Field
from typing import Generic, TypeVar, List, Optional

T = TypeVar('T')


# For paginated result
class GenericResponse(Generic[T], BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    items: List[T]
    total: int
    page: int
    per_page: int
    pages: int

class GenericCUDResponse(Generic[T], BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: bool = Field(default=True)
    error_message: Optional[str] = None
    success_message: Optional[str] = None
    result: Optional[T] = None


class PaginatedResponse(BaseModel):
    status: bool = True
    message: Optional[str] = None
    total: int
    page: int
    per_page: int
    pages: int