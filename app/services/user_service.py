from typing import List, Optional

from app.data.users_db import fake_users_db
from app.schemas.user_schema import RoleEnum, UserCreate, UserPatch, UserUpdate


def get_all_users(role: Optional[RoleEnum] = None, is_active: Optional[bool] = None) -> List[dict]:
    """Lista usuarios aplicando filtros opcionales de rol y estado."""
    filtered_users = fake_users_db

    if role is not None:
        filtered_users = [user for user in filtered_users if user["role"] == role]

    if is_active is not None:
        filtered_users = [user for user in filtered_users if user["is_active"] == is_active]

    return filtered_users


def get_user_by_id(user_id: int) -> Optional[dict]:
    """Busca un usuario por su ID. Retorna None si no existe."""
    return next((user for user in fake_users_db if user["id"] == user_id), None)


def email_exists(email: str) -> bool:
    """Verifica si un correo ya está registrado."""
    return any(user["email"] == email for user in fake_users_db)


def create_user(user: UserCreate) -> dict:
    """Registra un nuevo usuario con ID autogenerado.

    Lanza ValueError si el correo ya existe (error de negocio,
    la capa de rutas lo traduce a HTTP 400).
    """
    if email_exists(user.email):
        raise ValueError("El correo electrónico ya está registrado")

    new_id = max(u["id"] for u in fake_users_db) + 1 if fake_users_db else 1

    new_user = user.model_dump()
    new_user["id"] = new_id
    fake_users_db.append(new_user)

    return new_user


def email_exists_for_other(email: str, exclude_id: int) -> bool:
    """Verifica si un correo está en uso por otro usuario distinto a exclude_id."""
    return any(
        user["email"] == email and user["id"] != exclude_id
        for user in fake_users_db
    )


def _get_or_raise(user_id: int) -> dict:
    """Obtiene el usuario o lanza LookupError (defensa en profundidad;
    normalmente la ruta ya garantizó la existencia con UserDep)."""
    user = get_user_by_id(user_id)
    if user is None:
        raise LookupError("Usuario no encontrado")
    return user


def update_user_full(user_id: int, data: UserUpdate) -> dict:
    """Reemplazo completo (PUT): sobrescribe todos los campos editables.

    Lanza ValueError si el correo ya pertenece a otro usuario.
    """
    user = _get_or_raise(user_id)

    if email_exists_for_other(data.email, user_id):
        raise ValueError("El correo electrónico ya está registrado por otro usuario")

    user.update(data.model_dump())
    return user


def update_user_partial(user_id: int, data: UserPatch) -> dict:
    """Actualización parcial (PATCH): solo modifica los campos enviados.

    Lanza ValueError si no se envió ningún campo o si el nuevo correo
    ya pertenece a otro usuario.
    """
    user = _get_or_raise(user_id)

    # exclude_unset: solo los campos que el cliente envió realmente
    changes = data.model_dump(exclude_unset=True)
    if not changes:
        raise ValueError("No se enviaron datos para actualizar")

    if "email" in changes and email_exists_for_other(changes["email"], user_id):
        raise ValueError("El correo electrónico ya está registrado por otro usuario")

    user.update(changes)
    return user


def delete_user(user_id: int) -> None:
    """Elimina un usuario de la base de datos simulada."""
    user = _get_or_raise(user_id)
    fake_users_db.remove(user)
