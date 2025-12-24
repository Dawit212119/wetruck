from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List, Optional

T = TypeVar('T')


# For paginated result
class GenericResponse(Generic[T], BaseModel):
    items: List[T]
    total: int
    page: int
    per_page: int
    pages: int

class GenericCUDResponse(Generic[T], BaseModel):
    status: bool = Field(default=True)
    error_message: Optional[str] = None
    success_message: Optional[str] = None
    result: Optional[T] = None
