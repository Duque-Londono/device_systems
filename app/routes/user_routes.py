from fastapi import APIRouter, HTTPException, Response, status

from app.dependencies.database_dependency import DbSession
from app.dependencies.user_dependencies import (
    ApiKeyDep,
    ConfigDep,
    FiltersDep,
    UserDep,
)
from app.schemas.user_schema import UserCreate, UserPatch, UserResponse, UserUpdate
from app.services import user_service

# Inicializamos el router
router = APIRouter(prefix="/users", tags=["Users"])


# Endpoint GET /users (filtros vía dependencia reutilizable)
@router.get(
    "",
    response_model=list[UserResponse],
    summary="Listar usuarios",
    description=(
        "Retorna todos los usuarios registrados en el sistema. "
        "Admite filtros opcionales por query param: `role` (admin, support, user) "
        "e `is_active` (true/false); ambos pueden combinarse. También permite "
        "ordenar con `sort_by` (name o created_at) y `sort_order` (asc o desc). "
        "**Códigos de respuesta:** `200` con la lista (posiblemente vacía) y "
        "`422` si un filtro tiene un valor inválido (ej. rol inexistente)."
    ),
    response_description="Lista de usuarios que cumplen los filtros aplicados.",
    responses={422: {"description": "Filtros u ordenamiento inválidos."}},
)
def get_users(filters: FiltersDep, db: DbSession):
    return user_service.get_all_users(db, **filters)


# Endpoint GET /users/{user_id} (resolución vía dependencia get_existing_user)
@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Consultar un usuario por ID",
    description=(
        "Busca y retorna un usuario específico por su identificador numérico. "
        "La existencia se valida mediante la dependencia `get_existing_user`. "
        "**Códigos de respuesta:** `200` si existe, `404` si el ID no se encuentra, "
        "`422` si el ID no es un entero válido."
    ),
    response_description="Datos completos del usuario solicitado.",
    responses={404: {"description": "Usuario no encontrado."}},
)
def get_user_by_id(user: UserDep):
    return user


# Endpoint POST /users
@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo usuario",
    description=(
        "Crea un usuario a partir del cuerpo JSON validado por `UserCreate` "
        "(nombre mínimo 3 caracteres, correo válido, rol dentro del enum). "
        "El ID se autogenera y la respuesta incluye las cabeceras personalizadas "
        "`X-App-Name` y `X-API-Version`. "
        "**Códigos de respuesta:** `201` creado correctamente, `400` si el correo "
        "ya está registrado, `422` si el cuerpo viola las reglas de Pydantic."
    ),
    response_description="Usuario creado con su ID autogenerado.",
    responses={400: {"description": "El correo electrónico ya está registrado."}},
)
def create_user(user: UserCreate, response: Response, db: DbSession):
    try:
        new_user = user_service.create_user(db, user)
    except ValueError as error:
        # Error de negocio -> lo traducimos a HTTP 400
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

    # Cabeceras personalizadas
    response.headers["X-App-Name"] = "device_systems"
    response.headers["X-API-Version"] = "1.0"

    return new_user


# Endpoint PUT /users/{user_id} (reemplazo completo)
@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Reemplazar un usuario completamente",
    description=(
        "Sobrescribe **todos** los campos editables (name, email, role, is_active) "
        "del usuario indicado; cualquier campo omitido se rechaza con `422`. "
        "Si el nuevo correo pertenece a otro usuario se devuelve `400`. "
        "**Códigos de respuesta:** `200` reemplazo exitoso, `400` correo duplicado "
        "en otro usuario, `404` si el ID no existe, `422` cuerpo incompleto o inválido."
    ),
    response_description="Usuario actualizado con todos sus campos.",
    responses={
        400: {"description": "El correo electrónico ya está registrado."},
        404: {"description": "Usuario no encontrado."},
    },
)
def replace_user(data: UserUpdate, user: UserDep, db: DbSession):
    # UserDep ya garantizó la existencia (404 si no existe)
    try:
        return user_service.update_user_full(db, user, data)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# Endpoint PATCH /users/{user_id} (actualización parcial)
@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar parcialmente un usuario",
    description=(
        "Modifica únicamente los campos enviados en el cuerpo JSON "
        "(name, email, role e is_active son todos opcionales). "
        "Si el cuerpo llega vacío `{}` se devuelve `400`; si el nuevo correo "
        "pertenece a otro usuario también se devuelve `400`. "
        "**Códigos de respuesta:** `200` actualización exitosa, `400` sin campos "
        "o correo duplicado, `404` si el ID no existe, `422` campos inválidos."
    ),
    response_description="Usuario con los campos enviados aplicados.",
    responses={
        400: {"description": "No se enviaron datos o el correo ya está registrado."},
        404: {"description": "Usuario no encontrado."},
    },
)
def update_partial(data: UserPatch, user: UserDep, db: DbSession):
    # UserDep ya garantizó la existencia (404 si no existe)
    try:
        return user_service.update_user_partial(db, user, data)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# Endpoint DELETE /users/{user_id}
@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un usuario",
    description=(
        "Elimina permanentemente el usuario indicado. Al ser una operación "
        "destructiva, requiere el encabezado de seguridad simulada "
        "`X-API-Key: device-systems-2026` (dependencia `verify_api_key`). "
        "La respuesta incluye cabeceras informativas generadas desde la "
        "dependencia de configuración `get_api_config`. "
        "**Códigos de respuesta:** `204` eliminado sin contenido, `401` falta "
        "el encabezado X-API-Key, `403` llave inválida, `404` si el ID no existe."
    ),
    response_description="Sin contenido: el usuario fue eliminado.",
    responses={
        401: {"description": "Falta el encabezado X-API-Key."},
        403: {"description": "API Key inválida."},
        404: {"description": "Usuario no encontrado."},
    },
)
def delete_user(user: UserDep, config: ConfigDep, _auth: ApiKeyDep, response: Response, db: DbSession):
    # UserDep ya garantizó la existencia (404 si no existe)
    user_service.delete_user(db, user)

    # Cabeceras informativas desde la dependencia de configuración
    response.headers["X-API-Name"] = config["api_name"]
    response.headers["X-API-Version"] = config["api_version"]
