# schemas/project.py

from pydantic import BaseModel
from typing import Optional


class ProjectCreate(BaseModel):
    title: str
    customer_id: int


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None


class ProjectResponse(BaseModel):
    id: int
    title: str
    status: str
    customer_id: int

    class Config:
        from_attributes = True
