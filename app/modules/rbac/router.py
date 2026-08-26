from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from core.dependencies import get_rbac_service
from app.modules.rbac.service import RBACService
from security.dependencies import require_permission
from core.logger import get_logger
from schemas.schema import SuccessResponse

router = APIRouter(prefix="/admin/rbac", tags=["RBAC"])

logger = get_logger("admin_rbac")


# Assign Role to User
@router.post(
    "/users/{user_id}/roles",
    dependencies=[Depends(require_permission("user.manage"))],
)
def assign_role(
    user_id: int,
    role_name: str,
    service: RBACService = Depends(get_rbac_service),
    db: Session = Depends(get_db),
):
    logger.info(f"Assign role attempt: user_id={user_id}, role_name={role_name}")

    try:
        service.assign_role(db, user_id, role_name)
        logger.info(f"Role assigned successfully: user_id={user_id}, role={role_name}")
        return SuccessResponse(
            message="Role assigned successfully",
        )

    except Exception:
        logger.exception(f"Error assigning role: user_id={user_id}, role={role_name}")
        raise


# Assign Permission to Role
@router.post(
    "/roles/{role_name}/permissions",
    dependencies=[Depends(require_permission("user.manage"))],
)
def assign_permission(
    role_name: str,
    permission_name: str,
    db: Session = Depends(get_db),
    service: RBACService = Depends(get_rbac_service),
):
    logger.info(
        f"Assign permission attempt: role={role_name}, permission={permission_name}"
    )

    service.assign_permission(db, role_name, permission_name)

    logger.info(
        f"Permission assigned successfully: "
        f"role={role_name}, permission={permission_name}"
    )

    return SuccessResponse(
        message="Permission assigned successfully",
    )
