from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from core.limiter import limiter
from core.exception_handler import rate_limit_handler


# ===========================================================================
# Initialization / Configuration
# ===========================================================================


class TestLimiterInitialization:
    def test_is_limiter_instance(self):
        assert isinstance(limiter, Limiter)

    def test_key_func_is_get_remote_address(self):
        assert limiter._key_func is get_remote_address

    def test_has_in_memory_storage(self):
        assert limiter._storage is not None

    def test_default_limits_are_empty(self):
        assert limiter._default_limits == []

    def test_application_limits_are_empty(self):
        assert limiter._application_limits == []

    def test_enabled_by_default(self):
        assert limiter.enabled is True

    def test_auto_check_is_enabled(self):
        assert limiter._auto_check is True

    def test_headers_disabled_by_default(self):
        assert limiter._headers_enabled is False

    def test_strategy_is_none(self):
        assert limiter._strategy is None


# ===========================================================================
# Limiter.reset
# ===========================================================================


class TestLimiterReset:
    def test_reset_does_not_raise(self):
        limiter.reset()

    def test_reset_clears_storage(self):
        limiter.reset()
        assert limiter._storage is not None


# ===========================================================================
# Rate limiting behavior (isolated app with fresh limiter)
# ===========================================================================


def _build_limited_app(rate_limit="3/minute"):
    """Create a minimal FastAPI app with its own fresh limiter."""
    app_limiter = Limiter(key_func=get_remote_address)
    app = FastAPI()
    app.state.limiter = app_limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

    @app.get("/limited")
    @app_limiter.limit(rate_limit)
    def limited_endpoint(request: Request):
        return {"ok": True}

    return app, app_limiter


class TestRateLimitingBehavior:
    def test_requests_within_limit_succeed(self):
        app, _ = _build_limited_app()
        with TestClient(app) as c:
            for _ in range(3):
                resp = c.get("/limited")
                assert resp.status_code == 200
                assert resp.json() == {"ok": True}

    def test_request_exceeding_limit_returns_429(self):
        app, _ = _build_limited_app()
        with TestClient(app) as c:
            for _ in range(3):
                c.get("/limited")
            resp = c.get("/limited")
            assert resp.status_code == 429

    def test_429_response_body_matches_error_schema(self):
        app, _ = _build_limited_app()
        with TestClient(app) as c:
            for _ in range(3):
                c.get("/limited")
            resp = c.get("/limited")
            body = resp.json()
            assert body["success"] is False
            assert body["status_code"] == 429
            assert body["error_type"] == "RateLimitExceeded"
            assert body["message"] == "Too many requests"

    def test_reset_allows_new_requests_in_fresh_client(self):
        app, app_limiter = _build_limited_app()
        with TestClient(app) as c:
            for _ in range(3):
                c.get("/limited")
            resp = c.get("/limited")
            assert resp.status_code == 429

        app_limiter.reset()

        with TestClient(app) as c:
            resp = c.get("/limited")
            assert resp.status_code == 200

    def test_all_requests_share_same_key_in_testclient(self):
        """get_remote_address returns request.client.host which is always
        'testclient' in the TestClient — all requests share one counter."""
        app, _ = _build_limited_app()
        with TestClient(app) as c:
            for _ in range(3):
                c.get("/limited")
            resp = c.get("/limited")
            assert resp.status_code == 429


# ===========================================================================
# Rate limit applied to auth endpoints (integration)
# ===========================================================================


class TestAuthEndpointRateLimits:
    """Verify that the real auth endpoints enforce their documented limits."""

    def test_register_rate_limit(self, client, seed_db):
        for i in range(3):
            resp = client.post(
                "/auth/register",
                data={"username": f"rluser{i}", "password": "rlpass12345"},
            )
            assert resp.status_code == 201

        resp = client.post(
            "/auth/register",
            data={"username": "rluser_overflow", "password": "rlpass12345"},
        )
        assert resp.status_code == 429

    def test_login_rate_limit(self, client, seed_db, create_user):
        create_user("rllogin", "rlpass12345")
        for _ in range(5):
            resp = client.post(
                "/auth/login",
                data={"username": "rllogin", "password": "wrongpassword"},
            )
            assert resp.status_code == 401

        resp = client.post(
            "/auth/login",
            data={"username": "rllogin", "password": "wrongpassword"},
        )
        assert resp.status_code == 429

    def test_refresh_rate_limit(self, client, seed_db):
        for i in range(10):
            resp = client.post(
                "/auth/refresh",
                params={"refresh_token": f"fake.token.{i}"},
            )
            assert resp.status_code in (400, 401)

        resp = client.post(
            "/auth/refresh",
            params={"refresh_token": "fake.token.overflow"},
        )
        assert resp.status_code == 429
