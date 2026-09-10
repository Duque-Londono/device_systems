from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, Query, status
from app.dependencies.database_dependency import DbSession
from app.models.user_model import User
from app.schemas.user_schema import RoleEnum
from app.services import user_service

# Llave válida para la autenticación simulada (Fase 7)
VALID_API_KEY = "device-systems-2026"


def user_filters(
    role: Optional[RoleEnum] = Query(None, description="Filtrar por rol (admin, support, user)"),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado (true o false)"),
    sort_by: str = Query("name", pattern="^(name|created_at)$", description="Campo de ordenamiento"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Dirección del ordenamiento"),
) -> dict:
    """Dependencia reutilizable: agrupa los query params de filtrado."""
    return {"role": role, "is_active": is_active, "sort_by": sort_by, "sort_order": sort_order}


def get_existing_user(user_id: int, db: DbSession) -> User:
    """Dependencia reutilizable: resuelve el usuario por ID o lanza 404."""
    user = user_service.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return user


def verify_api_key(x_api_key: Annotated[Optional[str], Header()] = None) -> str:
    """Dependencia de seguridad simulada: verifica el encabezado X-API-Key.

    - 401 Unauthorized si el encabezado no se envía.
    - 403 Forbidden si la llave no es válida.
    """
    if x_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta el encabezado X-API-Key",
        )
    if x_api_key != VALID_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key inválida",
        )
    return "cliente autorizado"


def get_api_config() -> dict:
    """Dependencia de configuración general: expone metadatos de la aplicación."""
    return {"api_name": "device_systems", "api_version": "2.0.0", "env": "development"}


# Tipos anotados para inyectar las dependencias con Annotated + Depends()
FiltersDep = Annotated[dict, Depends(user_filters)]
UserDep = Annotated[User, Depends(get_existing_user)]
ApiKeyDep = Annotated[str, Depends(verify_api_key)]
ConfigDep = Annotated[dict, Depends(get_api_config)]
