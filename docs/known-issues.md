# Known Issues

## Refresh Token Collision

- Status: Resolved
- Found by: Pytest
- Location: `security/jwt.py`
- Symptom: Refresh token rotation can generate a duplicate JWT.
- Cause: Refresh tokens lacked a unique `jti`.
- Test: `tests/auth/test_auth.py::TestRefresh::test_refresh_token_success`
- Resolution: Added `uuid4`-based `jti` claim to `create_refresh_token`. Both the auth integration test and `tests/security/test_jwt.py` now pass with no xfail markers.

## Customers

### POST `/customers/` returns 200 instead of 201

- Status: Resolved
- Found by: Pytest
- Location: `app/modules/customers/router.py:21`
- Symptom: The customer creation endpoint returns HTTP 200.
- Cause: The router does not set `status_code=201`.
- Test: `tests/customers/test_customers.py::TestCreateCustomer::test_create_customer_success`
- Resolution: Added `status_code=201` to the `@router.post("/")` decorator.

### Inconsistent 403 error types for ownership violations

- Status: Resolved
- Found by: Pytest
- Location: `app/modules/customers/service.py:31-32` and `service.py:53-55`
- Symptom: `get_customer` raises `PermissionDeniedException` (`error_type: "PermissionDenied"`), while `update_customer` and `delete_customer` raise `HTTPException(403)` (`error_type: "HTTPException"`).
- Cause: Mixed exception types for the same ownership-denied concept.
- Test: `tests/customers/test_customers.py::TestUpdateCustomer::test_update_other_users_customer_denied` and `test_delete_other_users_customer_denied`
- Resolution: Standardized `update_customer` and `delete_customer` to raise `PermissionDeniedException`, matching the pattern in `get_customer`. Router null-check guards removed since services now raise exceptions directly.

## RBAC

### `assign_permission_to_role` is not idempotent

- Status: Resolved
- Found by: Pytest
- Location: `app/modules/rbac/repository.py:46-51`
- Symptom: Assigning the same permission to a role more than once causes a `UNIQUE constraint failed` error and results in HTTP 500.
- Cause: `assign_permission_to_role` inserts without checking for existing records. `assign_role` handles duplicates safely, but `assign_permission` does not.
- Test: `tests/rbac/test_rbac.py::TestAssignPermissionEndpoint::test_assign_permission_duplicate_idempotent`
- Resolution: Added `role_has_permission` check in `RBACRepository` and idempotency guard in `RBACService.assign_permission`, mirroring the existing `assign_role` / `user_has_role` pattern. Duplicate assignment now returns the existing record with HTTP 200.

## Tasks

### Inconsistent 403/404 error types for ownership violations and missing projects

- Status: Resolved
- Found by: Pytest
- Location: `app/modules/projects/service.py`
- Symptom: `get_project` used custom exceptions (`PermissionDeniedException` / `ProjectNotFoundException`), while `update_project` and `delete_project` returned `None` and raised `HTTPException(403/404)` with `error_type: "HTTPException"`.
- Cause: Mixed exception patterns across methods.
- Resolution: Standardized `update_project` and `delete_project` to raise `ProjectNotFoundException` / `PermissionDeniedException`, matching the pattern in `get_project`. Router null-check guards removed. Tests updated to assert correct `error_type`.

### POST `/tasks/` returns 200 instead of 201

- Status: Resolved
- Found by: Pytest
- Location: `app/modules/tasks/router.py:16`
- Symptom: The task creation endpoint returns HTTP 200.
- Cause: The router does not set `status_code=201`.
- Test: `tests/tasks/test_tasks.py::TestCreateTask::test_create_task_success`
- Resolution: Added `status_code=201` to the `@router.post("/")` decorator.

### Inconsistent 403 error types for ownership violations

- Status: Resolved
- Found by: Pytest
- Location: `app/modules/tasks/service.py:56-57`, `service.py:67-68`, `service.py:79-82`, `service.py:108-111`
- Symptom: `get_task` and `toggle_task` raise `PermissionDeniedException` (`error_type: "PermissionDenied"`), while `update_task` and `delete_task` raise `HTTPException(403)` (`error_type: "HTTPException"`).
- Cause: Mixed exception types for the same ownership-denied concept.
- Test: `tests/tasks/test_tasks.py::TestToggleTask::test_toggle_other_users_task_denied` and `TestUpdateTask::test_update_other_users_task_denied`
- Resolution: Standardized `update_task` and `delete_task` to raise `PermissionDeniedException`, matching the pattern in `get_task` and `toggle_task`. Router null-check guards removed.

