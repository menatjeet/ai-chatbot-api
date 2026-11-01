from datetime import datetime, timedelta, timezone
import jwt
import pytest

from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token


def test_password_hashing():
    raw_password = "MySuperSecretPassword123!"
    hashed = hash_password(raw_password)

    assert hashed != raw_password
    assert hashed.startswith("$argon2")

    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_token_generation():
    user_id = 42
    token = create_access_token(user_id)

    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm]
    )

    assert payload["sub"] == str(user_id)
    assert "exp" in payload


def test_expired_token_rejection():
    # Create expired token
    expired_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    payload = {
        "sub": "42",
        "exp": expired_time
    }
    expired_token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(
            expired_token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
