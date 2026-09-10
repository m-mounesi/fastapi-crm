from security.jwt import create_access_token


class TestAssignRoleEndpoint:
    def test_assign_role_success(self, client, auth_headers, create_user, seed_db):
        user, _ = create_user("target_user")
        resp = client.post(
            f"/admin/rbac/users/{user.user_id}/roles",
            params={"role_name": "viewer"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "Role assigned" in body["message"]

    def test_assign_role_nonexistent_role(
        self, client, auth_headers, create_user, seed_db
    ):
        user, _ = create_user("target_user2")
        resp = client.post(
            f"/admin/rbac/users/{user.user_id}/roles",
            params={"role_name": "nonexistent_role"},
            headers=auth_headers,
        )
        assert resp.status_code == 404
        assert resp.json()["error_type"] == "RoleNotFound"

    def test_assign_role_duplicate_idempotent(
        self, client, auth_headers, create_user, assign_role, seed_db
    ):
        user, _ = create_user("target_user3")
        assign_role(user.user_id, "viewer")
        resp = client.post(
            f"/admin/rbac/users/{user.user_id}/roles",
            params={"role_name": "viewer"},
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_assign_role_viewer_denied(
        self, client, viewer_headers, create_user, seed_db
    ):
        user, _ = create_user("target_user4")
        resp = client.post(
            f"/admin/rbac/users/{user.user_id}/roles",
            params={"role_name": "admin"},
            headers=viewer_headers,
        )
        assert resp.status_code == 403
        assert resp.json()["error_type"] == "PermissionDenied"

    def test_assign_role_unauthenticated(self, client, create_user, seed_db):
        user, _ = create_user("target_user5")
        resp = client.post(
            f"/admin/rbac/users/{user.user_id}/roles",
            params={"role_name": "viewer"},
        )
        assert resp.status_code == 401


class TestAssignPermissionEndpoint:
    def test_assign_permission_success(self, client, auth_headers, seed_db):
        resp = client.post(
            "/admin/rbac/roles/operator/permissions",
            params={"permission_name": "customer.read"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_assign_permission_duplicate_idempotent(
        self, client, auth_headers, seed_db
    ):
        resp1 = client.post(
            "/admin/rbac/roles/operator/permissions",
            params={"permission_name": "customer.read"},
            headers=auth_headers,
        )
        assert resp1.status_code == 200

        resp2 = client.post(
            "/admin/rbac/roles/operator/permissions",
            params={"permission_name": "customer.read"},
            headers=auth_headers,
        )
        assert resp2.status_code == 200
        assert resp2.json()["success"] is True

    def test_assign_permission_nonexistent_role(self, client, auth_headers, seed_db):
        resp = client.post(
            "/admin/rbac/roles/nonexistent/permissions",
            params={"permission_name": "customer.read"},
            headers=auth_headers,
        )
        assert resp.status_code == 404
        assert resp.json()["error_type"] == "RoleNotFound"

    def test_assign_permission_nonexistent_permission(
        self, client, auth_headers, seed_db
    ):
        resp = client.post(
            "/admin/rbac/roles/operator/permissions",
            params={"permission_name": "fake.permission"},
            headers=auth_headers,
        )
        assert resp.status_code == 404
        assert resp.json()["error_type"] == "PermissionNotFound"

    def test_assign_permission_viewer_denied(self, client, viewer_headers, seed_db):
        resp = client.post(
            "/admin/rbac/roles/operator/permissions",
            params={"permission_name": "customer.read"},
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_assign_permission_unauthenticated(self, client, seed_db):
        resp = client.post(
            "/admin/rbac/roles/operator/permissions",
            params={"permission_name": "customer.read"},
        )
        assert resp.status_code == 401


class TestRBACAuthorizationBoundaries:
    def test_viewer_denied_customer_read(self, client, viewer_headers, seed_db):
        resp = client.get("/customers/", headers=viewer_headers)
        assert resp.status_code == 403
        assert resp.json()["error_type"] == "PermissionDenied"

    def test_grant_permission_grants_access(
        self, client, create_user, assign_role, seed_db
    ):
        # Create an admin to call the RBAC endpoint
        admin_user, _ = create_user("rbac_admin", "adminpass123")
        assign_role(admin_user.user_id, "admin")
        admin_token = create_access_token(
            {
                "sub": admin_user.username,
                "user_id": admin_user.user_id,
                "type": "access",
            }
        )
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Grant customer.create permission to the viewer role
        resp = client.post(
            "/admin/rbac/roles/viewer/permissions",
            params={"permission_name": "customer.create"},
            headers=admin_headers,
        )
        assert resp.status_code == 200

        # Register a new viewer user
        client.post(
            "/auth/register",
            data={"username": "new_viewer", "password": "viewerpass123"},
        )
        login_resp = client.post(
            "/auth/login",
            data={"username": "new_viewer", "password": "viewerpass123"},
        )
        viewer_token = login_resp.json()["access_token"]
        viewer_hdrs = {"Authorization": f"Bearer {viewer_token}"}

        # Viewer should now be able to create a customer
        resp = client.post(
            "/customers/",
            json={"name": "Test Customer"},
            headers=viewer_hdrs,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Test Customer"

    def test_operator_denied_rbac_endpoints(
        self, client, operator_headers, create_user, seed_db
    ):
        user, _ = create_user("op_target")
        resp1 = client.post(
            f"/admin/rbac/users/{user.user_id}/roles",
            params={"role_name": "viewer"},
            headers=operator_headers,
        )
        resp2 = client.post(
            "/admin/rbac/roles/viewer/permissions",
            params={"permission_name": "customer.read"},
            headers=operator_headers,
        )
        assert resp1.status_code == 403
        assert resp2.status_code == 403
