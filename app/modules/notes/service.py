from core.exceptions import (
    CustomerNotFoundException,
    NoteNotFoundException,
    PermissionDeniedException,
    ProjectNotFoundException,
)
from app.modules.users.models import UserDB
from app.modules.notes.models import NoteDB
from app.modules.notes.repository import NoteRepository
from app.modules.customers.repository import CustomerRepository
from app.modules.projects.repository import ProjectRepository


class NoteService:
    def __init__(
        self,
        repo: NoteRepository,
        customer_repo: CustomerRepository,
        project_repo: ProjectRepository,
    ):
        self.repo = repo
        self.customer_repo = customer_repo
        self.project_repo = project_repo

    # CREATE
    def create_note(self, db, data, user_id: int):
        if data.customer_id is not None:
            if not self.customer_repo.get_by_id(db, data.customer_id):
                raise CustomerNotFoundException("Customer not found")

        if data.project_id is not None:
            if not self.project_repo.get_by_id(db, data.project_id):
                raise ProjectNotFoundException("Project not found")

        note = NoteDB(
            content=data.content,
            customer_id=data.customer_id,
            project_id=data.project_id,
            created_by=user_id,
        )

        return self.repo.create(db, note)

    # GET ONE
    def get_note(self, db, note_id: int, user_id: int):
        note: NoteDB = self.repo.get_by_id(db, note_id)

        if not note:
            raise NoteNotFoundException("Note not found by this id")

        if note.created_by != user_id:
            raise PermissionDeniedException("Permission Denied!")

        return note

    # GET ALL
    def get_notes(self, db, user: UserDB, skip: int = 0, limit: int = 10):
        return self.repo.get_all(
            db,
            user_id=user.user_id,
            is_admin=any(role.name == "admin" for role in user.roles),
            skip=skip,
            limit=limit,
        )

    # UPDATE
    def update_note(self, db, note_id: int, data, user_id: int):
        note = self.repo.get_by_id(db, note_id)

        if not note:
            raise NoteNotFoundException("Note not found by this id")

        if note.created_by != user_id:
            raise PermissionDeniedException("Permission Denied!")

        if data.content is not None:
            note.content = data.content

        if data.customer_id is not None:
            if not self.customer_repo.get_by_id(db, data.customer_id):
                raise CustomerNotFoundException("Customer not found")
            note.customer_id = data.customer_id

        if data.project_id is not None:
            if not self.project_repo.get_by_id(db, data.project_id):
                raise ProjectNotFoundException("Project not found")
            note.project_id = data.project_id

        return self.repo.update(db, note)

    # DELETE
    def delete_note(self, db, note_id: int, user_id: int):
        note = self.repo.get_by_id(db, note_id)

        if not note:
            raise NoteNotFoundException("Note not found by this id")

        if note.created_by != user_id:
            raise PermissionDeniedException("Permission Denied!")

        self.repo.delete(db, note)
        return True

    # RESTORE
    def restore_note(self, db, note_id, user: UserDB):
        is_admin = any(role.name == "admin" for role in user.roles)

        return self.repo.restore(db, note_id, user.user_id, is_admin)
