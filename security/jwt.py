from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import jwt, JWTError
from core.config import settings
from core.exceptions import UnauthorizedException
from core.logger import get_logger


logger = get_logger("jwt")

# CONFIG
# =========================
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_EXPIRE_DAYS = settings.REFRESH_EXPIRE_DAYS


# CREATE JWT TOKEN  ( ACCESS TOKEN )
# =========================
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    logger.info("Creating access token for user_id=%s", data.get("user_id"))
    payload = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload["type"] = "access"
    payload.update({"exp": expire})

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    logger.info(f"Access token created for user_id: {data.get('user_id')}")
    return token


# CREATE JWT TOKEN  ( REFRESH TOKEN )
# =========================
def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    payload = data.copy()

    payload["type"] = "refresh"
    payload["jti"] = str(uuid4())
    payload["exp"] = datetime.now(timezone.utc) + timedelta(days=REFRESH_EXPIRE_DAYS)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# DECODE / VERIFY TOKEN
# =========================
def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info(f"Token decoded successfully for user_id: {payload.get('user_id')}")
        return payload
    except JWTError as e:
        raise UnauthorizedException(f"Token verification failed: {str(e)}")


# DECODE / VERIFY REFRESH TOKEN
# =========================
def decode_refresh_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            logger.warning("Invalid token type for refresh token")
            raise UnauthorizedException("Invalid token type")

        logger.info(
            f"Refresh token decoded successfully for user_id: {payload.get('user_id')}"
        )
        return payload

    except JWTError as e:
        logger.warning(f"Refresh token verification failed: {str(e)}")
        raise UnauthorizedException(f"Token verification failed: {str(e)}")
