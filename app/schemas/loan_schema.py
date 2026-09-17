"""Contratos y validaciones Pydantic para el recurso /loans."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class LoanStatusEnum(str, Enum):
    """Estados posibles de un préstamo."""

    active = "active"
    returned = "returned"
    overdue = "overdue"


# Modelo para crear un préstamo
class LoanCreate(BaseModel):
    user_id: int = Field(..., gt=0, description="ID del usuario que solicita el préstamo")
    device_id: int = Field(..., gt=0, description="ID del dispositivo a prestar")


# Modelo para actualizar un préstamo (estado / fecha de devolución)
class LoanUpdate(BaseModel):
    status: Optional[LoanStatusEnum] = Field(None, description="Nuevo estado del préstamo")
    return_date: Optional[datetime] = Field(None, description="Fecha de devolución")


# Modelo básico para devolver un préstamo
class LoanResponse(BaseModel):
    id: int
    user_id: int
    device_id: int
    loan_date: datetime
    return_date: Optional[datetime]
    status: str

    model_config = ConfigDict(from_attributes=True)


# --- Sub-schemas anidados para la respuesta detallada (consultas con joins) ---
class LoanUserInfo(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class LoanDeviceInfo(BaseModel):
    id: int
    name: str
    serial_number: str
    device_type: str

    model_config = ConfigDict(from_attributes=True)


# Respuesta detallada con información relacionada de usuario y dispositivo
class LoanDetailResponse(BaseModel):
    id: int = Field(..., description="ID del préstamo (loan_id)")
    status: str
    loan_date: datetime
    return_date: Optional[datetime]
    user: LoanUserInfo
    device: LoanDeviceInfo

    model_config = ConfigDict(from_attributes=True)
