from sqlalchemy.orm import Session
from sqlalchemy import select

from app.modules.rbac.models.user_role import UserRoleDB
from app.modules.rbac.models.role_permission import RolePermissionDB
from app.modules.rbac.models.role import RoleDB
from app.modules.rbac.models.permission import PermissionDB


class RBACRepository:
    def get_user_roles(self, db, user_id: int):
        stmt = select(RoleDB.name).join(UserRoleDB).where(UserRoleDB.user_id == user_id)
        return db.execute(stmt).scalars().all()

    def get_user_permissions(self, db, user_id: int):
        stmt = (
            select(PermissionDB.name)
            .join(RolePermissionDB)
            .join(RoleDB)
            .join(UserRoleDB)
            .where(UserRoleDB.user_id == user_id)
        )
        return db.execute(stmt).scalars().all()

    def get_role_by_name(self, db: Session, name: str):
        stmt = select(RoleDB).where(RoleDB.name == name)
        return db.execute(stmt).scalar_one_or_none()

    def get_permission_by_name(self, db, name):
        stmt = select(PermissionDB).where(PermissionDB.name == name)
        return db.execute(stmt).scalar_one_or_none()

    def assign_role_to_user(self, db, user_id, role_id):
        obj = UserRoleDB(user_id=user_id, role_id=role_id)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def user_has_role(self, db, user_id, role_id):
        stmt = select(UserRoleDB).where(
            UserRoleDB.user_id == user_id, UserRoleDB.role_id == role_id
        )
        return db.execute(stmt).scalar_one_or_none()

    def role_has_permission(self, db, role_id, permission_id):
        stmt = select(RolePermissionDB).where(
            RolePermissionDB.role_id == role_id,
            RolePermissionDB.permission_id == permission_id,
        )
        return db.execute(stmt).scalar_one_or_none()

    def assign_permission_to_role(self, db, role_id, permission_id):
        obj = RolePermissionDB(role_id=role_id, permission_id=permission_id)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj
