"""
app/infrastructure/security/jwt_handler.py
Manajemen token JWT (access, refresh, reset password, verifikasi email).
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union

from jose import JWTError, jwt

from app.infrastructure.config import settings


def buat_access_token(
    subyek: Union[str, Any],
    peran: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(subyek),
        "peran": peran,
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def buat_refresh_token(
    subyek: Union[str, Any],
    peran: str,
    expires_delta: Optional[timedelta] = None,
) -> tuple[str, datetime]:
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": str(subyek),
        "peran": peran,
        "iat": now,
        "exp": expire,
        "type": "refresh",
    }
    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt, expire


def buat_reset_password_token(subyek: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta if expires_delta else timedelta(minutes=15))
    payload = {
        "sub": str(subyek),
        "iat": now,
        "exp": expire,
        "type": "reset_password",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verifikasi_reset_password_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "reset_password":
            return None
        return payload.get("sub")
    except (JWTError, ValueError):
        return None


def buat_verifikasi_email_token(
    subyek: Union[str, Any],
    email: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta if expires_delta else timedelta(hours=24))
    payload = {
        "sub": str(subyek),
        "email": email,
        "iat": now,
        "exp": expire,
        "type": "verify_email",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verifikasi_token_email(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "verify_email":
            return None
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
        }
    except (JWTError, ValueError):
        return None
