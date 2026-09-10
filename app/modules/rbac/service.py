from core.exceptions import PermissionNotFoundException, RoleNotFoundException
from app.modules.rbac.repository import RBACRepository
from app.modules.rbac.models.user_role import UserRoleDB
from core.logger import get_logger

logger = get_logger("rbac-service")


class RBACService:
    def __init__(self, repo: RBACRepository):
        self.repo = repo

    def build_user_context(self, db, user_id: int):
        logger.info(f"Building RBAC context for user_id={user_id}")

        roles = self.repo.get_user_roles(db, user_id)
        permissions = self.repo.get_user_permissions(db, user_id)

        logger.info(
            f"RBAC context built: user_id={user_id}, "
            f"roles={roles}, permissions_count={len(permissions)}"
        )

        return {"roles": roles, "permissions": permissions}

    def assign_role(self, db, user_id: int, role_name: str):
        logger.info(f"Assign role attempt: user_id={user_id}, role={role_name}")

        role = self.repo.get_role_by_name(db, role_name)

        if not role:
            logger.warning(f"Role not found: role={role_name}")
            raise RoleNotFoundException(f"Role '{role_name}' does not exist")

        exists = self.repo.user_has_role(db, user_id, role.id)

        if exists:
            logger.info(f"User already has role: user_id={user_id}, role={role_name}")
            return exists

        user_role = UserRoleDB(user_id=user_id, role_id=role.id)

        db.add(user_role)
        db.commit()

        logger.info(f"Role assigned successfully: user_id={user_id}, role={role_name}")

        return user_role

    def assign_permission(self, db, role_name: str, permission_name: str):
        logger.info(
            f"Assign permission attempt: role={role_name}, permission={permission_name}"
        )

        role = self.repo.get_role_by_name(db, role_name)
        permission = self.repo.get_permission_by_name(db, permission_name)

        if not role:
            logger.info(f"Role not found: {role_name}")
            raise RoleNotFoundException(f"Role '{role_name}' does not exist")

        if not permission:
            logger.info(f"Permission not found: {permission_name}")
            raise PermissionNotFoundException(
                f"Permission '{permission_name}' does not exist"
            )

        exists = self.repo.role_has_permission(db, role.id, permission.id)

        if exists:
            logger.info(
                f"Role already has permission: "
                f"role={role_name}, permission={permission_name}"
            )
            return exists

        logger.info(f"Fetched role: {role_name}, permission: {permission_name}")
        result = self.repo.assign_permission_to_role(db, role.id, permission.id)

        logger.info(
            f"Permission assigned successfully: "
            f"role={role_name}, permission={permission_name}"
        )

        return result
