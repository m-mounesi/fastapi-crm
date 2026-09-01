import pytest
from security.jwt import create_access_token


PERMISSIONS_ALL_CUSTOMER = [
    "customer.create",
    "customer.read",
    "customer.update",
    "customer.delete",
    "customer.restore",
]


def _make_headers(user, role_name="viewer"):
    token = create_access_token(
        {"sub": user.username, "user_id": user.user_id, "type": "access"}
    )
    return {"Authorization": f"Bearer {token}"}


def _grant_customer_permissions(client, admin_headers, role_name="viewer"):
    for perm in PERMISSIONS_ALL_CUSTOMER:
        resp = client.post(
            f"/admin/rbac/roles/{role_name}/permissions",
            params={"permission_name": perm},
            headers=admin_headers,
        )
        assert resp.status_code == 200


def _register_and_login(client, username, password="pass123"):
    client.post(
        "/auth/register",
        data={"username": username, "password": password},
    )
    resp = client.post(
        "/auth/login",
        data={"username": username, "password": password},
    )
    return resp.json()["access_token"]


@pytest.fixture()
def seeded_client(client, seed_db):
    return client


@pytest.fixture()
def admin_hdrs(create_user, assign_role):
    user, _ = create_user("cust_admin", "adminpass123")
    assign_role(user.user_id, "admin")
    return _make_headers(user)


@pytest.fixture()
def user_a_hdrs(seeded_client, create_user, assign_role, admin_hdrs):
    _grant_customer_permissions(seeded_client, admin_hdrs)
    user, _ = create_user("user_a", "pass123")
    assign_role(user.user_id, "viewer")
    return _make_headers(user)


@pytest.fixture()
def user_b_hdrs(seeded_client, create_user, assign_role, admin_hdrs):
    user, _ = create_user("user_b", "pass123")
    assign_role(user.user_id, "viewer")
    return _make_headers(user)


def _create_customer(client, headers, **overrides):
    payload = {"name": "Default"}
    payload.update(overrides)
    return client.post("/customers/", json=payload, headers=headers)


