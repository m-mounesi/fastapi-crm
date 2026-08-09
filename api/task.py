from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from models.user import UserDB
from schemas.task import TaskCreate, TaskUpdate, TaskResponse
from schemas.schema import SuccessResponse
from security.dependencies import require_permission
from core.dependencies import get_task_service
from services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


# CREATE Task
@router.post("/", response_model=TaskResponse)
def create_task(
    data: TaskCreate,
    db: Session = Depends(get_db),
    service: TaskService = Depends(get_task_service),
    user: UserDB = Depends(require_permission("task.create")),
):
    return service.create_task(db, data, user.user_id)


# GET ALL
@router.get("/", response_model=list[TaskResponse])
def get_tasks(
    project_id: int,
    db: Session = Depends(get_db),
    service: TaskService = Depends(get_task_service),
    user: UserDB = Depends(require_permission("task.read")),
):
    return service.get_tasks(db, project_id, user)


# GET BY ID
@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    service: TaskService = Depends(get_task_service),
    user: UserDB = Depends(require_permission("task.read")),
):
    return service.get_task(db, task_id, user.user_id)


# TOGGLE STATUS
@router.patch("/{task_id}/toggle")
def toggle_task(
    task_id: int,
    db: Session = Depends(get_db),
    service: TaskService = Depends(get_task_service),
    user: UserDB = Depends(require_permission("task.update")),
):
    task = service.toggle_task(db, task_id, user.user_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


# UPDATE
@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    service: TaskService = Depends(get_task_service),
    user: UserDB = Depends(require_permission("task.update")),
):
    task = service.update_task(db, task_id, data, user.user_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


# DELETE
@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    service: TaskService = Depends(get_task_service),
    user: UserDB = Depends(require_permission("task.delete")),
):
    result = service.delete_task(db, task_id, user.user_id)

    if not result:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"message": "Task deleted successfully"}


# Restore
@router.post("/{task_id}/restore")
def restore_task(
    task_id: int,
    db: Session = Depends(get_db),
    service: TaskService = Depends(get_task_service),
    current_user: UserDB = Depends(require_permission("task.restore")),
):
    task = service.restore_task(db, task_id, current_user)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return SuccessResponse(
        message="Task restored successfully", data=f"task : {task.title} "
    )
