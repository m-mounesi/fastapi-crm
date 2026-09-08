from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class UserRoleDB(Base):
    __tablename__ = "user_roles"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True)

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), index=True)

    __table_args__ = (UniqueConstraint("user_id", "role_id"),)
