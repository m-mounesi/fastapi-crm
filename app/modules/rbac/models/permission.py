from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.rbac.models.role import RoleDB


class PermissionDB(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    roles: Mapped[list["RoleDB"]] = relationship(
        secondary="role_permissions", back_populates="permissions"
    )
