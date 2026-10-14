"""
app/core/security.py
Utilitas keamanan: hashing kata sandi native menggunakan bcrypt
dan manajemen JSON Web Token (python-jose).
Bebas dari bug inkompatibilitas passlib vs bcrypt 4.x/5.x (KNF-03).
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def hash_kata_sandi(kata_sandi: str) -> str:
    """Mengenkripsi kata sandi menggunakan algoritma bcrypt native."""
    pwd_bytes = kata_sandi.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


# Alias untuk kemudahan integrasi
get_password_hash = hash_kata_sandi


def verifikasi_kata_sandi(kata_sandi_plain: str, kata_sandi_hash: str) -> bool:
    """Memvalidasi kecocokan kata sandi plain terhadap hash bcrypt."""
    try:
        plain_bytes = kata_sandi_plain.encode("utf-8")
        hash_bytes = kata_sandi_hash.encode("utf-8")
        return bcrypt.checkpw(plain_bytes, hash_bytes)
    except Exception:
        return False


def buat_access_token(
    subyek: Union[str, Any],
    peran: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Membuat JWT Access Token.
    `subyek` biasanya adalah UUID pengguna dalam bentuk string.
    """
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
    """
    Membuat JWT Refresh Token yang disimpan ke tabel TokenSesi.
    Mengembalikan tuple (token_string, waktu_kedaluwarsa).
    """
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
    """
    Membuat JWT khusus untuk pemulihan/reset kata sandi (default masa berlaku: 15 menit).
    """
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
    """
    Memvalidasi token pemulihan kata sandi. Mengembalikan user_id (string) jika sah,
    atau None jika tidak sah/kedaluwarsa.
    """
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
    """
    Membuat JWT untuk verifikasi alamat email pengguna (default masa berlaku: 24 jam).
    """
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
    """
    Memvalidasi token verifikasi email. Mengembalikan dict payload {'sub': user_id, 'email': email}
    jika sah dan belum kedaluwarsa, atau None jika tidak sah.
    """
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
