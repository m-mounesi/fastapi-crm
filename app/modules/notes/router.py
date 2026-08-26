from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_note_service
from app.modules.users.models import UserDB
from app.modules.notes.service import NoteService
from app.modules.notes.schemas import NoteCreate, NoteUpdate, NoteResponse
from schemas.schema import SuccessResponse
from security.dependencies import require_permission

router = APIRouter(prefix="/notes", tags=["notes"])


# CREATE Note
@router.post("/", response_model=NoteResponse)
def create_note(
    data: NoteCreate,
    service: NoteService = Depends(get_note_service),
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(require_permission("note.create")),
):
    return service.create_note(db, data, current_user.user_id)


# GET ALL
@router.get("/", response_model=list[NoteResponse])
def get_notes(
    skip: int = 0,
    limit: int = 10,
    service: NoteService = Depends(get_note_service),
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(require_permission("note.read")),
):
    return service.get_notes(db, current_user, skip, limit)


# GET BY ID
@router.get("/{note_id}", response_model=NoteResponse)
def get_note(
    note_id: int,
    service: NoteService = Depends(get_note_service),
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(require_permission("note.read")),
):
    note = service.get_note(db, note_id, current_user.user_id)

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return note


# UPDATE
@router.put("/{note_id}", response_model=NoteResponse)
def update_note(
    note_id: int,
    data: NoteUpdate,
    service: NoteService = Depends(get_note_service),
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(require_permission("note.update")),
):
    note = service.update_note(db, note_id, data, current_user.user_id)

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return note


# DELETE
@router.delete("/{note_id}")
def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    service: NoteService = Depends(get_note_service),
    current_user: UserDB = Depends(require_permission("note.delete")),
):
    result = service.delete_note(db, note_id, current_user.user_id)

    if not result:
        raise HTTPException(status_code=404, detail="Note not found")

    return SuccessResponse(
        message="Note deleted successfully", data=f"Deleted Note : {note_id} "
    )


# Restore
@router.post("/{note_id}/restore")
def restore_note(
    note_id: int,
    db: Session = Depends(get_db),
    service: NoteService = Depends(get_note_service),
    current_user: UserDB = Depends(require_permission("note.restore")),
):
    note = service.restore_note(db, note_id, current_user)

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return SuccessResponse(
        message="Note restored successfully", data=f"note : {note.content[:30]}... "
    )
