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


