from datetime import timedelta, datetime, timezone

import pytest
from unittest.mock import MagicMock
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from jose import jwt as jose_jwt

from security.dependencies import get_current_user, require_permission
from security.jwt import create_access_token, SECRET_KEY, ALGORITHM
from core.exceptions import UnauthorizedException, PermissionDeniedException
from core.database import get_db
from core.dependencies import get_rbac_repository, get_user_repository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _token(sub="testuser", user_id=1, **extra):
    data = {"sub": sub, "user_id": user_id, "type": "access", **extra}
    return create_access_token(data)


def _expired_token(sub="testuser", user_id=1):
    """Encode a token with an already-expired exp claim.

    Cannot use create_access_token because it overwrites the exp claim.
    """
    payload = {
        "sub": sub,
        "user_id": user_id,
        "type": "access",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    return jose_jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ===========================================================================
# get_current_user
# ===========================================================================


class TestGetCurrentUser:
    def test_valid_token_returns_user(self, client, seed_db, create_user):
        user, _ = create_user("depuser", "deppass123")
        token = _token(sub=user.username, user_id=user.user_id)
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.get("/customers/", headers=headers)
        assert resp.status_code in (200, 403)

    def test_invalid_token_raises_unauthorized(self, client, seed_db):
        headers = {"Authorization": "Bearer invalid.token.value"}
        resp = client.get("/customers/", headers=headers)
        assert resp.status_code == 401

    def test_expired_token_raises_unauthorized(self, client, seed_db, create_user):
        user, _ = create_user("expuser", "exppass123")
        token = _expired_token(sub=user.username, user_id=user.user_id)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/customers/", headers=headers)
        assert resp.status_code == 401

    def test_user_not_found_raises_unauthorized(self, client, seed_db):
        token = _token(sub="ghostuser", user_id=9999)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/customers/", headers=headers)
        assert resp.status_code == 401

    def test_missing_sub_claim_raises_unauthorized(self, client, seed_db):
        payload = {
            "user_id": 1,
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
        }
        token = jose_jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/customers/", headers=headers)
        assert resp.status_code == 401

    def test_missing_authorization_header_returns_401(self, client, seed_db):
        resp = client.get("/customers/")
        assert resp.status_code == 401

    def test_malformed_bearer_token_returns_401(self, client, seed_db):
        headers = {"Authorization": "Bearer not-a-jwt"}
        resp = client.get("/customers/", headers=headers)
        assert resp.status_code == 401

    def test_token_with_wrong_secret_returns_401(self, client, seed_db):
        payload = {
            "sub": "testuser",
            "user_id": 1,
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
        }
        token = jose_jwt.encode(
            payload, "wrong-secret-key-12345678901234", algorithm=ALGORITHM
        )
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/customers/", headers=headers)
        assert resp.status_code == 401


# ===========================================================================
# get_current_user — unit tests with mocks
# ===========================================================================


class TestGetCurrentUserUnit:
    def test_decodes_token_and_fetches_user(self, db_session):
        from app.modules.users.repository import UserRepository
        from security.password import hash_password

        repo = UserRepository()
        user_data = {"username": "mockuser", "password": hash_password("mockpass")}
        user = repo.create_user(db_session, user_data)

        token = _token(sub=user.username, user_id=user.user_id)
        mock_repo = MagicMock(spec=UserRepository)
        mock_repo.get_user.return_value = user

        result = get_current_user(token=token, db=db_session, repo=mock_repo)
        mock_repo.get_user.assert_called_once_with(db_session, user.username)
        assert result.user_id == user.user_id

    def test_missing_sub_raises_unauthorized(self, db_session):
        from app.modules.users.repository import UserRepository

        payload = {
            "user_id": 1,
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
        }
        token = jose_jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        mock_repo = MagicMock(spec=UserRepository)

        with pytest.raises(UnauthorizedException, match="missing username"):
            get_current_user(token=token, db=db_session, repo=mock_repo)

    def test_user_not_found_raises_unauthorized(self, db_session):
        from app.modules.users.repository import UserRepository

        token = _token(sub="nonexistent", user_id=999)
        mock_repo = MagicMock(spec=UserRepository)
        mock_repo.get_user.return_value = None

        with pytest.raises(UnauthorizedException, match="User not found"):
            get_current_user(token=token, db=db_session, repo=mock_repo)

    def test_expired_token_raises_unauthorized(self, db_session):
        from app.modules.users.repository import UserRepository

        token = _expired_token(sub="expuser", user_id=1)
        mock_repo = MagicMock(spec=UserRepository)

        with pytest.raises(UnauthorizedException):
            get_current_user(token=token, db=db_session, repo=mock_repo)


# ===========================================================================
# require_permission — integration tests
# ===========================================================================


class TestRequirePermission:
    def _make_permission_app(self, db_session):
        from app.modules.rbac.repository import RBACRepository
        from app.modules.users.repository import UserRepository
        from core.exception_handler import global_exception_handler

        app = FastAPI()
        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_rbac_repository] = lambda: RBACRepository()
        app.dependency_overrides[get_user_repository] = lambda: UserRepository()
        app.add_exception_handler(Exception, global_exception_handler)

        @app.get("/test-perm")
        def test_endpoint(current_user=Depends(require_permission("customer.read"))):
            return {"user_id": current_user.user_id}

        return app

    def test_user_with_permission_succeeds(
        self, db_session, create_user, assign_role, seed_db
    ):
        user, _ = create_user("permuser", "permpass123")
        assign_role(user.user_id, "admin")

        app = self._make_permission_app(db_session)

        with TestClient(app, raise_server_exceptions=False) as c:
            token = _token(sub=user.username, user_id=user.user_id)
            headers = {"Authorization": f"Bearer {token}"}
            resp = c.get("/test-perm", headers=headers)
            assert resp.status_code == 200
            assert resp.json()["user_id"] == user.user_id

    def test_user_without_permission_denied(
        self, db_session, create_user, assign_role, seed_db
    ):
        user, _ = create_user("nopermuser", "nopermpass123")
        assign_role(user.user_id, "viewer")

        app = self._make_permission_app(db_session)

        with TestClient(app, raise_server_exceptions=False) as c:
            token = _token(sub=user.username, user_id=user.user_id)
            headers = {"Authorization": f"Bearer {token}"}
            resp = c.get("/test-perm", headers=headers)
            assert resp.status_code == 403
            assert resp.json()["error_type"] == "PermissionDenied"

    def test_unauthenticated_user_denied(self, db_session, seed_db):
        app = self._make_permission_app(db_session)

        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.get("/test-perm")
            assert resp.status_code == 401


