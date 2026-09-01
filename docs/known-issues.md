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


