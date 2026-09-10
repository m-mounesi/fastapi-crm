import json
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError, BaseModel

from core.exception_handler import global_exception_handler, rate_limit_handler
from core.exceptions import (
    CustomerNotFoundException,
    InvalidTokenException,
    NoteNotFoundException,
    PermissionDeniedException,
    PermissionNotFoundException,
    ProjectNotFoundException,
    RoleNotFoundException,
    TaskNotFoundException,
    UnauthorizedException,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_request():
    return MagicMock()


def _parse_response(response):
    """Extract status_code and parsed JSON body from a JSONResponse."""
    return response.status_code, json.loads(response.body)


# ===========================================================================
# global_exception_handler — AppException subclasses
# ===========================================================================


class TestAppExceptionSubclasses:
    @pytest.mark.parametrize(
        "exc_cls, status_code, error_type, message",
        [
            (RoleNotFoundException, 404, "RoleNotFound", "Role not found"),
            (
                PermissionNotFoundException,
                404,
                "PermissionNotFound",
                "Permission not found",
            ),
            (CustomerNotFoundException, 404, "CustomerNotFound", "Customer not found"),
            (ProjectNotFoundException, 404, "ProjectNotFound", "Project not found"),
            (TaskNotFoundException, 404, "TaskNotFound", "Task not found"),
            (NoteNotFoundException, 404, "NoteNotFound", "Note not found"),
        ],
    )
    @pytest.mark.asyncio
    async def test_not_found_exceptions(
        self, exc_cls, status_code, error_type, message
    ):
        resp = await global_exception_handler(_mock_request(), exc_cls("unused"))
        code, body = _parse_response(resp)
        assert code == status_code
        assert body["success"] is False
        assert body["status_code"] == status_code
        assert body["error_type"] == error_type
        assert body["message"] == message
        assert body["details"] is None

    @pytest.mark.asyncio
    async def test_unauthorized_uses_exception_message(self):
        resp = await global_exception_handler(
            _mock_request(), UnauthorizedException("Token expired")
        )
        code, body = _parse_response(resp)
        assert code == 401
        assert body["error_type"] == "Unauthorized"
        assert body["message"] == "Token expired"

    @pytest.mark.asyncio
    async def test_invalid_token_uses_exception_message(self):
        resp = await global_exception_handler(
            _mock_request(), InvalidTokenException("Bad signature")
        )
        code, body = _parse_response(resp)
        assert code == 401
        assert body["error_type"] == "InvalidToken"
        assert body["message"] == "Bad signature"

    @pytest.mark.asyncio
    async def test_permission_denied_uses_exception_message(self):
        resp = await global_exception_handler(
            _mock_request(), PermissionDeniedException("No access")
        )
        code, body = _parse_response(resp)
        assert code == 403
        assert body["error_type"] == "PermissionDenied"
        assert body["message"] == "No access"


# ===========================================================================
# global_exception_handler — HTTPException
# ===========================================================================


class TestHTTPException:
    @pytest.mark.asyncio
    async def test_404(self):
        resp = await global_exception_handler(
            _mock_request(), HTTPException(status_code=404, detail="Not found")
        )
        code, body = _parse_response(resp)
        assert code == 404
        assert body["error_type"] == "HTTPException"
        assert body["message"] == "Not found"
        assert body["details"] is None

    @pytest.mark.asyncio
    async def test_401(self):
        resp = await global_exception_handler(
            _mock_request(), HTTPException(status_code=401, detail="Unauthorized")
        )
        code, body = _parse_response(resp)
        assert code == 401
        assert body["message"] == "Unauthorized"

    @pytest.mark.asyncio
    async def test_500(self):
        resp = await global_exception_handler(
            _mock_request(), HTTPException(status_code=500, detail="Server error")
        )
        code, body = _parse_response(resp)
        assert code == 500
        assert body["message"] == "Server error"


# ===========================================================================
# global_exception_handler — RequestValidationError
# ===========================================================================


class TestRequestValidationError:
    @pytest.mark.asyncio
    async def test_single_field_error(self):
        errors = [{"loc": ("query", "name"), "msg": "Field required"}]
        exc = RequestValidationError(errors)
        resp = await global_exception_handler(_mock_request(), exc)
        code, body = _parse_response(resp)
        assert code == 422
        assert body["success"] is False
        assert body["status_code"] == 422
        assert body["error_type"] == "RequestValidationError"
        assert body["message"] == "Request validation failed"
        assert body["details"]["query.name"] == "Field required"

    @pytest.mark.asyncio
    async def test_nested_field_error(self):
        errors = [{"loc": ("body", "user", "email"), "msg": "Invalid email"}]
        exc = RequestValidationError(errors)
        resp = await global_exception_handler(_mock_request(), exc)
        code, body = _parse_response(resp)
        assert code == 422
        assert "body.user.email" in body["details"]

    @pytest.mark.asyncio
    async def test_multiple_errors(self):
        errors = [
            {"loc": ("query", "a"), "msg": "Required"},
            {"loc": ("query", "b"), "msg": "Must be int"},
        ]
        exc = RequestValidationError(errors)
        resp = await global_exception_handler(_mock_request(), exc)
        code, body = _parse_response(resp)
        assert code == 422
        assert len(body["details"]) == 2


# ===========================================================================
# global_exception_handler — Pydantic ValidationError
# ===========================================================================


class TestValidationError:
    @pytest.mark.asyncio
    async def test_validation_error(self):
        class Dummy(BaseModel):
            name: str
            age: int

        try:
            Dummy(name=123, age="not-a-number")
        except ValidationError as exc:
            resp = await global_exception_handler(_mock_request(), exc)
            code, body = _parse_response(resp)
            assert code == 422
            assert body["error_type"] == "ValidationError"
            assert body["message"] == "Validation failed"
            assert body["details"] is not None
            assert len(body["details"]) > 0


# ===========================================================================
# global_exception_handler — unknown / fallback
# ===========================================================================


class TestUnknownException:
    @pytest.mark.asyncio
    async def test_generic_exception_returns_500(self):
        resp = await global_exception_handler(
            _mock_request(), ValueError("something broke")
        )
        code, body = _parse_response(resp)
        assert code == 500
        assert body["success"] is False
        assert body["status_code"] == 500
        assert body["error_type"] == "InternalServerError"
        assert body["message"] == "An unexpected error occurred"
        assert body["details"] is None

    @pytest.mark.asyncio
    async def test_runtime_error_returns_500(self):
        resp = await global_exception_handler(_mock_request(), RuntimeError("boom"))
        code, body = _parse_response(resp)
        assert code == 500
        assert body["error_type"] == "InternalServerError"


# ===========================================================================
# global_exception_handler — ErrorResponse schema compliance
# ===========================================================================


class TestErrorResponseSchemaCompliance:
    @pytest.mark.asyncio
    async def test_always_has_success_false(self):
        resp = await global_exception_handler(
            _mock_request(), UnauthorizedException("no")
        )
        _, body = _parse_response(resp)
        assert body["success"] is False

    @pytest.mark.asyncio
    async def test_always_has_required_fields(self):
        resp = await global_exception_handler(
            _mock_request(), CustomerNotFoundException("not found")
        )
        _, body = _parse_response(resp)
        assert "success" in body
        assert "status_code" in body
        assert "error_type" in body
        assert "message" in body
        assert "details" in body

    @pytest.mark.asyncio
    async def test_details_is_none_for_simple_exceptions(self):
        resp = await global_exception_handler(
            _mock_request(), PermissionDeniedException("denied")
        )
        _, body = _parse_response(resp)
        assert body["details"] is None


# ===========================================================================
# rate_limit_handler
# ===========================================================================


class TestRateLimitHandler:
    @pytest.mark.asyncio
    async def test_returns_429(self):
        resp = await rate_limit_handler(_mock_request(), Exception())
        code, body = _parse_response(resp)
        assert code == 429

    @pytest.mark.asyncio
    async def test_response_body(self):
        resp = await rate_limit_handler(_mock_request(), Exception())
        _, body = _parse_response(resp)
        assert body["success"] is False
        assert body["status_code"] == 429
        assert body["error_type"] == "RateLimitExceeded"
        assert body["message"] == "Too many requests"
        assert body["details"] is None

    @pytest.mark.asyncio
    async def test_ignores_exception_type(self):
        resp = await rate_limit_handler(_mock_request(), ValueError("irrelevant"))
        code, body = _parse_response(resp)
        assert code == 429
        assert body["error_type"] == "RateLimitExceeded"
