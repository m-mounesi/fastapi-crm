import pytest
from contextlib import asynccontextmanager
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from core.database import Base, get_db
from core.limiter import limiter
from security.jwt import create_access_token
from seeders.rbac_seed import seed_roles, seed_permissions, assign_admin_permissions

# Import all models so Base.metadata.create_all picks them up

TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@asynccontextmanager
async def noop_lifespan(app):
    yield


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    original_lifespan = app.router.lifespan_context
    original_limiter = app.state.limiter
    app.dependency_overrides[get_db] = override_get_db
    app.router.lifespan_context = noop_lifespan
    app.state.limiter = limiter
    limiter.reset()

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()
    app.router.lifespan_context = original_lifespan
    app.state.limiter = original_limiter


@pytest.fixture(scope="function")
def seed_db(db_session):
    seed_roles(db_session)
    seed_permissions(db_session)
    assign_admin_permissions(db_session)


@pytest.fixture(scope="function")
def create_user(db_session):
    from app.modules.users.repository import UserRepository
    from security.password import hash_password

    repo = UserRepository()

    def _create(username: str, password: str = "testpass123"):
        user_data = {
            "username": username,
            "password": hash_password(password),
        }
        user = repo.create_user(db_session, user_data)
        return user, password

    return _create


@pytest.fixture(scope="function")
def assign_role(db_session):
    from app.modules.rbac.service import RBACService
    from app.modules.rbac.repository import RBACRepository

    service = RBACService(RBACRepository())

    def _assign(user_id: int, role_name: str):
        service.assign_role(db_session, user_id, role_name)

    return _assign


@pytest.fixture(scope="function")
def auth_headers(create_user, assign_role, seed_db):
    user, password = create_user("admin_user", "adminpass123")
    assign_role(user.user_id, "admin")
    token = create_access_token(
        {"sub": user.username, "user_id": user.user_id, "type": "access"}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def viewer_headers(create_user, assign_role, seed_db):
    user, password = create_user("viewer_user", "viewerpass123")
    assign_role(user.user_id, "viewer")
    token = create_access_token(
        {"sub": user.username, "user_id": user.user_id, "type": "access"}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def operator_headers(create_user, assign_role, seed_db):
    user, password = create_user("operator_user", "operatorpass123")
    assign_role(user.user_id, "operator")
    token = create_access_token(
        {"sub": user.username, "user_id": user.user_id, "type": "access"}
    )
    return {"Authorization": f"Bearer {token}"}
