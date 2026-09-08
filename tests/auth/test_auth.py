class TestRegister:
    def test_register_success(self, client, seed_db):
        response = client.post(
            "/auth/register",
            data={"username": "newuser", "password": "securepass123"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["success"] is True
        assert body["status_code"] == 201
        assert "created successfully" in body["message"]

    def test_register_duplicate(self, client, seed_db):
        client.post(
            "/auth/register",
            data={"username": "dupuser", "password": "securepass123"},
        )
        response = client.post(
            "/auth/register",
            data={"username": "dupuser", "password": "securepass123"},
        )
        assert response.status_code == 400

    def test_register_missing_username(self, client, seed_db):
        response = client.post(
            "/auth/register",
            data={"password": "securepass123"},
        )
        assert response.status_code == 422

    def test_register_missing_password(self, client, seed_db):
        response = client.post(
            "/auth/register",
            data={"username": "nouser"},
        )
        assert response.status_code == 422


class TestLogin:
    def test_login_success(self, client, seed_db):
        client.post(
            "/auth/register",
            data={"username": "loginuser", "password": "securepass123"},
        )
        response = client.post(
            "/auth/login",
            data={"username": "loginuser", "password": "securepass123"},
        )
        assert response.status_code == 202
        body = response.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

    def test_login_wrong_password(self, client, seed_db):
        client.post(
            "/auth/register",
            data={"username": "wpuser", "password": "securepass123"},
        )
        response = client.post(
            "/auth/login",
            data={"username": "wpuser", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        body = response.json()
        assert body.get("detail") == "Invalid credentials"

    def test_login_nonexistent_user(self, client, seed_db):
        response = client.post(
            "/auth/login",
            data={"username": "ghostuser", "password": "securepass123"},
        )
        assert response.status_code == 401


class TestRefresh:
    def test_refresh_token_success(self, client, seed_db):
        client.post(
            "/auth/register",
            data={"username": "refreshuser", "password": "securepass123"},
        )
        login_resp = client.post(
            "/auth/login",
            data={"username": "refreshuser", "password": "securepass123"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        response = client.post(
            "/auth/refresh",
            params={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert "refresh_token" in body

    def test_refresh_revoked_token(self, client, seed_db):
        client.post(
            "/auth/register",
            data={"username": "revokeduser", "password": "securepass123"},
        )
        login_resp = client.post(
            "/auth/login",
            data={"username": "revokeduser", "password": "securepass123"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        client.post(
            "/auth/logout",
            params={"refresh_token": refresh_token},
        )

        response = client.post(
            "/auth/refresh",
            params={"refresh_token": refresh_token},
        )
        assert response.status_code == 401


class TestLogout:
    def test_logout_success(self, client, seed_db):
        client.post(
            "/auth/register",
            data={"username": "logoutuser", "password": "securepass123"},
        )
        login_resp = client.post(
            "/auth/login",
            data={"username": "logoutuser", "password": "securepass123"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        response = client.post(
            "/auth/logout",
            params={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert "logged out" in body["message"].lower()

    def test_logout_invalid_token(self, client, seed_db):
        response = client.post(
            "/auth/logout",
            params={"refresh_token": "invalid.token.here"},
        )
        assert response.status_code == 400
