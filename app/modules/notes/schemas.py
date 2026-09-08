from pydantic import BaseModel
from typing import Optional


class NoteCreate(BaseModel):
    content: str
    customer_id: Optional[int] = None
    project_id: Optional[int] = None


class NoteUpdate(BaseModel):
    content: Optional[str] = None
    customer_id: Optional[int] = None
    project_id: Optional[int] = None


class NoteResponse(BaseModel):
    id: int
    content: str
    customer_id: Optional[int]
    project_id: Optional[int]
    created_by: int

    class Config:
        from_attributes = True
