import pytest
from security.jwt import create_access_token


PERMISSIONS_ALL_CUSTOMER = [
    "customer.create",
    "customer.read",
]
PERMISSIONS_ALL_PROJECT = [
    "project.create",
    "project.read",
]
PERMISSIONS_ALL_TASK = [
    "task.create",
    "task.read",
    "task.update",
    "task.delete",
    "task.restore",
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


def _create_customer(client, headers, name="Default Customer"):
    resp = client.post("/customers/", json={"name": name}, headers=headers)
    assert resp.status_code == 200
    return resp.json()["id"]


def _create_project(client, headers, customer_id, title="Default Project"):
    resp = client.post(
        "/projects/", json={"title": title, "customer_id": customer_id}, headers=headers
    )
    assert resp.status_code == 200
    return resp.json()["id"]


def _create_task(client, headers, project_id, **overrides):
    payload = {"title": "Default Task", "project_id": project_id}
    payload.update(overrides)
    return client.post("/tasks/", json=payload, headers=headers)


@pytest.fixture()
def seeded_client(client, seed_db):
    return client


@pytest.fixture()
def admin_hdrs(create_user, assign_role):
    user, _ = create_user("task_admin", "adminpass123")
    assign_role(user.user_id, "admin")
    return _make_headers(user)


@pytest.fixture()
def user_a_hdrs(seeded_client, create_user, assign_role, admin_hdrs):
    _grant_permissions(
        seeded_client,
        admin_hdrs,
        PERMISSIONS_ALL_CUSTOMER + PERMISSIONS_ALL_PROJECT + PERMISSIONS_ALL_TASK,
    )
    user, _ = create_user("task_user_a", "pass123")
    assign_role(user.user_id, "viewer")
    return _make_headers(user)


@pytest.fixture()
def user_b_hdrs(seeded_client, create_user, assign_role, user_a_hdrs):
    user, _ = create_user("task_user_b", "pass123")
    assign_role(user.user_id, "viewer")
    return _make_headers(user)


class TestCreateTask:
    def test_create_task_success(self, seeded_client, admin_hdrs):
        cid = _create_customer(seeded_client, admin_hdrs)
        pid = _create_project(seeded_client, admin_hdrs, customer_id=cid)
        resp = _create_task(
            seeded_client, admin_hdrs, project_id=pid, title="Fix login bug"
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["title"] == "Fix login bug"
        assert body["project_id"] == pid
        assert body["completed"] is False
        assert body["assigned_to"] is None
        assert "id" in body

    def test_create_task_missing_title(self, seeded_client, admin_hdrs):
        cid = _create_customer(seeded_client, admin_hdrs)
        pid = _create_project(seeded_client, admin_hdrs, customer_id=cid)
        resp = seeded_client.post(
            "/tasks/", json={"project_id": pid}, headers=admin_hdrs
        )
        assert resp.status_code == 422

    def test_create_task_invalid_project_id(self, seeded_client, admin_hdrs):
        resp = _create_task(
            seeded_client, admin_hdrs, project_id=9999, title="Orphan Task"
        )
        assert resp.status_code == 404

    def test_create_task_invalid_assigned_user(self, seeded_client, admin_hdrs):
        cid = _create_customer(seeded_client, admin_hdrs)
        pid = _create_project(seeded_client, admin_hdrs, customer_id=cid)
        resp = _create_task(seeded_client, admin_hdrs, project_id=pid, assigned_to=9999)
        assert resp.status_code == 404


class TestReadTasks:
    def test_get_all_tasks(self, seeded_client, admin_hdrs):
        cid = _create_customer(seeded_client, admin_hdrs)
        pid = _create_project(seeded_client, admin_hdrs, customer_id=cid)
        _create_task(seeded_client, admin_hdrs, project_id=pid, title="T1")
        _create_task(seeded_client, admin_hdrs, project_id=pid, title="T2")
        resp = seeded_client.get("/tasks/", headers=admin_hdrs)
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_get_task_by_id(self, seeded_client, admin_hdrs):
        cid = _create_customer(seeded_client, admin_hdrs)
        pid = _create_project(seeded_client, admin_hdrs, customer_id=cid)
        create_resp = _create_task(
            seeded_client, admin_hdrs, project_id=pid, title="ByID"
        )
        tid = create_resp.json()["id"]
        resp = seeded_client.get(f"/tasks/{tid}", headers=admin_hdrs)
        assert resp.status_code == 200
        assert resp.json()["title"] == "ByID"

    def test_get_nonexistent_task(self, seeded_client, admin_hdrs):
        resp = seeded_client.get("/tasks/9999", headers=admin_hdrs)
        assert resp.status_code == 404

    def test_get_tasks_filter_by_project(self, seeded_client, admin_hdrs):
        cid = _create_customer(seeded_client, admin_hdrs)
        pid_a = _create_project(seeded_client, admin_hdrs, customer_id=cid, title="PA")
        pid_b = _create_project(seeded_client, admin_hdrs, customer_id=cid, title="PB")
        _create_task(seeded_client, admin_hdrs, project_id=pid_a, title="Task A1")
        _create_task(seeded_client, admin_hdrs, project_id=pid_a, title="Task A2")
        _create_task(seeded_client, admin_hdrs, project_id=pid_b, title="Task B1")
        resp = seeded_client.get(
            "/tasks/", params={"project_id": pid_a}, headers=admin_hdrs
        )
        assert resp.status_code == 200
        titles = {t["title"] for t in resp.json()}
        assert titles == {"Task A1", "Task A2"}


class TestTaskOwnershipVisibility:
    def test_admin_sees_all_tasks(
        self, seeded_client, admin_hdrs, user_a_hdrs, user_b_hdrs
    ):
        cid_a = _create_customer(seeded_client, user_a_hdrs, name="Cust A")
        pid_a = _create_project(seeded_client, user_a_hdrs, customer_id=cid_a)
        _create_task(seeded_client, user_a_hdrs, project_id=pid_a, title="A Task")

        cid_b = _create_customer(seeded_client, user_b_hdrs, name="Cust B")
        pid_b = _create_project(seeded_client, user_b_hdrs, customer_id=cid_b)
        _create_task(seeded_client, user_b_hdrs, project_id=pid_b, title="B Task")

        resp = seeded_client.get("/tasks/", headers=admin_hdrs)
        assert resp.status_code == 200
        titles = {t["title"] for t in resp.json()}
        assert titles == {"A Task", "B Task"}

    def test_nonadmin_sees_own_only(
        self, seeded_client, admin_hdrs, user_a_hdrs, user_b_hdrs
    ):
        cid_a = _create_customer(seeded_client, user_a_hdrs, name="Cust A2")
        pid_a = _create_project(seeded_client, user_a_hdrs, customer_id=cid_a)
        _create_task(seeded_client, user_a_hdrs, project_id=pid_a, title="Mine")

        cid_b = _create_customer(seeded_client, user_b_hdrs, name="Cust B2")
        pid_b = _create_project(seeded_client, user_b_hdrs, customer_id=cid_b)
        _create_task(seeded_client, user_b_hdrs, project_id=pid_b, title="Theirs")

        resp = seeded_client.get("/tasks/", headers=user_a_hdrs)
        assert resp.status_code == 200
        titles = {t["title"] for t in resp.json()}
        assert titles == {"Mine"}


class TestToggleTask:
    def test_toggle_task_success(self, seeded_client, admin_hdrs):
        cid = _create_customer(seeded_client, admin_hdrs)
        pid = _create_project(seeded_client, admin_hdrs, customer_id=cid)
        create_resp = _create_task(
            seeded_client, admin_hdrs, project_id=pid, title="Toggle Me"
        )
        tid = create_resp.json()["id"]
        assert create_resp.json()["completed"] is False

        resp1 = seeded_client.patch(f"/tasks/{tid}/toggle", headers=admin_hdrs)
        assert resp1.status_code == 200
        assert resp1.json()["completed"] is True

        resp2 = seeded_client.patch(f"/tasks/{tid}/toggle", headers=admin_hdrs)
        assert resp2.status_code == 200
        assert resp2.json()["completed"] is False

    def test_toggle_other_users_task_denied(
        self, seeded_client, user_a_hdrs, user_b_hdrs
    ):
        cid = _create_customer(seeded_client, user_a_hdrs, name="Shared Cust")
        pid = _create_project(seeded_client, user_a_hdrs, customer_id=cid)
        create_resp = _create_task(
            seeded_client, user_a_hdrs, project_id=pid, title="Protected"
        )
        tid = create_resp.json()["id"]
        resp = seeded_client.patch(f"/tasks/{tid}/toggle", headers=user_b_hdrs)
        assert resp.status_code == 403


class TestUpdateTask:
    def test_update_task_success(self, seeded_client, admin_hdrs):
        cid = _create_customer(seeded_client, admin_hdrs)
        pid = _create_project(seeded_client, admin_hdrs, customer_id=cid)
        create_resp = _create_task(
            seeded_client, admin_hdrs, project_id=pid, title="Old Title"
        )
        tid = create_resp.json()["id"]
        resp = seeded_client.put(
            f"/tasks/{tid}",
            json={"title": "New Title", "description": "Updated desc"},
            headers=admin_hdrs,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["title"] == "New Title"
        assert body["description"] == "Updated desc"

    def test_update_other_users_task_denied(
        self, seeded_client, user_a_hdrs, user_b_hdrs
    ):
        cid = _create_customer(seeded_client, user_a_hdrs, name="Cust X")
        pid = _create_project(seeded_client, user_a_hdrs, customer_id=cid)
        create_resp = _create_task(
            seeded_client, user_a_hdrs, project_id=pid, title="Protected"
        )
        tid = create_resp.json()["id"]
        resp = seeded_client.put(
            f"/tasks/{tid}",
            json={"title": "Stolen"},
            headers=user_b_hdrs,
        )
        assert resp.status_code == 403


class TestDeleteTask:
    def test_delete_task_success(self, seeded_client, admin_hdrs):
        cid = _create_customer(seeded_client, admin_hdrs)
        pid = _create_project(seeded_client, admin_hdrs, customer_id=cid)
        create_resp = _create_task(
            seeded_client, admin_hdrs, project_id=pid, title="Doomed"
        )
        tid = create_resp.json()["id"]
        resp = seeded_client.delete(f"/tasks/{tid}", headers=admin_hdrs)
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        list_resp = seeded_client.get("/tasks/", headers=admin_hdrs)
        assert len(list_resp.json()) == 0

    def test_delete_other_users_task_denied(
        self, seeded_client, user_a_hdrs, user_b_hdrs
    ):
        cid = _create_customer(seeded_client, user_a_hdrs, name="Cust Y")
        pid = _create_project(seeded_client, user_a_hdrs, customer_id=cid)
        create_resp = _create_task(
            seeded_client, user_a_hdrs, project_id=pid, title="Protected"
        )
        tid = create_resp.json()["id"]
        resp = seeded_client.delete(f"/tasks/{tid}", headers=user_b_hdrs)
        assert resp.status_code == 403


class TestRestoreTask:
    def test_restore_task_success(self, seeded_client, admin_hdrs):
        cid = _create_customer(seeded_client, admin_hdrs)
        pid = _create_project(seeded_client, admin_hdrs, customer_id=cid)
        create_resp = _create_task(
            seeded_client, admin_hdrs, project_id=pid, title="Phoenix"
        )
        tid = create_resp.json()["id"]
        seeded_client.delete(f"/tasks/{tid}", headers=admin_hdrs)
        get_resp = seeded_client.get(f"/tasks/{tid}", headers=admin_hdrs)
        assert get_resp.status_code == 404

        restore_resp = seeded_client.post(f"/tasks/{tid}/restore", headers=admin_hdrs)
        assert restore_resp.status_code == 200
        assert restore_resp.json()["success"] is True

        get_resp = seeded_client.get(f"/tasks/{tid}", headers=admin_hdrs)
        assert get_resp.status_code == 200
        assert get_resp.json()["title"] == "Phoenix"
