from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from core.exceptions import (
    CustomerNotFoundException,
    NoteNotFoundException,
    PermissionNotFoundException,
    ProjectNotFoundException,
    RoleNotFoundException,
    PermissionDeniedException,
    TaskNotFoundException,
    UnauthorizedException,
    InvalidTokenException,
)
from core.logger import get_logger
from core.schemas import ErrorResponse

logger = get_logger("exception")


async def global_exception_handler(request: Request, exc: Exception):
    # Request Validation Error (for query/path parameters)

    if isinstance(exc, RequestValidationError):
        errors = {}
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            errors[field] = error["msg"]

        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                status_code=422,
                error_type="RequestValidationError",
                message="Request validation failed",
                details=errors,
            ).model_dump(),
        )

    # Pydantic Validation Error (For body)
    if isinstance(exc, ValidationError):
        errors = {}
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            errors[field] = error["msg"]

        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                status_code=422,
                error_type="ValidationError",
                message="Validation failed",
                details=errors,
            ).model_dump(),
        )

    # FastAPI HTTP Exception (404, 401, etc)
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                status_code=exc.status_code,
                error_type="HTTPException",
                message=str(exc.detail),
                details=None,
            ).model_dump(),
        )

    if isinstance(exc, RoleNotFoundException):
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                status_code=404,
                error_type="RoleNotFound",
                message="Role not found",
                details=None,
            ).model_dump(),
        )

    if isinstance(exc, PermissionNotFoundException):
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                status_code=404,
                error_type="PermissionNotFound",
                message="Permission not found",
                details=None,
            ).model_dump(),
        )

    if isinstance(exc, UnauthorizedException):
        return JSONResponse(
            status_code=401,
            content=ErrorResponse(
                status_code=401,
                error_type="Unauthorized",
                message=str(exc.message),
                details=None,
            ).model_dump(),
        )

    if isinstance(exc, InvalidTokenException):
        return JSONResponse(
            status_code=401,
            content=ErrorResponse(
                status_code=401,
                error_type="InvalidToken",
                message=str(exc.message),
                details=None,
            ).model_dump(),
        )

    if isinstance(exc, PermissionDeniedException):
        return JSONResponse(
            status_code=403,
            content=ErrorResponse(
                status_code=403,
                error_type="PermissionDenied",
                message=str(exc.message),
                details=None,
            ).model_dump(),
        )

    if isinstance(exc, CustomerNotFoundException):
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                status_code=404,
                error_type="CustomerNotFound",
                message="Customer not found",
                details=None,
            ).model_dump(),
        )

    if isinstance(exc, ProjectNotFoundException):
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                status_code=404,
                error_type="ProjectNotFound",
                message="Project not found",
                details=None,
            ).model_dump(),
        )

    if isinstance(exc, TaskNotFoundException):
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                status_code=404,
                error_type="TaskNotFound",
                message="Task not found",
                details=None,
            ).model_dump(),
        )

    if isinstance(exc, NoteNotFoundException):
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                status_code=404,
                error_type="NoteNotFound",
                message="Note not found",
                details=None,
            ).model_dump(),
        )

    # Unknown Error (500)
    logger.exception("Unhandled server error occurred", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            status_code=500,
            error_type="InternalServerError",
            message="An unexpected error occurred",
            details=None,
        ).model_dump(),
    )


async def rate_limit_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=429,
        content=ErrorResponse(
            status_code=429,
            error_type="RateLimitExceeded",
            message="Too many requests",
            details=None,
        ).model_dump(),
    )
