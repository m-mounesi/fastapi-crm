from fastapi import HTTPException

from core.exceptions import PermissionDeniedException, TaskNotFoundException
from models.user import UserDB
from repositories.task_repository import TaskRepository
from models.task import TaskDB
from app.modules.projects.service import ProjectService
from repositories.user_repository import UserRepository


class TaskService:
    def __init__(
        self,
        repo: TaskRepository,
        project_service: ProjectService,
        user_repo: UserRepository,
    ):
        self.repo = repo
        self.project_service = project_service
        self.user_repo = user_repo

    def create_task(self, db, data, user_id: int):
        project = self.project_service.repo.get_by_id(db, data.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if data.assigned_to is not None:
            if not self.user_repo.get_by_id(db, data.assigned_to):
                raise HTTPException(status_code=404, detail="Assigned user not found")

        task = TaskDB(
            title=data.title,
            description=data.description,
            project_id=data.project_id,
            assigned_to=data.assigned_to,
            created_by=user_id,
        )

        return self.repo.create(db, task)

    def get_tasks(self, db, project_id: int | None, user: UserDB):
        is_admin = any(role.name == "admin" for role in user.roles)
        return self.repo.get_all(
            db,
            project_id,
            user,
            is_admin,
        )

    def get_task(self, db, task_id: int, user_id: int):
        task: TaskDB = self.repo.get_by_id(db, task_id)

        if not task:
            raise TaskNotFoundException("Task not found by this id")

        if task.created_by != user_id:
            raise PermissionDeniedException("Permission Denied!")

        return task

    def toggle_task(self, db, task_id: int, user_id: int):
        task: TaskDB = self.repo.get_by_id(db, task_id)

        if not task:
            raise TaskNotFoundException("Task not found by this id")

        if task.created_by != user_id:
            raise PermissionDeniedException("Permission Denied!")

        task.completed = not task.completed
        return self.repo.update(db, task)

    def update_task(self, db, task_id: int, data, user_id: int):
        task = self.repo.get_by_id(db, task_id)

        if not task:
            return None

        if task.created_by != user_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to access this task"
            )

        if data.assigned_to is not None:
            if not self.user_repo.get_by_id(db, data.assigned_to):
                raise HTTPException(status_code=404, detail="Assigned user not found")

        if data.title is not None:
            task.title = data.title

        if data.description is not None:
            task.description = data.description

        if data.completed is not None:
            task.completed = data.completed

        if data.assigned_to is not None:
            task.assigned_to = data.assigned_to

        return self.repo.update(db, task)

    def delete_task(self, db, task_id: int, user_id: int):
        task = self.repo.get_by_id(db, task_id)

        if not task:
            return None

        if task.created_by != user_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to access this task"
            )

        self.repo.delete(db, task)
        return True

    # RESTORE
    def restore_task(self, db, task_id, user: UserDB):
        is_admin = any(role.name == "admin" for role in user.roles)

        return self.repo.restore(db, task_id, user.user_id, is_admin)
