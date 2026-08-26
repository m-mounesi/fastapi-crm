from datetime import datetime, timezone

from core.exceptions import PermissionDeniedException, TaskNotFoundException
from app.modules.tasks.models import TaskDB
from app.modules.users.models import UserDB


class TaskRepository:
    def create(self, db, task: TaskDB):
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def get_by_id(self, db, task_id: int):
        return (
            db.query(TaskDB)
            .filter(TaskDB.id == task_id, TaskDB.deleted_at.is_(None))
            .first()
        )

    def get_all(
        self,
        db,
        project_id: int | None,
        user: UserDB,
        is_admin: bool,
    ):
        query = db.query(TaskDB).filter(TaskDB.deleted_at.is_(None))

        if not is_admin:
            query = query.filter(TaskDB.created_by == user.user_id)

        if project_id is not None:
            query = query.filter(TaskDB.project_id == project_id)

        return query.all()

    def update(self, db, task: TaskDB):
        db.commit()
        db.refresh(task)
        return task

    def delete(self, db, task: TaskDB):
        task.deleted_at = datetime.now(timezone.utc)
        db.commit()

    def restore(self, db, task_id: int, user_id, is_admin: bool):
        task: TaskDB = db.query(TaskDB).filter(TaskDB.id == task_id).first()

        if not task:
            raise TaskNotFoundException("Task not found")

        if not is_admin and task.created_by != user_id:
            raise PermissionDeniedException("You cannot restore this task.")

        task.deleted_at = None
        db.commit()
        db.refresh(task)

        return task
