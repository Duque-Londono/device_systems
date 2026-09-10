from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# Definimos los roles permitidos usando Enum
class RoleEnum(str, Enum):
    admin = "admin"
    support = "support"
    user = "user"

# Modelo base para crear o recibir un usuario
class UserCreate(BaseModel):
    name: str = Field(..., min_length=3, description="Nombre del usuario (mínimo 3 caracteres)")
    email: EmailStr = Field(..., description="Correo electrónico válido")
    role: RoleEnum = Field(..., description="Rol del usuario: admin, support o user")
    is_active: bool = Field(default=True, description="Estado del usuario (activo/inactivo)")

# Modelo para devolver un usuario (incluye el ID)
class UserResponse(UserCreate):
    id: int
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
