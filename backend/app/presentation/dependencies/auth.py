"""
app/presentation/dependencies/auth.py
FastAPI Dependencies untuk autentikasi dan otorisasi berbasis Role (RBAC).
"""
import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.config import settings
from app.infrastructure.database.session import get_db
from app.domain.enums import Peran
from app.domain.entities.pengguna import Pengguna, Warga, Petugas

security_bearer = HTTPBearer(auto_error=True)


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    token_auth: Annotated[HTTPAuthorizationCredentials, Depends(security_bearer)],
) -> Pengguna:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Kredensial autentikasi tidak valid atau telah kedaluwarsa.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = token_auth.credentials

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id_str: str = payload.get("sub")
        token_type: str = payload.get("type")

        if user_id_str is None or token_type != "access":
            raise credentials_exception

        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    user = db.scalar(select(Pengguna).where(Pengguna.id == user_id))
    if not user:
        raise credentials_exception

    if not user.is_aktif:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun pengguna dinonaktifkan.",
        )

    return user


def require_role(allowed_roles: list[Peran]):
    def role_checker(
        current_user: Annotated[Pengguna, Depends(get_current_user)]
    ) -> Pengguna:
        if current_user.peran not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Akses ditolak. Dibutuhkan peran: {[r.value for r in allowed_roles]}.",
            )
        return current_user

    return role_checker


require_warga = require_role([Peran.WARGA])
require_petugas = require_role([Peran.PETUGAS])
