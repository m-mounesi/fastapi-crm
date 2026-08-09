from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from repositories.rbac_repository import RBACRepository
from security.auth import get_current_user
from core.exceptions import PermissionDeniedException
from core.dependencies import get_rbac_repository


def require_permission(permission: str):
    def permission_checker(
        current_user=Depends(get_current_user),
        db: Session = Depends(get_db),
        repo: RBACRepository = Depends(get_rbac_repository),
    ):
        permission_names = repo.get_user_permissions(db, current_user.user_id)

        if permission not in permission_names:
            raise PermissionDeniedException(
                "You do not have permission to perform this action."
            )

        return current_user

    return permission_checker
