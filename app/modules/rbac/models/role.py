from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.users.models import UserDB
    from app.modules.rbac.models.permission import PermissionDB


class RoleDB(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    users: Mapped[list["UserDB"]] = relationship(
        secondary="user_roles", back_populates="roles"
    )

    permissions: Mapped[list["PermissionDB"]] = relationship(
        secondary="role_permissions", back_populates="roles"
    )
