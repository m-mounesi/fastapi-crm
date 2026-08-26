from fastapi import Depends

from app.modules.customers.repository import CustomerRepository
from repositories.project_repository import ProjectRepository
from repositories.refresh_token_repository import RefreshTokenRepository
from repositories.task_repository import TaskRepository
from repositories.user_repository import UserRepository
from repositories.rbac_repository import RBACRepository
from repositories.note_repository import NoteRepository
from services.project_service import ProjectService
from services.rbac_service import RBACService
from services.task_service import TaskService
from services.auth_service import AuthService
from app.modules.customers.service import CustomerService
from services.note_service import NoteService


# CUSTOMER
def get_customer_repository():
    return CustomerRepository()


def get_customer_service(repo: CustomerRepository = Depends(get_customer_repository)):
    return CustomerService(repo)


# RBAC


def get_rbac_repository():
    return RBACRepository()


def get_rbac_service(repo: RBACRepository = Depends(get_rbac_repository)):
    return RBACService(repo)

    # AUTH / USER


def get_user_repository():
    return UserRepository()


def get_refresh_token_repository():
    return RefreshTokenRepository()


def get_auth_service(
    repo: UserRepository = Depends(get_user_repository),
    refresh_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
    rbac_service: RBACService = Depends(get_rbac_service),
):
    return AuthService(repo, refresh_repo, rbac_service)

    # PROJECT


def get_project_repository():
    return ProjectRepository()


def get_project_service(
    repo: ProjectRepository = Depends(get_project_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    customer_repo: CustomerRepository = Depends(get_customer_repository),
):
    return ProjectService(
        repo=repo,
        user_repo=user_repo,
        customer_repo=customer_repo,
    )


# TASK


def get_task_repository():
    return TaskRepository()


def get_task_service(
    repo: TaskRepository = Depends(get_task_repository),
    project_service: ProjectService = Depends(get_project_service),
    user_repo: UserRepository = Depends(get_user_repository),
):
    return TaskService(repo, project_service, user_repo)


# NOTE


def get_note_repository():
    return NoteRepository()


def get_note_service(repo: NoteRepository = Depends(get_note_repository)):
    return NoteService(repo)
