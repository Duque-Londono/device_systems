"""Endpoints de autenticación: registro, login y perfil del usuario actual."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.auth import auth_service
from app.auth.security import create_access_token
from app.dependencies.auth_dependency import CurrentActiveUser
from app.dependencies.database_dependency import DbSession
from app.rate_limit import limiter
from app.schemas.auth_schema import Token, UserRegister
from app.schemas.user_schema import UserResponse
from app.services.user_service import DuplicateEmailError

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un usuario con contraseña segura",
    description=(
        "Crea un usuario validando nombre, correo único, contraseña segura "
        "(mín. 8 caracteres, mayúscula, minúscula y número) y rol permitido. "
        "La contraseña se almacena solo como hash bcrypt; nunca en texto plano. "
        "**Límite:** 3 solicitudes por minuto. "
        "**Códigos:** `201` creado, `400` correo duplicado, `422` datos inválidos, "
        "`429` demasiadas solicitudes."
    ),
    response_description="Usuario creado (sin exponer la contraseña).",
    responses={
        400: {"description": "El correo electrónico ya está registrado."},
        429: {"description": "Demasiadas solicitudes (rate limit)."},
    },
)
@limiter.limit("3/minute")
def register(data: UserRegister, request: Request, db: DbSession):
    try:
        return auth_service.register_user(db, data)
    except DuplicateEmailError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post(
    "/login",
    response_model=Token,
    summary="Autenticar usuario y obtener token JWT",
    description=(
        "Recibe las credenciales por formulario OAuth2 (`username` = correo, "
        "`password`) y devuelve un token JWT de acceso. "
        "**Límite:** 5 solicitudes por minuto. "
        "**Códigos:** `200` token generado, `401` credenciales inválidas, "
        "`429` demasiadas solicitudes."
    ),
    response_description="Token de acceso JWT (token_type = bearer).",
    responses={
        401: {"description": "Correo o contraseña incorrectos."},
        429: {"description": "Demasiadas solicitudes (rate limit)."},
    },
)
@limiter.limit("5/minute")
def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
):
    # En el formulario OAuth2 el campo "username" transporta el correo del usuario.
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return Token(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Obtener el usuario autenticado",
    description=(
        "Devuelve los datos del usuario asociado al token enviado en "
        "`Authorization: Bearer <token>`. Nunca retorna el hash de la contraseña. "
        "**Códigos:** `200` datos del usuario, `401` token ausente o inválido."
    ),
    response_description="Datos del usuario autenticado.",
    responses={401: {"description": "Token ausente o inválido."}},
)
def read_me(current_user: CurrentActiveUser):
    return current_user
