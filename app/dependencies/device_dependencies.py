"""Dependencias reutilizables para el recurso /devices."""

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Query, status

from app.dependencies.database_dependency import DbSession
from app.models.device_model import Device
from app.schemas.device_schema import DeviceTypeEnum
from app.services import device_service


def device_filters(
    device_type: Optional[DeviceTypeEnum] = Query(
        None, description="Filtrar por tipo de dispositivo"
    ),
    is_available: Optional[bool] = Query(
        None, description="Filtrar por disponibilidad (true o false)"
    ),
    brand: Optional[str] = Query(None, description="Filtrar por marca (coincidencia parcial)"),
    search: Optional[str] = Query(
        None, description="Búsqueda por nombre, serie o marca"
    ),
) -> dict:
    """Agrupa los query params de filtrado de dispositivos."""
    return {
        "device_type": device_type.value if device_type is not None else None,
        "is_available": is_available,
        "brand": brand,
        "search": search,
    }


def get_existing_device(device_id: int, db: DbSession) -> Device:
    """Resuelve el dispositivo por ID o lanza 404."""
    device = device_service.get_device_by_id(db, device_id)
    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dispositivo no encontrado"
        )
    return device


DeviceFiltersDep = Annotated[dict, Depends(device_filters)]
DeviceDep = Annotated[Device, Depends(get_existing_device)]
