from datetime import datetime, timezone

from core.exceptions import PermissionDeniedException, ProjectNotFoundException
from app.modules.projects.models import ProjectDB


class ProjectRepository:
    def create(self, db, project: ProjectDB):
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    def get_by_id(self, db, project_id: int):
        return (
            db.query(ProjectDB)
            .filter(ProjectDB.id == project_id, ProjectDB.deleted_at.is_(None))
            .first()
        )

    def get_all(self, db, user_id: int, is_admin: bool):
        query = db.query(ProjectDB).filter(ProjectDB.deleted_at.is_(None))

        if not is_admin:
            query = query.filter(ProjectDB.created_by == user_id)

        return query.all()

    def update(self, db, project: ProjectDB):
        db.commit()
        db.refresh(project)
        return project

    def delete(self, db, project: ProjectDB):
        project.deleted_at = datetime.now(timezone.utc)
        db.commit()

    def restore(self, db, project_id: int, user_id, is_admin: bool):
        project: ProjectDB = (
            db.query(ProjectDB).filter(ProjectDB.id == project_id).first()
        )

        if not project:
            raise ProjectNotFoundException("project not found")

        if not is_admin and project.created_by != user_id:
            raise PermissionDeniedException("You cannot restore this project.")

        project.deleted_at = None
        db.commit()
        db.refresh(project)

        return project
