"""Lógica de negocio de autenticación: registro y verificación de credenciales."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.security import get_password_hash, verify_password
from app.models.user_model import User
from app.schemas.auth_schema import UserRegister
from app.services import user_service
from app.services.user_service import DuplicateEmailError


def register_user(db: Session, data: UserRegister) -> User:
    """Crea un usuario con contraseña hasheada.

    Lanza :class:`DuplicateEmailError` si el correo ya está registrado.
    """
    # Comprobación temprana para un mensaje de negocio claro.
    if user_service.get_user_by_email(db, data.email) is not None:
        raise DuplicateEmailError("El correo electrónico ya está registrado")

    user = User(
        name=data.name,
        email=data.email,
        role=data.role.value,
        is_active=True,
        hashed_password=get_password_hash(data.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as error:
        # Cubre la condición de carrera si dos registros usan el mismo correo.
        db.rollback()
        raise DuplicateEmailError("El correo electrónico ya está registrado") from error
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Devuelve el usuario si las credenciales son válidas; ``None`` si no lo son."""
    user = user_service.get_user_by_email(db, email)
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
