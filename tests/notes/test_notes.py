from security.jwt import create_access_token


class TestCreateNote:
    def test_create_note_success(self, client, auth_headers):
        response = client.post(
            "/notes/",
            json={"content": "Test note content"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "Test note content"
        assert data["created_by"] is not None
        assert data["id"] is not None

    def test_create_note_missing_content(self, client, auth_headers):
        response = client.post(
            "/notes/",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_create_note_with_customer_id(self, client, auth_headers, db_session):
        from app.modules.customers.models import CustomerDB

        customer = CustomerDB(name="Test Customer", created_by=1)
        db_session.add(customer)
        db_session.commit()
        db_session.refresh(customer)

        response = client.post(
            "/notes/",
            json={
                "content": "Note with customer",
                "customer_id": customer.id,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "Note with customer"
        assert data["customer_id"] == customer.id

    def test_create_note_with_project_id(self, client, auth_headers, db_session):
        from app.modules.projects.models import ProjectDB
        from app.modules.customers.models import CustomerDB

        customer = CustomerDB(name="Test Customer", created_by=1)
        db_session.add(customer)
        db_session.commit()
        db_session.refresh(customer)

        project = ProjectDB(title="Test Project", customer_id=customer.id, created_by=1)
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        response = client.post(
            "/notes/",
            json={
                "content": "Note with project",
                "project_id": project.id,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "Note with project"
        assert data["project_id"] == project.id

    def test_create_note_invalid_customer_id(self, client, auth_headers):
        response = client.post(
            "/notes/",
            json={
                "content": "Note with bad customer",
                "customer_id": 9999,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["customer_id"] == 9999


class TestReadNotes:
    def test_get_all_notes(self, client, auth_headers):
        client.post(
            "/notes/",
            json={"content": "Note 1"},
            headers=auth_headers,
        )
        client.post(
            "/notes/",
            json={"content": "Note 2"},
            headers=auth_headers,
        )

        response = client.get("/notes/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_notes_filter_by_ownership(self, client, auth_headers, db_session):
        from app.modules.users.repository import UserRepository
        from security.password import hash_password
        from app.modules.rbac.service import RBACService
        from app.modules.rbac.repository import RBACRepository

        repo = UserRepository()
        user_data = {
            "username": "note_owner",
            "password": hash_password("pass123"),
        }
        user2 = repo.create_user(db_session, user_data)

        rbac = RBACService(RBACRepository())
        rbac.assign_role(db_session, user2.user_id, "admin")

        token = create_access_token(
            {"sub": user2.username, "user_id": user2.user_id, "type": "access"}
        )
        user2_headers = {"Authorization": f"Bearer {token}"}

        client.post(
            "/notes/",
            json={"content": "Admin note"},
            headers=auth_headers,
        )
        client.post(
            "/notes/",
            json={"content": "User2 note"},
            headers=user2_headers,
        )

        response = client.get("/notes/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_note_by_id(self, client, auth_headers):
        create_resp = client.post(
            "/notes/",
            json={"content": "Fetchable note"},
            headers=auth_headers,
        )
        note_id = create_resp.json()["id"]

        response = client.get(f"/notes/{note_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Fetchable note"
        assert data["id"] == note_id

    def test_get_nonexistent_note(self, client, auth_headers):
        response = client.get("/notes/9999", headers=auth_headers)
        assert response.status_code == 404
        assert response.json()["error_type"] == "NoteNotFound"

    def test_get_other_users_note_denied(self, client, auth_headers, db_session):
        from app.modules.users.repository import UserRepository
        from security.password import hash_password
        from app.modules.rbac.service import RBACService
        from app.modules.rbac.repository import RBACRepository

        repo = UserRepository()
        user_data = {
            "username": "note_reader",
            "password": hash_password("pass123"),
        }
        user2 = repo.create_user(db_session, user_data)

        rbac = RBACService(RBACRepository())
        rbac.assign_role(db_session, user2.user_id, "viewer")

        token = create_access_token(
            {"sub": user2.username, "user_id": user2.user_id, "type": "access"}
        )
        user2_headers = {"Authorization": f"Bearer {token}"}

        create_resp = client.post(
            "/notes/",
            json={"content": "Owner only note"},
            headers=auth_headers,
        )
        note_id = create_resp.json()["id"]

        response = client.get(f"/notes/{note_id}", headers=user2_headers)
        assert response.status_code == 403
        assert response.json()["error_type"] == "PermissionDenied"


class TestOwnershipVisibility:
    def test_admin_sees_all_notes(self, client, auth_headers, db_session):
        from app.modules.users.repository import UserRepository
        from security.password import hash_password
        from app.modules.rbac.service import RBACService
        from app.modules.rbac.repository import RBACRepository

        repo = UserRepository()
        user_data = {
            "username": "note_worker",
            "password": hash_password("pass123"),
        }
        user2 = repo.create_user(db_session, user_data)

        rbac = RBACService(RBACRepository())
        rbac.assign_role(db_session, user2.user_id, "operator")
        rbac.assign_permission(db_session, "operator", "note.read")
        rbac.assign_permission(db_session, "operator", "note.create")

        token = create_access_token(
            {"sub": user2.username, "user_id": user2.user_id, "type": "access"}
        )
        user2_headers = {"Authorization": f"Bearer {token}"}

        client.post(
            "/notes/",
            json={"content": "User2 note"},
            headers=user2_headers,
        )
        client.post(
            "/notes/",
            json={"content": "Admin note"},
            headers=auth_headers,
        )

        response = client.get("/notes/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_nonadmin_sees_own_notes_only(self, client, auth_headers, db_session):
        from app.modules.users.repository import UserRepository
        from security.password import hash_password
        from app.modules.rbac.service import RBACService
        from app.modules.rbac.repository import RBACRepository

        repo = UserRepository()
        user_data = {
            "username": "note_viewer",
            "password": hash_password("pass123"),
        }
        user2 = repo.create_user(db_session, user_data)

        rbac = RBACService(RBACRepository())
        rbac.assign_role(db_session, user2.user_id, "operator")
        rbac.assign_permission(db_session, "operator", "note.read")
        rbac.assign_permission(db_session, "operator", "note.create")

        token = create_access_token(
            {"sub": user2.username, "user_id": user2.user_id, "type": "access"}
        )
        user2_headers = {"Authorization": f"Bearer {token}"}

        client.post(
            "/notes/",
            json={"content": "User2 note"},
            headers=user2_headers,
        )
        client.post(
            "/notes/",
            json={"content": "Admin note"},
            headers=auth_headers,
        )

        response = client.get("/notes/", headers=user2_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["content"] == "User2 note"


class TestUpdateNote:
    def test_update_note_success(self, client, auth_headers):
        create_resp = client.post(
            "/notes/",
            json={"content": "Original content"},
            headers=auth_headers,
        )
        note_id = create_resp.json()["id"]

        response = client.put(
            f"/notes/{note_id}",
            json={"content": "Updated content"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated content"

    def test_update_other_users_note_denied(self, client, auth_headers, db_session):
        from app.modules.users.repository import UserRepository
        from security.password import hash_password
        from app.modules.rbac.service import RBACService
        from app.modules.rbac.repository import RBACRepository

        repo = UserRepository()
        user_data = {
            "username": "note_updater",
            "password": hash_password("pass123"),
        }
        user2 = repo.create_user(db_session, user_data)

        rbac = RBACService(RBACRepository())
        rbac.assign_role(db_session, user2.user_id, "operator")

        token = create_access_token(
            {"sub": user2.username, "user_id": user2.user_id, "type": "access"}
        )
        user2_headers = {"Authorization": f"Bearer {token}"}

        create_resp = client.post(
            "/notes/",
            json={"content": "Owner only note"},
            headers=auth_headers,
        )
        note_id = create_resp.json()["id"]

        response = client.put(
            f"/notes/{note_id}",
            json={"content": "Hacked content"},
            headers=user2_headers,
        )
        assert response.status_code == 403
        assert response.json()["error_type"] == "PermissionDenied"

    def test_update_nonexistent_note(self, client, auth_headers):
        response = client.put(
            "/notes/9999",
            json={"content": "Ghost note"},
            headers=auth_headers,
        )
        assert response.status_code == 404
        assert response.json()["error_type"] == "NoteNotFound"


class TestDeleteNote:
    def test_delete_note_success(self, client, auth_headers):
        create_resp = client.post(
            "/notes/",
            json={"content": "To be deleted"},
            headers=auth_headers,
        )
        note_id = create_resp.json()["id"]

        delete_resp = client.delete(f"/notes/{note_id}", headers=auth_headers)
        assert delete_resp.status_code == 200
        data = delete_resp.json()
        assert data["message"] == "Note deleted successfully"

        get_resp = client.get(f"/notes/{note_id}", headers=auth_headers)
        assert get_resp.status_code == 404

    def test_delete_other_users_note_denied(self, client, auth_headers, db_session):
        from app.modules.users.repository import UserRepository
        from security.password import hash_password
        from app.modules.rbac.service import RBACService
        from app.modules.rbac.repository import RBACRepository

        repo = UserRepository()
        user_data = {
            "username": "note_deleter",
            "password": hash_password("pass123"),
        }
        user2 = repo.create_user(db_session, user_data)

        rbac = RBACService(RBACRepository())
        rbac.assign_role(db_session, user2.user_id, "operator")

        token = create_access_token(
            {"sub": user2.username, "user_id": user2.user_id, "type": "access"}
        )
        user2_headers = {"Authorization": f"Bearer {token}"}

        create_resp = client.post(
            "/notes/",
            json={"content": "Protected note"},
            headers=auth_headers,
        )
        note_id = create_resp.json()["id"]

        response = client.delete(f"/notes/{note_id}", headers=user2_headers)
        assert response.status_code == 403
        assert response.json()["error_type"] == "PermissionDenied"

    def test_delete_nonexistent_note(self, client, auth_headers):
        response = client.delete("/notes/9999", headers=auth_headers)
        assert response.status_code == 404
        assert response.json()["error_type"] == "NoteNotFound"


class TestRestoreNote:
    def test_restore_note_success(self, client, auth_headers):
        create_resp = client.post(
            "/notes/",
            json={"content": "To be restored"},
            headers=auth_headers,
        )
        note_id = create_resp.json()["id"]

        client.delete(f"/notes/{note_id}", headers=auth_headers)

        get_resp = client.get(f"/notes/{note_id}", headers=auth_headers)
        assert get_resp.status_code == 404

        restore_resp = client.post(f"/notes/{note_id}/restore", headers=auth_headers)
        assert restore_resp.status_code == 200

        get_resp = client.get(f"/notes/{note_id}", headers=auth_headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["content"] == "To be restored"


class TestNoteAuth:
    def test_unauthenticated_access_denied(self, client):
        response = client.get("/notes/")
        assert response.status_code == 401
