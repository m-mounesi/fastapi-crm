from fastapi import Depends

from app.modules.customers.repository import CustomerRepository
from app.modules.projects.repository import ProjectRepository
from app.modules.auth.repository import RefreshTokenRepository
from app.modules.tasks.repository import TaskRepository
from app.modules.users.repository import UserRepository
from app.modules.rbac.repository import RBACRepository
from app.modules.notes.repository import NoteRepository
from app.modules.projects.service import ProjectService
from app.modules.rbac.service import RBACService
from app.modules.tasks.service import TaskService
from app.modules.users.service import AuthService
from app.modules.customers.service import CustomerService
from app.modules.notes.service import NoteService


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


def get_note_service(
    repo: NoteRepository = Depends(get_note_repository),
    customer_repo: CustomerRepository = Depends(get_customer_repository),
    project_repo: ProjectRepository = Depends(get_project_repository),
):
    return NoteService(repo, customer_repo, project_repo)
