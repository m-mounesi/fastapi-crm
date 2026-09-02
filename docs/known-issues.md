# Known Issues

## Refresh Token Collision

- Status: Open
- Found by: Pytest
- Location: `security/jwt.py`
- Symptom: Refresh token rotation can generate a duplicate JWT.
- Cause: Refresh tokens lack a unique `jti`.
- Test: `tests/auth/test_auth.py::TestRefresh::test_refresh_token_success`
- Current workaround: Test marked as `xfail`.
- Planned fix: Add a unique `jti` to refresh tokens.

## Customers

### POST `/customers/` returns 200 instead of 201

- Status: Open
- Found by: Pytest
- Location: `app/modules/customers/router.py:21`
- Symptom: The customer creation endpoint returns HTTP 200.
- Cause: The router does not set `status_code=201`.
- Test: `tests/customers/test_customers.py::TestCreateCustomer::test_create_customer_success`
- Current workaround: None.
- Planned fix: Add `status_code=201` to the `@router.post("/")` decorator.

### Inconsistent 403 error types for ownership violations

- Status: Open
- Found by: Pytest
- Location: `app/modules/customers/service.py:31-32` and `service.py:53-55`
- Symptom: `get_customer` raises `PermissionDeniedException` (`error_type: "PermissionDenied"`), while `update_customer` and `delete_customer` raise `HTTPException(403)` (`error_type: "HTTPException"`).
- Cause: Mixed exception types for the same ownership-denied concept.
- Test: `tests/customers/test_customers.py::TestUpdateCustomer::test_update_other_users_customer_denied` and `test_delete_other_users_customer_denied`
- Current workaround: None. HTTP status is correct; only the error type differs.
- Planned fix: Use `PermissionDeniedException` consistently across all ownership checks.

## RBAC

### `assign_permission_to_role` is not idempotent

- Status: Open
- Found by: Pytest
- Location: `app/modules/rbac/repository.py:46-51`
- Symptom: Assigning the same permission to a role more than once causes a `UNIQUE constraint failed` error and results in HTTP 500.
- Cause: `assign_permission_to_role` inserts without checking for existing records. `assign_role` handles duplicates safely, but `assign_permission` does not.
- Test: Discovered while setting up Projects test fixtures (`tests/projects/test_projects.py`).
- Current workaround: Ensure permissions are only granted once per role in test fixtures.
- Planned fix: Add a duplicate check in `RBACService.assign_permission` or `RBACRepository.assign_permission_to_role`, consistent with how `assign_role` handles idempotency.

## Tasks

### POST `/tasks/` returns 200 instead of 201

- Status: Open
- Found by: Pytest
- Location: `app/modules/tasks/router.py:16`
- Symptom: The task creation endpoint returns HTTP 200.
- Cause: The router does not set `status_code=201`.
- Test: `tests/tasks/test_tasks.py::TestCreateTask::test_create_task_success`
- Current workaround: None.
- Planned fix: Add `status_code=201` to the `@router.post("/")` decorator.

### Inconsistent 403 error types for ownership violations

- Status: Open
- Found by: Pytest
- Location: `app/modules/tasks/service.py:56-57`, `service.py:67-68`, `service.py:79-82`, `service.py:108-111`
- Symptom: `get_task` and `toggle_task` raise `PermissionDeniedException` (`error_type: "PermissionDenied"`), while `update_task` and `delete_task` raise `HTTPException(403)` (`error_type: "HTTPException"`).
- Cause: Mixed exception types for the same ownership-denied concept.
- Test: `tests/tasks/test_tasks.py::TestToggleTask::test_toggle_other_users_task_denied` and `TestUpdateTask::test_update_other_users_task_denied`
- Current workaround: None. HTTP status is correct; only the error type differs.
- Planned fix: Use `PermissionDeniedException` consistently across all ownership checks.

### Inconsistent 404 error types for missing tasks

- Status: Open
- Found by: Pytest
- Location: `app/modules/tasks/service.py:53-54`, `service.py:64-65`, `service.py:75-77`, `service.py:105-106`
- Symptom: `get_task` and `toggle_task` raise `TaskNotFoundException` (`error_type: "TaskNotFound"`), while `update_task` and `delete_task` return `None` and the router raises `HTTPException(404)` (`error_type: "HTTPException"`).
- Cause: Mixed patterns for not-found handling.
- Test: `tests/tasks/test_tasks.py::TestReadTasks::test_get_nonexistent_task` and `TestToggleTask::test_toggle_other_users_task_denied`
- Current workaround: None. HTTP status is correct; only the error type differs.
- Planned fix: Use `TaskNotFoundException` consistently in the service layer for all not-found cases.


