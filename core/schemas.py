from typing import Optional, Any, Dict, List, TypeVar, Generic
from pydantic import BaseModel


#    GLOBAL SCHEMAS

T = TypeVar("T")  #   use for Generic intput


# Model for Success responses
class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    status_code: int = 200
    message: str = "Operation successful"
    data: Optional[T] = None


# Model For error responses
class ErrorResponse(BaseModel):
    success: bool = False
    status_code: int
    error_type: str
    message: str
    details: Optional[Dict[str, Any]] = None


# Model For PaginatedResponse   ( All tasks )


class PaginatedResponse(SuccessResponse, Generic[T]):
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next_page: bool
    has_previous_page: bool
    data: Optional[List[T]] = None