# ===========================================================================
# require_permission — unit tests with mocks
# ===========================================================================


class TestRequirePermissionUnit:
    def test_user_with_permission_returns_user(self, db_session):
        from app.modules.rbac.repository import RBACRepository

        mock_user = MagicMock()
        mock_user.user_id = 42

        mock_repo = MagicMock(spec=RBACRepository)
        mock_repo.get_user_permissions.return_value = [
            "customer.read",
            "customer.create",
        ]

        checker = require_permission("customer.read")
        result = checker(current_user=mock_user, db=db_session, repo=mock_repo)
        assert result.user_id == 42

    def test_user_without_permission_raises_denied(self, db_session):
        from app.modules.rbac.repository import RBACRepository

        mock_user = MagicMock()
        mock_user.user_id = 42

        mock_repo = MagicMock(spec=RBACRepository)
        mock_repo.get_user_permissions.return_value = ["project.read"]

        checker = require_permission("customer.read")
        with pytest.raises(PermissionDeniedException, match="do not have permission"):
            checker(current_user=mock_user, db=db_session, repo=mock_repo)

    def test_empty_permissions_raises_denied(self, db_session):
        from app.modules.rbac.repository import RBACRepository

        mock_user = MagicMock()
        mock_user.user_id = 42

        mock_repo = MagicMock(spec=RBACRepository)
        mock_repo.get_user_permissions.return_value = []

        checker = require_permission("customer.read")
        with pytest.raises(PermissionDeniedException):
            checker(current_user=mock_user, db=db_session, repo=mock_repo)

    def test_nonexistent_permission_raises_denied(self, db_session):
        from app.modules.rbac.repository import RBACRepository

        mock_user = MagicMock()
        mock_user.user_id = 42

        mock_repo = MagicMock(spec=RBACRepository)
        mock_repo.get_user_permissions.return_value = ["customer.read"]

        checker = require_permission("fake.permission")
        with pytest.raises(PermissionDeniedException):
            checker(current_user=mock_user, db=db_session, repo=mock_repo)

    def test_admin_with_all_permissions_succeeds(self, db_session):
        from app.modules.rbac.repository import RBACRepository

        mock_user = MagicMock()
        mock_user.user_id = 1

        all_perms = [
            "customer.create",
            "customer.read",
            "customer.update",
            "customer.delete",
            "customer.restore",
            "project.create",
            "project.read",
            "project.update",
            "project.delete",
            "project.restore",
            "task.create",
            "task.read",
            "task.update",
            "task.delete",
            "task.restore",
            "note.create",
            "note.read",
            "note.update",
            "note.delete",
            "note.restore",
            "user.manage",
        ]
        mock_repo = MagicMock(spec=RBACRepository)
        mock_repo.get_user_permissions.return_value = all_perms

        checker = require_permission("customer.read")
        result = checker(current_user=mock_user, db=db_session, repo=mock_repo)
        assert result.user_id == 1

    def test_permission_string_must_match_exactly(self, db_session):
        from app.modules.rbac.repository import RBACRepository

        mock_user = MagicMock()
        mock_user.user_id = 42

        mock_repo = MagicMock(spec=RBACRepository)
        mock_repo.get_user_permissions.return_value = ["customer.read"]

        checker = require_permission("customer.Read")
        with pytest.raises(PermissionDeniedException):
            checker(current_user=mock_user, db=db_session, repo=mock_repo)
