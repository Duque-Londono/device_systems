import re
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# Definimos los roles permitidos usando Enum
class RoleEnum(str, Enum):
    admin = "admin"
    support = "support"
    user = "user"


def validate_password_strength(value: str) -> str:
    """Valida las reglas mínimas de robustez de una contraseña.

    - Mínimo 8 caracteres.
    - Al menos una mayúscula, una minúscula y un número.
    - Sin espacios en blanco.
    """
    if len(value) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")
    if re.search(r"\s", value):
        raise ValueError("La contraseña no debe contener espacios en blanco")
    if not re.search(r"[A-Z]", value):
        raise ValueError("La contraseña debe incluir al menos una mayúscula")
    if not re.search(r"[a-z]", value):
        raise ValueError("La contraseña debe incluir al menos una minúscula")
    if not re.search(r"\d", value):
        raise ValueError("La contraseña debe incluir al menos un número")
    return value


# Modelo para crear o recibir un usuario (la contraseña se hashea en el servicio)
class UserCreate(BaseModel):
    name: str = Field(..., min_length=3, description="Nombre del usuario (mínimo 3 caracteres)")
    email: EmailStr = Field(..., description="Correo electrónico válido")
    password: str = Field(
        ...,
        min_length=8,
        description="Contraseña segura: mín. 8 caracteres, con mayúscula, minúscula y número",
    )
    role: RoleEnum = Field(..., description="Rol del usuario: admin, support o user")
    is_active: bool = Field(default=True, description="Estado del usuario (activo/inactivo)")

    @field_validator("password")
    @classmethod
    def _check_password(cls, value: str) -> str:
        return validate_password_strength(value)


# Modelo para devolver un usuario. NUNCA incluye la contraseña ni su hash.
class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: RoleEnum
    is_active: bool
    created_at: datetime

    # Permite construir la respuesta desde una instancia ORM de SQLAlchemy.
    model_config = ConfigDict(from_attributes=True)

# Modelo para reemplazo completo (PUT): todos los campos son obligatorios
class UserUpdate(BaseModel):
    name: str = Field(..., min_length=3, description="Nombre del usuario (mínimo 3 caracteres)")
    email: EmailStr = Field(..., description="Correo electrónico válido")
    role: RoleEnum = Field(..., description="Rol del usuario: admin, support o user")
    is_active: bool = Field(..., description="Estado del usuario (activo/inactivo)")

# Modelo para actualización parcial (PATCH): todos los campos son opcionales
class UserPatch(BaseModel):
    name: Optional[str] = Field(None, min_length=3, description="Nombre del usuario (mínimo 3 caracteres)")
    email: Optional[EmailStr] = Field(None, description="Correo electrónico válido")
    role: Optional[RoleEnum] = Field(None, description="Rol del usuario: admin, support o user")
    is_active: Optional[bool] = Field(None, description="Estado del usuario (activo/inactivo)")
