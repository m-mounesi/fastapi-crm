from app.modules.users.models import UserDB
from app.modules.rbac.models.role import RoleDB
from app.modules.rbac.models.user_role import UserRoleDB
from core.config import settings
from security.password import hash_password


def create_admin(db):
    admin = db.query(UserDB).filter(UserDB.username == settings.ADMIN_USERNAME).first()

    if admin:
        return admin

    admin = UserDB(
        username=settings.ADMIN_USERNAME,
        hashed_password=hash_password(settings.ADMIN_PASSWORD),
    )

    db.add(admin)
    db.commit()
    db.refresh(admin)

    admin_role = db.query(RoleDB).filter(RoleDB.name == "admin").first()

    db.add(UserRoleDB(user_id=admin.user_id, role_id=admin_role.id))

    db.commit()

    return admin
