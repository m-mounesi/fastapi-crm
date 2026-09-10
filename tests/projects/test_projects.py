import pytest
from security.jwt import create_access_token


PERMISSIONS_ALL_PROJECT = [
    "project.create",
    "project.read",
    "project.update",
    "project.delete",
    "project.restore",
]

PERMISSIONS_ALL_CUSTOMER = [
    "customer.create",
    "customer.read",
]


def _make_headers(user):
    token = create_access_token(
        {"sub": user.username, "user_id": user.user_id, "type": "access"}
    )
    return {"Authorization": f"Bearer {token}"}


def _grant_permissions(client, admin_headers, permissions, role_name="viewer"):
    for perm in permissions:
        resp = client.post(
            f"/admin/rbac/roles/{role_name}/permissions",
            params={"permission_name": perm},
            headers=admin_headers,
        )
        assert resp.status_code == 200


def _create_customer_via_api(client, headers, name="Default Customer"):
    resp = client.post("/customers/", json={"name": name}, headers=headers)
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.fixture()
def seeded_client(client, seed_db):
    return client


@pytest.fixture()
def admin_hdrs(create_user, assign_role):
    user, _ = create_user("proj_admin", "adminpass123")
    assign_role(user.user_id, "admin")
    return _make_headers(user)


@pytest.fixture()
def user_a_hdrs(seeded_client, create_user, assign_role, admin_hdrs):
    _grant_permissions(
        seeded_client, admin_hdrs, PERMISSIONS_ALL_CUSTOMER + PERMISSIONS_ALL_PROJECT
    )
    user, _ = create_user("proj_user_a", "pass123")
    assign_role(user.user_id, "viewer")
    return _make_headers(user)


@pytest.fixture()
def user_b_hdrs(seeded_client, create_user, assign_role, user_a_hdrs):
    user, _ = create_user("proj_user_b", "pass123")
    assign_role(user.user_id, "viewer")
    return _make_headers(user)


def _create_project(client, headers, customer_id, **overrides):
    payload = {"title": "Default Project", "customer_id": customer_id}
    payload.update(overrides)
    return client.post("/projects/", json=payload, headers=headers)


