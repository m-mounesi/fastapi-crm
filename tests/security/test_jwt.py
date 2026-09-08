from datetime import timedelta, datetime, timezone

import pytest
from jose import jwt

from security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_EXPIRE_DAYS,
)
from core.exceptions import UnauthorizedException


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_DATA = {"sub": "testuser", "user_id": 42, "type": "access"}


def _make_token(payload: dict) -> str:
    """Encode an arbitrary payload with the project's secret/algorithm."""
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ===========================================================================
# create_access_token
# ===========================================================================


class TestCreateAccessToken:
    def test_returns_string(self):
        token = create_access_token(SAMPLE_DATA)
        assert isinstance(token, str)

    def test_contains_access_type(self):
        token = create_access_token(SAMPLE_DATA)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["type"] == "access"

    def test_preserves_sub(self):
        token = create_access_token(SAMPLE_DATA)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser"

    def test_preserves_user_id(self):
        token = create_access_token(SAMPLE_DATA)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["user_id"] == 42

    def test_expiration_is_present_and_future(self):
        token = create_access_token(SAMPLE_DATA)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        assert exp > datetime.now(timezone.utc)

    def test_default_expiration_matches_config(self):
        token = create_access_token(SAMPLE_DATA)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        expected_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        # Allow 5 seconds of clock drift
        assert abs((exp - now) - expected_delta) < timedelta(seconds=5)

    def test_custom_expires_delta(self):
        delta = timedelta(minutes=5)
        token = create_access_token(SAMPLE_DATA, expires_delta=delta)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        assert abs((exp - now) - delta) < timedelta(seconds=5)

    def test_decode_returns_original_payload(self):
        token = create_access_token(SAMPLE_DATA)
        payload = decode_access_token(token)
        assert payload["sub"] == "testuser"
        assert payload["user_id"] == 42
        assert payload["type"] == "access"


# ===========================================================================
# create_refresh_token
# ===========================================================================


class TestCreateRefreshToken:
    def test_returns_string(self):
        token = create_refresh_token(SAMPLE_DATA)
        assert isinstance(token, str)

    def test_contains_refresh_type(self):
        token = create_refresh_token(SAMPLE_DATA)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["type"] == "refresh"

    def test_preserves_sub(self):
        token = create_refresh_token(SAMPLE_DATA)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser"

    def test_preserves_user_id(self):
        token = create_refresh_token(SAMPLE_DATA)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["user_id"] == 42

    def test_expiration_is_present_and_future(self):
        token = create_refresh_token(SAMPLE_DATA)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        assert exp > datetime.now(timezone.utc)

    def test_default_expiration_matches_config(self):
        token = create_refresh_token(SAMPLE_DATA)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        expected_delta = timedelta(days=REFRESH_EXPIRE_DAYS)
        assert abs((exp - now) - expected_delta) < timedelta(seconds=5)

    def test_expires_delta_parameter_is_ignored(self):
        """create_refresh_token accepts expires_delta but ignores it."""
        short_delta = timedelta(seconds=1)
        token = create_refresh_token(SAMPLE_DATA, expires_delta=short_delta)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        # Expiration should be ~REFRESH_EXPIRE_DAYS, NOT 1 second
        assert (exp - now) > timedelta(hours=1)

    def test_jti_claim_is_unique_string(self):
        """Refresh tokens include a unique jti claim."""
        token = create_refresh_token(SAMPLE_DATA)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "jti" in payload
        assert isinstance(payload["jti"], str)
        assert len(payload["jti"]) > 0


# ===========================================================================
# Refresh-token collision bug
# ===========================================================================


class TestRefreshTokenCollision:
    def test_two_tokens_for_same_user_are_different(self):
        """After the jti fix, two refresh tokens for the same user must differ."""
        data = {"sub": "user1", "user_id": 10}
        token1 = create_refresh_token(data)
        token2 = create_refresh_token(data)
        assert token1 != token2

    def test_jti_is_different_each_time(self):
        """Each refresh token gets a unique jti."""
        data = {"sub": "user1", "user_id": 10}
        payload1 = jwt.decode(
            create_refresh_token(data), SECRET_KEY, algorithms=[ALGORITHM]
        )
        payload2 = jwt.decode(
            create_refresh_token(data), SECRET_KEY, algorithms=[ALGORITHM]
        )
        assert payload1["jti"] != payload2["jti"]


