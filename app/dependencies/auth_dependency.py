"""Dependencias de autenticación y autorización basadas en OAuth2 + JWT."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.auth.security import decode_access_token
from app.dependencies.database_dependency import DbSession
from app.models.user_model import User
from app.schemas.user_schema import RoleEnum
from app.services import user_service

# Esquema OAuth2: Swagger mostrará el botón "Authorize" y enviará el token en
# la cabecera Authorization: Bearer <token>. tokenUrl apunta al endpoint de login.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Excepción reutilizable para credenciales inválidas (401).
_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="No se pudieron validar las credenciales",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DbSession,
) -> User:
    """Resuelve el usuario autenticado a partir del token JWT.

    Responde 401 si el token es inválido, ha expirado o el usuario no existe.
    """
    payload = decode_access_token(token)
    if payload is None:
        raise _credentials_exception

    email = payload.get("sub")
    if not email:
        raise _credentials_exception

    user = user_service.get_user_by_email(db, email)
    if user is None:
        raise _credentials_exception
    return user


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Garantiza que el usuario autenticado esté activo (401 si está inactivo)."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo",
        )
    return current_user


def require_roles(*allowed_roles: RoleEnum):
    """Fábrica de dependencias: exige que el usuario tenga uno de los roles dados.

    Responde 403 Forbidden si el rol del usuario no está autorizado.
    """
    allowed = {role.value for role in allowed_roles}

    def _checker(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para realizar esta operación",
            )
        return current_user

    return _checker


# Dependencia específica para rutas exclusivas de administradores.
require_admin = require_roles(RoleEnum.admin)

# Tipos anotados reutilizables.
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]
