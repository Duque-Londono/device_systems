"""Contratos y validaciones Pydantic para el recurso /devices."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DeviceTypeEnum(str, Enum):
    """Tipos de dispositivo sugeridos por la guía."""

    laptop = "laptop"
    tablet = "tablet"
    proyector = "proyector"
    camara = "camara"
    router = "router"
    monitor = "monitor"


# Modelo para crear un dispositivo
class DeviceCreate(BaseModel):
    name: str = Field(..., min_length=2, description="Nombre del dispositivo")
    serial_number: str = Field(
        ..., min_length=1, description="Número de serie único del dispositivo"
    )
    device_type: DeviceTypeEnum = Field(..., description="Tipo de dispositivo")
    brand: Optional[str] = Field(None, description="Marca del dispositivo (opcional)")
    is_available: bool = Field(
        default=True, description="Indica si el dispositivo está disponible para préstamo"
    )


# Modelo para reemplazo completo (PUT): todos los campos obligatorios
class DeviceUpdate(BaseModel):
    name: str = Field(..., min_length=2, description="Nombre del dispositivo")
    serial_number: str = Field(..., min_length=1, description="Número de serie único")
    device_type: DeviceTypeEnum = Field(..., description="Tipo de dispositivo")
    brand: Optional[str] = Field(None, description="Marca del dispositivo (opcional)")
    is_available: bool = Field(..., description="Disponibilidad del dispositivo")


# Modelo para actualización parcial (PATCH): todos los campos opcionales
class DevicePatch(BaseModel):
    name: Optional[str] = Field(None, min_length=2, description="Nombre del dispositivo")
    serial_number: Optional[str] = Field(
        None, min_length=1, description="Número de serie único"
    )
    device_type: Optional[DeviceTypeEnum] = Field(None, description="Tipo de dispositivo")
    brand: Optional[str] = Field(None, description="Marca del dispositivo (opcional)")
    is_available: Optional[bool] = Field(None, description="Disponibilidad del dispositivo")


# Modelo para devolver un dispositivo (incluye ID y metadatos)
class DeviceResponse(BaseModel):
    id: int
    name: str
    serial_number: str
    device_type: str
    brand: Optional[str]
    is_available: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