class TestCreateProject:
    def test_create_project_success(self, seeded_client, admin_hdrs):
        cid = _create_customer_via_api(seeded_client, admin_hdrs)
        resp = _create_project(
            seeded_client, admin_hdrs, customer_id=cid, title="Website Redesign"
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["title"] == "Website Redesign"
        assert body["customer_id"] == cid
        assert body["status"] == "active"
        assert "id" in body

    def test_create_project_missing_title(self, seeded_client, admin_hdrs):
        cid = _create_customer_via_api(seeded_client, admin_hdrs)
        resp = seeded_client.post(
            "/projects/",
            json={"customer_id": cid},
            headers=admin_hdrs,
        )
        assert resp.status_code == 422

    def test_create_project_invalid_customer_id(self, seeded_client, admin_hdrs):
        resp = _create_project(
            seeded_client, admin_hdrs, customer_id=9999, title="Orphan Project"
        )
        assert resp.status_code == 404


class TestReadProjects:
    def test_get_all_projects(self, seeded_client, admin_hdrs):
        cid = _create_customer_via_api(seeded_client, admin_hdrs)
        _create_project(seeded_client, admin_hdrs, customer_id=cid, title="P1")
        _create_project(seeded_client, admin_hdrs, customer_id=cid, title="P2")
        resp = seeded_client.get("/projects/", headers=admin_hdrs)
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_get_project_by_id(self, seeded_client, admin_hdrs):
        cid = _create_customer_via_api(seeded_client, admin_hdrs)
        create_resp = _create_project(
            seeded_client, admin_hdrs, customer_id=cid, title="ByID"
        )
        pid = create_resp.json()["id"]
        resp = seeded_client.get(f"/projects/{pid}", headers=admin_hdrs)
        assert resp.status_code == 200
        assert resp.json()["title"] == "ByID"

    def test_get_nonexistent_project(self, seeded_client, admin_hdrs):
        resp = seeded_client.get("/projects/9999", headers=admin_hdrs)
        assert resp.status_code == 404
        assert resp.json()["error_type"] == "ProjectNotFound"


class TestProjectOwnershipVisibility:
    def test_admin_sees_all_projects(
        self, seeded_client, admin_hdrs, user_a_hdrs, user_b_hdrs
    ):
        cid_a = _create_customer_via_api(seeded_client, user_a_hdrs, name="Cust A")
        cid_b = _create_customer_via_api(seeded_client, user_b_hdrs, name="Cust B")
        _create_project(seeded_client, user_a_hdrs, customer_id=cid_a, title="Proj A")
        _create_project(seeded_client, user_b_hdrs, customer_id=cid_b, title="Proj B")
        resp = seeded_client.get("/projects/", headers=admin_hdrs)
        assert resp.status_code == 200
        titles = {p["title"] for p in resp.json()}
        assert titles == {"Proj A", "Proj B"}

    def test_nonadmin_sees_own_only(
        self, seeded_client, admin_hdrs, user_a_hdrs, user_b_hdrs
    ):
        cid_a = _create_customer_via_api(seeded_client, user_a_hdrs, name="Cust A2")
        cid_b = _create_customer_via_api(seeded_client, user_b_hdrs, name="Cust B2")
        _create_project(seeded_client, user_a_hdrs, customer_id=cid_a, title="Mine")
        _create_project(seeded_client, user_b_hdrs, customer_id=cid_b, title="Theirs")
        resp = seeded_client.get("/projects/", headers=user_a_hdrs)
        assert resp.status_code == 200
        titles = {p["title"] for p in resp.json()}
        assert titles == {"Mine"}


class TestUpdateProject:
    def test_update_project_success(self, seeded_client, admin_hdrs):
        cid = _create_customer_via_api(seeded_client, admin_hdrs)
        create_resp = _create_project(
            seeded_client, admin_hdrs, customer_id=cid, title="Old Title"
        )
        pid = create_resp.json()["id"]
        resp = seeded_client.put(
            f"/projects/{pid}",
            json={"title": "New Title", "status": "completed"},
            headers=admin_hdrs,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["title"] == "New Title"
        assert body["status"] == "completed"

    def test_update_other_users_project_denied(
        self, seeded_client, user_a_hdrs, user_b_hdrs
    ):
        cid = _create_customer_via_api(seeded_client, user_a_hdrs, name="Shared Cust")
        create_resp = _create_project(
            seeded_client, user_a_hdrs, customer_id=cid, title="A's Project"
        )
        pid = create_resp.json()["id"]
        resp = seeded_client.put(
            f"/projects/{pid}",
            json={"title": "Stolen"},
            headers=user_b_hdrs,
        )
        assert resp.status_code == 403
        assert resp.json()["error_type"] == "PermissionDenied"

    def test_update_nonexistent_project(self, seeded_client, admin_hdrs):
        resp = seeded_client.put(
            "/projects/9999",
            json={"title": "Ghost"},
            headers=admin_hdrs,
        )
        assert resp.status_code == 404
        assert resp.json()["error_type"] == "ProjectNotFound"


class TestDeleteProject:
    def test_delete_project_success(self, seeded_client, admin_hdrs):
        cid = _create_customer_via_api(seeded_client, admin_hdrs)
        create_resp = _create_project(
            seeded_client, admin_hdrs, customer_id=cid, title="Doomed"
        )
        pid = create_resp.json()["id"]
        resp = seeded_client.delete(f"/projects/{pid}", headers=admin_hdrs)
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        list_resp = seeded_client.get("/projects/", headers=admin_hdrs)
        assert len(list_resp.json()) == 0

    def test_delete_other_users_project_denied(
        self, seeded_client, user_a_hdrs, user_b_hdrs
    ):
        cid = _create_customer_via_api(seeded_client, user_a_hdrs, name="Cust X")
        create_resp = _create_project(
            seeded_client, user_a_hdrs, customer_id=cid, title="Protected"
        )
        pid = create_resp.json()["id"]
        resp = seeded_client.delete(f"/projects/{pid}", headers=user_b_hdrs)
        assert resp.status_code == 403
        assert resp.json()["error_type"] == "PermissionDenied"

    def test_delete_nonexistent_project(self, seeded_client, admin_hdrs):
        resp = seeded_client.delete("/projects/9999", headers=admin_hdrs)
        assert resp.status_code == 404
        assert resp.json()["error_type"] == "ProjectNotFound"


class TestRestoreProject:
    def test_restore_project_success(self, seeded_client, admin_hdrs):
        cid = _create_customer_via_api(seeded_client, admin_hdrs)
        create_resp = _create_project(
            seeded_client, admin_hdrs, customer_id=cid, title="Phoenix"
        )
        pid = create_resp.json()["id"]
        seeded_client.delete(f"/projects/{pid}", headers=admin_hdrs)
        get_resp = seeded_client.get(f"/projects/{pid}", headers=admin_hdrs)
        assert get_resp.status_code == 404
        restore_resp = seeded_client.post(
            f"/projects/{pid}/restore", headers=admin_hdrs
        )
        assert restore_resp.status_code == 200
        assert restore_resp.json()["success"] is True
        get_resp = seeded_client.get(f"/projects/{pid}", headers=admin_hdrs)
        assert get_resp.status_code == 200
        assert get_resp.json()["title"] == "Phoenix"


class TestProjectAuth:
    def test_unauthenticated_access_denied(self, seeded_client):
        resp = seeded_client.get("/projects/")
        assert resp.status_code == 401