### Inconsistent 404 error types for missing tasks

- Status: Resolved
- Found by: Pytest
- Location: `app/modules/tasks/service.py:53-54`, `service.py:64-65`, `service.py:75-77`, `service.py:105-106`
- Symptom: `get_task` and `toggle_task` raise `TaskNotFoundException` (`error_type: "TaskNotFound"`), while `update_task` and `delete_task` return `None` and the router raises `HTTPException(404)` (`error_type: "HTTPException"`).
- Cause: Mixed patterns for not-found handling.
- Test: `tests/tasks/test_tasks.py::TestReadTasks::test_get_nonexistent_task` and `TestToggleTask::test_toggle_other_users_task_denied`
- Resolution: Standardized `update_task` and `delete_task` to raise `TaskNotFoundException`, matching the pattern in `get_task` and `toggle_task`. Router null-check guards removed.

## Notes

### POST `/notes/` returns 200 instead of 201

- Status: Resolved
- Found by: Pytest
- Location: `app/modules/notes/router.py:16`
- Symptom: The note creation endpoint returns HTTP 200.
- Cause: The router does not set `status_code=201`.
- Test: `tests/notes/test_notes.py::TestCreateNote::test_create_note_success`
- Resolution: Added `status_code=201` to the `@router.post("/")` decorator.

### Inconsistent 403 error types for ownership violations

- Status: Resolved
- Found by: Pytest
- Location: `app/modules/notes/service.py:31-32`, `service.py:53-56`, `service.py:76-79`
- Symptom: `get_note` raises `PermissionDeniedException` (`error_type: "PermissionDenied"`), while `update_note` and `delete_note` raise `HTTPException(403)` (`error_type: "HTTPException"`).
- Cause: Mixed exception types for the same ownership-denied concept.
- Test: `tests/notes/test_notes.py::TestReadNotes::test_get_other_users_note_denied`, `TestUpdateNote::test_update_other_users_note_denied`, and `TestDeleteNote::test_delete_other_users_note_denied`
- Resolution: Standardized `update_note` and `delete_note` to raise `PermissionDeniedException`, matching the pattern in `get_note`. Router null-check guards removed.

### Inconsistent 404 error types for missing notes

- Status: Resolved
- Found by: Pytest
- Location: `app/modules/notes/service.py:28-29`, `service.py:48-51`, `service.py:71-74`
- Symptom: `get_note` raises `NoteNotFoundException` (`error_type: "NoteNotFound"`), while `update_note` and `delete_note` return `None` and the router raises `HTTPException(404)` (`error_type: "HTTPException"`).
- Cause: Mixed patterns for not-found handling.
- Test: `tests/notes/test_notes.py::TestReadNotes::test_get_nonexistent_note`, `TestUpdateNote::test_update_nonexistent_note`, and `TestDeleteNote::test_delete_nonexistent_note`
- Resolution: Standardized `update_note` and `delete_note` to raise `NoteNotFoundException`, matching the pattern in `get_note`. Router null-check guards removed.

### Missing application-level FK validation for customer_id / project_id

- Status: Resolved
- Found by: Pytest
- Location: `app/modules/notes/service.py:14-22`
- Symptom: `create_note` accepts any `customer_id` or `project_id` without validating that the referenced Customer or Project exists. With the current SQLite test configuration (FK enforcement disabled), an invalid `customer_id` is accepted and the API returns 200.
- Cause: The Notes service does not validate foreign key references before inserting.
- Test: `tests/notes/test_notes.py::TestCreateNote::test_create_note_invalid_customer_id`
- Resolution: Injected `CustomerRepository` and `ProjectRepository` into `NoteService`. Added application-level FK validation in `create_note` and `update_note`, raising `CustomerNotFoundException` / `ProjectNotFoundException` for invalid references. Behavior is now consistent regardless of database engine.


