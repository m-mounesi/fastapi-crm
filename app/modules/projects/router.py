from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from app.modules.users.models import UserDB
from app.modules.projects.schemas import ProjectCreate, ProjectUpdate, ProjectResponse
from schemas.schema import SuccessResponse
from security.dependencies import require_permission
from app.modules.projects.service import ProjectService
from core.dependencies import get_project_service

router = APIRouter(prefix="/projects", tags=["projects"])


# CREATE
@router.post("/", response_model=ProjectResponse)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    service: ProjectService = Depends(get_project_service),
    user: UserDB = Depends(require_permission("project.create")),
):
    return service.create_project(db, data, user.user_id)


# GET ALL
@router.get("/", response_model=list[ProjectResponse])
def get_projects(
    db: Session = Depends(get_db),
    service: ProjectService = Depends(get_project_service),
    user: UserDB = Depends(require_permission("project.read")),
):
    return service.get_projects(db, user)


# GET BY ID
@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    service: ProjectService = Depends(get_project_service),
    user: UserDB = Depends(require_permission("project.read")),
):
    return service.get_project(db, project_id, user)


# UPDATE
@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    service: ProjectService = Depends(get_project_service),
    user: UserDB = Depends(require_permission("project.update")),
):
    project = service.update_project(db, project_id, data, user.user_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


# DELETE
@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    service: ProjectService = Depends(get_project_service),
    user: UserDB = Depends(require_permission("project.delete")),
):
    result = service.delete_project(db, project_id, user.user_id)

    if not result:
        raise HTTPException(status_code=404, detail="Project not found")

    return SuccessResponse(
        message="Project deleted successfully", data=f"Deleted Project : {project_id} "
    )


# Restore
@router.post("/{project_id}/restore")
def restore_project(
    project_id: int,
    db: Session = Depends(get_db),
    service: ProjectService = Depends(get_project_service),
    current_user: UserDB = Depends(require_permission("project.restore")),
):
    project = service.restore_project(db, project_id, current_user)

    if not project:
        raise HTTPException(status_code=404, detail="project not found")

    return SuccessResponse(
        message="Project restored successfully", data=f"project : {project.title} "
    )
