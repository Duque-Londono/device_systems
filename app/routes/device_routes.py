"""Endpoints REST para el recurso /devices."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.auth_dependency import require_admin, require_roles
from app.dependencies.database_dependency import DbSession
from app.dependencies.device_dependencies import DeviceDep, DeviceFiltersDep
from app.schemas.device_schema import (
    DeviceCreate,
    DevicePatch,
    DeviceResponse,
    DeviceUpdate,
)
from app.schemas.user_schema import RoleEnum
from app.services import device_service

router = APIRouter(prefix="/devices", tags=["Devices"])

# Autorización reutilizable: crear/editar dispositivos lo pueden hacer admin o support.
require_admin_or_support = require_roles(RoleEnum.admin, RoleEnum.support)


@router.get(
    "",
    response_model=list[DeviceResponse],
    summary="Listar dispositivos",
    description=(
        "Retorna los dispositivos registrados. Admite filtros por query param: "
        "`device_type`, `is_available`, `brand` (coincidencia parcial) y `search` "
        "(busca en nombre, número de serie y marca con ilike). "
        "**Códigos:** `200` con la lista, `422` si un filtro es inválido."
    ),
    response_description="Lista de dispositivos que cumplen los filtros aplicados.",
)
def list_devices(filters: DeviceFiltersDep, db: DbSession):
    return device_service.get_all_devices(db, **filters)


@router.get(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Consultar un dispositivo por ID",
    description=(
        "Busca y retorna un dispositivo por su identificador. "
        "**Códigos:** `200` si existe, `404` si no se encuentra, `422` ID inválido."
    ),
    response_description="Datos completos del dispositivo solicitado.",
    responses={404: {"description": "Dispositivo no encontrado."}},
)
def get_device(device: DeviceDep):
    return device


@router.post(
    "",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo dispositivo",
    description=(
        "Crea un dispositivo validado por `DeviceCreate`. El número de serie debe "
        "ser único. "
        "**Códigos:** `201` creado, `400` serie duplicada, `422` cuerpo inválido."
    ),
    response_description="Dispositivo creado con su ID autogenerado.",
    responses={
        400: {"description": "El número de serie ya está registrado."},
        401: {"description": "Token ausente o inválido."},
        403: {"description": "Requiere rol admin o support."},
    },
    dependencies=[Depends(require_admin_or_support)],
)
def create_device(data: DeviceCreate, db: DbSession):
    try:
        return device_service.create_device(db, data)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.put(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Reemplazar un dispositivo completamente",
    description=(
        "Sobrescribe todos los campos editables del dispositivo indicado. "
        "**Códigos:** `200` reemplazo exitoso, `400` serie duplicada, `404` no "
        "encontrado, `422` cuerpo incompleto o inválido."
    ),
    response_description="Dispositivo actualizado con todos sus campos.",
    responses={
        400: {"description": "El número de serie ya está registrado."},
        401: {"description": "Token ausente o inválido."},
        403: {"description": "Requiere rol admin o support."},
        404: {"description": "Dispositivo no encontrado."},
    },
    dependencies=[Depends(require_admin_or_support)],
)
def replace_device(data: DeviceUpdate, device: DeviceDep, db: DbSession):
    try:
        return device_service.update_device_full(db, device, data)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.patch(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Actualizar parcialmente un dispositivo",
    description=(
        "Modifica solo los campos enviados en el cuerpo JSON. Si el cuerpo llega "
        "vacío se devuelve `400`. "
        "**Códigos:** `200` actualizado, `400` sin campos o serie duplicada, "
        "`404` no encontrado, `422` campos inválidos."
    ),
    response_description="Dispositivo con los campos enviados aplicados.",
    responses={
        400: {"description": "No se enviaron datos o el número de serie ya existe."},
        401: {"description": "Token ausente o inválido."},
        403: {"description": "Requiere rol admin o support."},
        404: {"description": "Dispositivo no encontrado."},
    },
    dependencies=[Depends(require_admin_or_support)],
)
def update_device(data: DevicePatch, device: DeviceDep, db: DbSession):
    try:
        return device_service.update_device_partial(db, device, data)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.delete(
    "/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un dispositivo",
    description=(
        "Elimina permanentemente el dispositivo indicado (y su historial de "
        "préstamos asociado). "
        "**Códigos:** `204` eliminado, `404` no encontrado."
    ),
    response_description="Sin contenido: el dispositivo fue eliminado.",
    responses={
        401: {"description": "Token ausente o inválido."},
        403: {"description": "Requiere rol admin."},
        404: {"description": "Dispositivo no encontrado."},
    },
    dependencies=[Depends(require_admin)],
)
def delete_device(device: DeviceDep, db: DbSession):
    device_service.delete_device(db, device)