class TestCreateCustomer:
    def test_create_customer_success(self, seeded_client, admin_hdrs):
        resp = _create_customer(
            seeded_client,
            admin_hdrs,
            name="Acme Corp",
            email="acme@example.com",
            phone="555-0100",
            description="A test customer",
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Acme Corp"
        assert body["email"] == "acme@example.com"
        assert body["phone"] == "555-0100"
        assert body["description"] == "A test customer"
        assert "id" in body

    def test_create_customer_missing_name(self, seeded_client, admin_hdrs):
        resp = seeded_client.post(
            "/customers/",
            json={"email": "noname@example.com"},
            headers=admin_hdrs,
        )
        assert resp.status_code == 422


class TestReadCustomers:
    def test_get_all_customers(self, seeded_client, admin_hdrs):
        _create_customer(seeded_client, admin_hdrs, name="C1")
        _create_customer(seeded_client, admin_hdrs, name="C2")
        resp = seeded_client.get("/customers/", headers=admin_hdrs)
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 2

    def test_get_customer_by_id(self, seeded_client, admin_hdrs):
        create_resp = _create_customer(
            seeded_client, admin_hdrs, name="ById", email="byid@example.com"
        )
        cid = create_resp.json()["id"]
        resp = seeded_client.get(f"/customers/{cid}", headers=admin_hdrs)
        assert resp.status_code == 200
        assert resp.json()["name"] == "ById"
        assert resp.json()["email"] == "byid@example.com"

    def test_get_nonexistent_customer(self, seeded_client, admin_hdrs):
        resp = seeded_client.get("/customers/9999", headers=admin_hdrs)
        assert resp.status_code == 404

    def test_admin_sees_all_customers(
        self, seeded_client, admin_hdrs, user_a_hdrs, user_b_hdrs
    ):
        _create_customer(seeded_client, user_a_hdrs, name="A Customer")
        _create_customer(seeded_client, user_b_hdrs, name="B Customer")
        resp = seeded_client.get("/customers/", headers=admin_hdrs)
        assert resp.status_code == 200
        names = {c["name"] for c in resp.json()}
        assert names == {"A Customer", "B Customer"}

    def test_nonadmin_sees_own_only(
        self, seeded_client, admin_hdrs, user_a_hdrs, user_b_hdrs
    ):
        _create_customer(seeded_client, user_a_hdrs, name="A Only")
        _create_customer(seeded_client, user_b_hdrs, name="B Only")
        resp = seeded_client.get("/customers/", headers=user_a_hdrs)
        assert resp.status_code == 200
        names = {c["name"] for c in resp.json()}
        assert names == {"A Only"}


class TestUpdateCustomer:
    def test_update_customer_success(self, seeded_client, admin_hdrs):
        create_resp = _create_customer(seeded_client, admin_hdrs, name="Original")
        cid = create_resp.json()["id"]
        resp = seeded_client.put(
            f"/customers/{cid}",
            json={"name": "Updated"},
            headers=admin_hdrs,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated"

    def test_update_partial_fields(self, seeded_client, admin_hdrs):
        create_resp = _create_customer(
            seeded_client,
            admin_hdrs,
            name="KeepMe",
            email="old@example.com",
            phone="111",
            description="keep desc",
        )
        cid = create_resp.json()["id"]
        resp = seeded_client.put(
            f"/customers/{cid}",
            json={"email": "new@example.com"},
            headers=admin_hdrs,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "KeepMe"
        assert body["email"] == "new@example.com"
        assert body["phone"] == "111"
        assert body["description"] == "keep desc"

    def test_update_other_users_customer_denied(
        self, seeded_client, user_a_hdrs, user_b_hdrs
    ):
        create_resp = _create_customer(seeded_client, user_a_hdrs, name="A's Customer")
        cid = create_resp.json()["id"]
        resp = seeded_client.put(
            f"/customers/{cid}",
            json={"name": "Hijacked"},
            headers=user_b_hdrs,
        )
        assert resp.status_code == 403


class TestDeleteCustomer:
    def test_delete_customer_success(self, seeded_client, admin_hdrs):
        create_resp = _create_customer(seeded_client, admin_hdrs, name="ToDelete")
        cid = create_resp.json()["id"]
        resp = seeded_client.delete(f"/customers/{cid}", headers=admin_hdrs)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_soft_delete_hides_from_list(self, seeded_client, admin_hdrs):
        create_resp = _create_customer(seeded_client, admin_hdrs, name="Ghost")
        cid = create_resp.json()["id"]
        seeded_client.delete(f"/customers/{cid}", headers=admin_hdrs)
        resp = seeded_client.get("/customers/", headers=admin_hdrs)
        assert resp.status_code == 200
        assert len(resp.json()) == 0

    def test_delete_other_users_customer_denied(
        self, seeded_client, user_a_hdrs, user_b_hdrs
    ):
        create_resp = _create_customer(seeded_client, user_a_hdrs, name="Protected")
        cid = create_resp.json()["id"]
        resp = seeded_client.delete(f"/customers/{cid}", headers=user_b_hdrs)
        assert resp.status_code == 403


class TestRestoreCustomer:
    def test_restore_customer_success(self, seeded_client, admin_hdrs):
        create_resp = _create_customer(seeded_client, admin_hdrs, name="Restored")
        cid = create_resp.json()["id"]
        seeded_client.delete(f"/customers/{cid}", headers=admin_hdrs)
        resp = seeded_client.post(f"/customers/{cid}/restore", headers=admin_hdrs)
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        get_resp = seeded_client.get(f"/customers/{cid}", headers=admin_hdrs)
        assert get_resp.status_code == 200
        assert get_resp.json()["name"] == "Restored"

    def test_restore_other_users_customer_denied(
        self, seeded_client, admin_hdrs, user_a_hdrs, user_b_hdrs
    ):
        create_resp = _create_customer(seeded_client, user_a_hdrs, name="A's")
        cid = create_resp.json()["id"]
        seeded_client.delete(f"/customers/{cid}", headers=admin_hdrs)
        resp = seeded_client.post(f"/customers/{cid}/restore", headers=user_b_hdrs)
        assert resp.status_code == 403


class TestCustomerAuth:
    def test_unauthenticated_access_denied(self, seeded_client):
        resp = seeded_client.get("/customers/")
        assert resp.status_code == 401
