"""Schemas de autenticación (Pydantic v2).

Incluye validación avanzada de contraseñas con ``field_validator`` y metadatos
con ``Field()``. El hash de la contraseña nunca se expone en las respuestas.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.user_schema import RoleEnum, validate_password_strength


class UserRegister(BaseModel):
    """Datos para registrar un nuevo usuario con contraseña segura."""

    name: str = Field(..., min_length=3, description="Nombre del usuario (mínimo 3 caracteres)")
    email: EmailStr = Field(..., description="Correo electrónico válido y único")
    password: str = Field(
        ...,
        min_length=8,
        description="Contraseña segura: mín. 8 caracteres, con mayúscula, minúscula y número",
    )
    role: RoleEnum = Field(default=RoleEnum.user, description="Rol del usuario: admin, support o user")

    @field_validator("password")
    @classmethod
    def _check_password(cls, value: str) -> str:
        return validate_password_strength(value)


class UserLogin(BaseModel):
    """Credenciales para autenticar un usuario."""

    email: EmailStr = Field(..., description="Correo electrónico registrado")
    password: str = Field(..., description="Contraseña del usuario")


class Token(BaseModel):
    """Respuesta de un login exitoso."""

    access_token: str = Field(..., description="Token JWT de acceso")
    token_type: str = Field(default="bearer", description="Tipo de token (siempre 'bearer')")


class TokenData(BaseModel):
    """Datos extraídos del payload de un token válido."""

    model_config = ConfigDict(from_attributes=True)

    email: str | None = None
    role: str | None = None