# ===========================================================================
# decode_access_token
# ===========================================================================


class TestDecodeAccessToken:
    def test_valid_token(self):
        token = create_access_token(SAMPLE_DATA)
        payload = decode_access_token(token)
        assert payload["sub"] == "testuser"

    def test_malformed_token_raises_unauthorized(self):
        with pytest.raises(UnauthorizedException, match="Token verification failed"):
            decode_access_token("not.a.valid.jwt")

    def test_empty_string_raises_unauthorized(self):
        with pytest.raises(UnauthorizedException, match="Token verification failed"):
            decode_access_token("")

    def test_tampered_signature_raises_unauthorized(self):
        token = create_access_token(SAMPLE_DATA)
        # Flip a character in the signature portion
        parts = token.rsplit(".", 1)
        tampered_sig = "A" + parts[1][1:]
        tampered = parts[0] + "." + tampered_sig
        with pytest.raises(UnauthorizedException, match="Token verification failed"):
            decode_access_token(tampered)

    def test_expired_token_raises_unauthorized(self):
        data = {**SAMPLE_DATA, "exp": datetime.now(timezone.utc) - timedelta(hours=1)}
        token = _make_token(data)
        with pytest.raises(UnauthorizedException, match="Token verification failed"):
            decode_access_token(token)

    def test_token_signed_with_wrong_secret_raises_unauthorized(self):
        token = jwt.encode(SAMPLE_DATA, "wrong-secret", algorithm=ALGORITHM)
        with pytest.raises(UnauthorizedException, match="Token verification failed"):
            decode_access_token(token)

    def test_refresh_token_can_be_decoded_as_access(self):
        """decode_access_token does not check the 'type' claim."""
        refresh = create_refresh_token(SAMPLE_DATA)
        payload = decode_access_token(refresh)
        assert payload["type"] == "refresh"


# ===========================================================================
# decode_refresh_token
# ===========================================================================


class TestDecodeRefreshToken:
    def test_valid_refresh_token(self):
        token = create_refresh_token(SAMPLE_DATA)
        payload = decode_refresh_token(token)
        assert payload["sub"] == "testuser"
        assert payload["type"] == "refresh"

    def test_access_token_rejected_as_refresh(self):
        """decode_refresh_token rejects tokens with type != 'refresh'."""
        token = create_access_token(SAMPLE_DATA)
        with pytest.raises(UnauthorizedException, match="Invalid token type"):
            decode_refresh_token(token)

    def test_malformed_token_raises_unauthorized(self):
        with pytest.raises(UnauthorizedException, match="Token verification failed"):
            decode_refresh_token("garbage.token.value")

    def test_tampered_signature_raises_unauthorized(self):
        token = create_refresh_token(SAMPLE_DATA)
        parts = token.rsplit(".", 1)
        tampered_sig = "B" + parts[1][1:]
        tampered = parts[0] + "." + tampered_sig
        with pytest.raises(UnauthorizedException, match="Token verification failed"):
            decode_refresh_token(tampered)

    def test_expired_refresh_token_raises_unauthorized(self):
        data = {
            "sub": "testuser",
            "user_id": 42,
            "type": "refresh",
            "exp": datetime.now(timezone.utc) - timedelta(days=1),
        }
        token = _make_token(data)
        with pytest.raises(UnauthorizedException, match="Token verification failed"):
            decode_refresh_token(token)

    def test_token_signed_with_wrong_secret_raises_unauthorized(self):
        data = {**SAMPLE_DATA, "type": "refresh"}
        token = jwt.encode(data, "wrong-secret", algorithm=ALGORITHM)
        with pytest.raises(UnauthorizedException, match="Token verification failed"):
            decode_refresh_token(token)
