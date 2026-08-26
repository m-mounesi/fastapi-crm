from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, func
from core.database import Base


class RefreshTokenDB(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)

    # connection to user
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)

    # the token itself
    token = Column(String, unique=True, index=True, nullable=False)

    # status of validity
    is_revoked = Column(Boolean, default=False)

    # expiration time
    expires_at = Column(DateTime, nullable=False)

    # creation time
    created_at = Column(DateTime(timezone=True), server_default=func.now())
