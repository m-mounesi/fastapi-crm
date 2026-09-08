from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from core.database import Base
from datetime import datetime


class NoteDB(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)

    content: Mapped[str] = mapped_column(String, nullable=False)

    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=True)

    created_by: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    updated_at = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
