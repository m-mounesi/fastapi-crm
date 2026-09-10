from core.dependencies import (
    get_customer_repository,
    get_customer_service,
    get_rbac_repository,
    get_rbac_service,
    get_user_repository,
    get_refresh_token_repository,
    get_auth_service,
    get_project_repository,
    get_project_service,
    get_task_repository,
    get_task_service,
    get_note_repository,
    get_note_service,
)
from app.modules.customers.repository import CustomerRepository
from app.modules.projects.repository import ProjectRepository
from app.modules.auth.repository import RefreshTokenRepository
from app.modules.tasks.repository import TaskRepository
from app.modules.users.repository import UserRepository
from app.modules.rbac.repository import RBACRepository
from app.modules.notes.repository import NoteRepository
from app.modules.customers.service import CustomerService
from app.modules.projects.service import ProjectService
from app.modules.rbac.service import RBACService
from app.modules.tasks.service import TaskService
from app.modules.users.service import AuthService
from app.modules.notes.service import NoteService


# ===========================================================================
# Repository factories
# ===========================================================================


class TestRepositoryFactories:
    def test_get_customer_repository_returns_customer_repository(self):
        repo = get_customer_repository()
        assert isinstance(repo, CustomerRepository)

    def test_get_rbac_repository_returns_rbac_repository(self):
        repo = get_rbac_repository()
        assert isinstance(repo, RBACRepository)

    def test_get_user_repository_returns_user_repository(self):
        repo = get_user_repository()
        assert isinstance(repo, UserRepository)

    def test_get_refresh_token_repository_returns_refresh_token_repository(self):
        repo = get_refresh_token_repository()
        assert isinstance(repo, RefreshTokenRepository)

    def test_get_project_repository_returns_project_repository(self):
        repo = get_project_repository()
        assert isinstance(repo, ProjectRepository)

    def test_get_task_repository_returns_task_repository(self):
        repo = get_task_repository()
        assert isinstance(repo, TaskRepository)

    def test_get_note_repository_returns_note_repository(self):
        repo = get_note_repository()
        assert isinstance(repo, NoteRepository)

    def test_repository_factories_create_new_instances(self):
        repo1 = get_customer_repository()
        repo2 = get_customer_repository()
        assert repo1 is not repo2


# ===========================================================================
# Service factories
# ===========================================================================


class TestServiceFactories:
    def test_get_customer_service_returns_customer_service(self):
        svc = get_customer_service(repo=CustomerRepository())
        assert isinstance(svc, CustomerService)

    def test_get_rbac_service_returns_rbac_service(self):
        svc = get_rbac_service(repo=RBACRepository())
        assert isinstance(svc, RBACService)

    def test_get_project_service_returns_project_service(self):
        svc = get_project_service(
            repo=ProjectRepository(),
            user_repo=UserRepository(),
            customer_repo=CustomerRepository(),
        )
        assert isinstance(svc, ProjectService)

    def test_get_task_service_returns_task_service(self):
        svc = get_task_service(
            repo=TaskRepository(),
            project_service=ProjectService(
                repo=ProjectRepository(),
                user_repo=UserRepository(),
                customer_repo=CustomerRepository(),
            ),
            user_repo=UserRepository(),
        )
        assert isinstance(svc, TaskService)

    def test_get_auth_service_returns_auth_service(self):
        svc = get_auth_service(
            repo=UserRepository(),
            refresh_repo=RefreshTokenRepository(),
            rbac_service=RBACService(repo=RBACRepository()),
        )
        assert isinstance(svc, AuthService)

    def test_get_note_service_returns_note_service(self):
        svc = get_note_service(repo=NoteRepository())
        assert isinstance(svc, NoteService)

    def test_service_factories_create_new_instances(self):
        svc1 = get_customer_service(repo=CustomerRepository())
        svc2 = get_customer_service(repo=CustomerRepository())
        assert svc1 is not svc2


# ===========================================================================
# Dependency injection wiring (via small isolated FastAPI app)
# ===========================================================================


class TestDependencyWiring:
    """Verify that FastAPI's DI resolves dependencies correctly
    through the factory functions in core/dependencies."""

    def test_customer_service_wired_correctly(self):
        from fastapi import FastAPI, Depends
        from fastapi.testclient import TestClient

        app = FastAPI()
        captured = {}

        @app.get("/test")
        def endpoint(svc: CustomerService = Depends(get_customer_service)):
            captured["svc"] = svc
            return {"ok": True}

        with TestClient(app, raise_server_exceptions=True) as c:
            c.get("/test")
            assert isinstance(captured["svc"], CustomerService)

    def test_rbac_service_wired_correctly(self):
        from fastapi import FastAPI, Depends
        from fastapi.testclient import TestClient

        app = FastAPI()
        captured = {}

        @app.get("/test")
        def endpoint(svc: RBACService = Depends(get_rbac_service)):
            captured["svc"] = svc
            return {"ok": True}

        with TestClient(app, raise_server_exceptions=True) as c:
            c.get("/test")
            assert isinstance(captured["svc"], RBACService)

    def test_project_service_wired_correctly(self):
        from fastapi import FastAPI, Depends
        from fastapi.testclient import TestClient

        app = FastAPI()
        captured = {}

        @app.get("/test")
        def endpoint(svc: ProjectService = Depends(get_project_service)):
            captured["svc"] = svc
            return {"ok": True}

        with TestClient(app, raise_server_exceptions=True) as c:
            c.get("/test")
            assert isinstance(captured["svc"], ProjectService)

    def test_task_service_wired_correctly(self):
        from fastapi import FastAPI, Depends
        from fastapi.testclient import TestClient

        app = FastAPI()
        captured = {}

        @app.get("/test")
        def endpoint(svc: TaskService = Depends(get_task_service)):
            captured["svc"] = svc
            return {"ok": True}

        with TestClient(app, raise_server_exceptions=True) as c:
            c.get("/test")
            assert isinstance(captured["svc"], TaskService)

    def test_auth_service_wired_correctly(self):
        from fastapi import FastAPI, Depends
        from fastapi.testclient import TestClient

        app = FastAPI()
        captured = {}

        @app.get("/test")
        def endpoint(svc: AuthService = Depends(get_auth_service)):
            captured["svc"] = svc
            return {"ok": True}

        with TestClient(app, raise_server_exceptions=True) as c:
            c.get("/test")
            assert isinstance(captured["svc"], AuthService)

    def test_note_service_wired_correctly(self):
        from fastapi import FastAPI, Depends
        from fastapi.testclient import TestClient

        app = FastAPI()
        captured = {}

        @app.get("/test")
        def endpoint(svc: NoteService = Depends(get_note_service)):
            captured["svc"] = svc
            return {"ok": True}

        with TestClient(app, raise_server_exceptions=True) as c:
            c.get("/test")
            assert isinstance(captured["svc"], NoteService)
