from fastapi import HTTPException

from core.exceptions import PermissionDeniedException, ProjectNotFoundException
from models.user import UserDB
from repositories.project_repository import ProjectRepository
from models.project import ProjectDB
from repositories.user_repository import UserRepository
from repositories.customer_repository import CustomerRepository


class ProjectService:
    def __init__(self, repo: ProjectRepository, user_repo: UserRepository):
        self.repo = repo
        self.user_repo = user_repo

    def create_project(self, db, data, user_id: int):
        customer_repo = CustomerRepository()
        if not customer_repo.get_by_id(db, data.customer_id):
            raise HTTPException(status_code=404, detail="Customer not found")

        project = ProjectDB(
            title=data.title, customer_id=data.customer_id, created_by=user_id
        )

        return self.repo.create(db, project)

    def get_projects(self, db, user: UserDB):
        return self.repo.get_all(
            db,
            user_id=user.user_id,
            is_admin=any(role.name == "admin" for role in user.roles),
        )

    def get_project(self, db, project_id: int, current_user: UserDB):
        project: ProjectDB = self.repo.get_by_id(db, project_id)

        if not project:
            raise ProjectNotFoundException("project not found by this id")

        if project.created_by != current_user.user_id:
            raise PermissionDeniedException("Permission Denied!")

        return project

    def update_project(self, db, project_id: int, data, user_id: int):
        project = self.repo.get_by_id(db, project_id)

        if not project:
            return None

        if project.created_by != user_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to access this project"
            )

        if data.title is not None:
            project.title = data.title

        if data.status is not None:
            project.status = data.status

        return self.repo.update(db, project)

    def delete_project(self, db, project_id: int, user_id: int):
        project = self.repo.get_by_id(db, project_id)

        if not project:
            return None

        if project.created_by != user_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to access this project"
            )

        self.repo.delete(db, project)
        return True

    # RESTORE
    def restore_project(self, db, project_id, user: UserDB):
        is_admin = any(role.name == "admin" for role in user.roles)

        return self.repo.restore(db, project_id, user.user_id, is_admin)
