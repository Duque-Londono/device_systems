"""Operaciones CRUD persistentes para el recurso de usuarios."""

from typing import Optional

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.security import get_password_hash
from app.models.user_model import User
from app.schemas.user_schema import RoleEnum, UserCreate, UserPatch, UserUpdate


class DuplicateEmailError(ValueError):
    """El correo viola la restricción única de la tabla users."""


def get_all_users(
    db: Session,
    role: Optional[RoleEnum] = None,
    is_active: Optional[bool] = None,
    sort_by: str = "name",
    sort_order: str = "asc",
) -> list[User]:
    """Lista usuarios con filtros y ordenamiento ejecutados en SQLite."""
    statement: Select[tuple[User]] = select(User)

    if role is not None:
        statement = statement.where(User.role == role.value)
    if is_active is not None:
        statement = statement.where(User.is_active == is_active)

    column = User.name if sort_by == "name" else User.created_at
    statement = statement.order_by(column.desc() if sort_order == "desc" else column.asc())
    return list(db.scalars(statement).all())


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Busca un usuario por su clave primaria."""
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Busca un usuario por su correo (campo único e indexado)."""
    return db.scalar(select(User).where(User.email == email))


def create_user(db: Session, data: UserCreate) -> User:
    """Crea y confirma un usuario; traduce la restricción única a un error de negocio.

    La contraseña recibida en texto plano se almacena únicamente como hash bcrypt.
    """
    payload = data.model_dump()
    plain_password = payload.pop("password")
    user = User(**payload, hashed_password=get_password_hash(plain_password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise DuplicateEmailError("El correo electrónico ya está registrado") from error
    db.refresh(user)
    return user


def _commit_user(db: Session, user: User, duplicate_message: str) -> User:
    """Confirma cambios y conserva la sesión utilizable si falla la unicidad."""
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise DuplicateEmailError(duplicate_message) from error
    db.refresh(user)
    return user


def update_user_full(db: Session, user: User, data: UserUpdate) -> User:
    """Reemplaza todos los campos editables de un usuario existente."""
    for field, value in data.model_dump().items():
        setattr(user, field, value)
    return _commit_user(db, user, "El correo electrónico ya está registrado por otro usuario")


def update_user_partial(db: Session, user: User, data: UserPatch) -> User:
    """Actualiza solo los campos explícitamente enviados por el cliente."""
    changes = data.model_dump(exclude_unset=True)
    if not changes:
        raise ValueError("No se enviaron datos para actualizar")
    for field, value in changes.items():
        setattr(user, field, value)
    return _commit_user(db, user, "El correo electrónico ya está registrado por otro usuario")


def delete_user(db: Session, user: User) -> None:
    """Elimina un usuario existente y confirma la transacción."""
    db.delete(user)
    db.commit()
