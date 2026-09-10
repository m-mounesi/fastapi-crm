from core.exceptions import (
    CustomerNotFoundException,
    PermissionDeniedException,
    ProjectNotFoundException,
)
from app.modules.users.models import UserDB
from app.modules.projects.repository import ProjectRepository
from app.modules.projects.models import ProjectDB
from app.modules.users.repository import UserRepository
from app.modules.customers.repository import CustomerRepository


class ProjectService:
    def __init__(
        self,
        repo: ProjectRepository,
        user_repo: UserRepository,
        customer_repo: CustomerRepository,
    ):
        self.repo = repo
        self.user_repo = user_repo
        self.customer_repo = customer_repo

    def create_project(self, db, data, user_id: int):
        if not self.customer_repo.get_by_id(db, data.customer_id):
            raise CustomerNotFoundException("Customer not found")

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
            raise ProjectNotFoundException("project not found by this id")

        if project.created_by != user_id:
            raise PermissionDeniedException("Permission Denied!")

        if data.title is not None:
            project.title = data.title

        if data.status is not None:
            project.status = data.status

        return self.repo.update(db, project)

    def delete_project(self, db, project_id: int, user_id: int):
        project = self.repo.get_by_id(db, project_id)

        if not project:
            raise ProjectNotFoundException("project not found by this id")

        if project.created_by != user_id:
            raise PermissionDeniedException("Permission Denied!")

        self.repo.delete(db, project)
        return True

    # RESTORE
    def restore_project(self, db, project_id, user: UserDB):
        is_admin = any(role.name == "admin" for role in user.roles)

        return self.repo.restore(db, project_id, user.user_id, is_admin)
