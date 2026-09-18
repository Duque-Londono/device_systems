"""Utilidades de seguridad: hashing de contraseñas y tokens JWT.

- Las contraseñas se almacenan como hash bcrypt mediante passlib; nunca en texto
  plano.
- Los tokens de acceso son JWT firmados con la clave y el algoritmo definidos en
  la configuración (``app.config.settings``).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# Contexto de passlib configurado con bcrypt.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Devuelve el hash bcrypt de una contraseña en texto plano."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica que una contraseña en texto plano corresponda a su hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Genera un JWT firmado a partir de un diccionario de datos (claims).

    Añade automáticamente la marca de expiración ``exp``.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """Decodifica y valida un JWT.

    Retorna el payload si el token es válido y no ha expirado; ``None`` en caso
    contrario (firma inválida, expirado o malformado).
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
