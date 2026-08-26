from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.role import RoleDB


class UserDB(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )

    hashed_password: Mapped[str] = mapped_column(nullable=False)

    created_at = mapped_column(DateTime, server_default=func.now(), index=True)
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    roles: Mapped[list["RoleDB"]] = relationship(
        secondary="user_roles", back_populates="users"
    )
