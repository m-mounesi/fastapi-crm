from fastapi import HTTPException

from core.exceptions import NoteNotFoundException, PermissionDeniedException
from app.modules.users.models import UserDB
from app.modules.notes.models import NoteDB
from app.modules.notes.repository import NoteRepository


class NoteService:
    def __init__(self, repo: NoteRepository):
        self.repo = repo

    # CREATE
    def create_note(self, db, data, user_id: int):
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
            return None

        if note.created_by != user_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to access this note"
            )

        if data.content is not None:
            note.content = data.content

        if data.customer_id is not None:
            note.customer_id = data.customer_id

        if data.project_id is not None:
            note.project_id = data.project_id

        return self.repo.update(db, note)

    # DELETE
    def delete_note(self, db, note_id: int, user_id: int):
        note = self.repo.get_by_id(db, note_id)

        if not note:
            return None

        if note.created_by != user_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to access this note"
            )

        self.repo.delete(db, note)
        return True

    # RESTORE
    def restore_note(self, db, note_id, user: UserDB):
        is_admin = any(role.name == "admin" for role in user.roles)

        return self.repo.restore(db, note_id, user.user_id, is_admin)
