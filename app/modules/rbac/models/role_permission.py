from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class RolePermissionDB(Base):
    __tablename__ = "role_permissions"

    id: Mapped[int] = mapped_column(primary_key=True)

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), index=True)

    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id"), index=True)

    __table_args__ = (UniqueConstraint("role_id", "permission_id"),)
