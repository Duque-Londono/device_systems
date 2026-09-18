"""Endpoints REST para el recurso /loans y consultas relacionadas."""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.dependencies.auth_dependency import get_current_active_user, require_roles
from app.dependencies.database_dependency import DbSession
from app.dependencies.device_dependencies import DeviceDep
from app.dependencies.loan_dependencies import LoanDep, LoanFiltersDep
from app.dependencies.user_dependencies import UserDep
from app.rate_limit import limiter
from app.schemas.loan_schema import LoanCreate, LoanDetailResponse, LoanResponse
from app.schemas.user_schema import RoleEnum
from app.services import loan_service
from app.services.loan_service import (
    DeviceNotAvailableError,
    DeviceNotFoundError,
    LoanAlreadyReturnedError,
    UserNotFoundError,
)

router = APIRouter(tags=["Loans"])

# Gestión de préstamos con privilegios: solo admin o support.
require_admin_or_support = require_roles(RoleEnum.admin, RoleEnum.support)


@router.get(
    "/loans",
    response_model=list[LoanDetailResponse],
    summary="Listar préstamos con filtros",
    description=(
        "Lista préstamos combinando información de usuario y dispositivo mediante "
        "joins. Admite filtros por query param: `status` (active, returned, overdue), "
        "`user_email` (coincidencia parcial) y `device_type`. "
        "**Códigos:** `200` con la lista, `422` filtro inválido."
    ),
    response_description="Lista de préstamos con datos relacionados.",
)
def list_loans(filters: LoanFiltersDep, db: DbSession):
    return loan_service.get_all_loans(db, **filters)


@router.get(
    "/loans/details",
    response_model=list[LoanDetailResponse],
    summary="Listar préstamos con información detallada (joins)",
    description=(
        "Retorna todos los préstamos con los datos básicos del usuario y del "
        "dispositivo relacionados, usando consultas con joins. "
        "**Códigos:** `200` con la lista."
    ),
    response_description="Préstamos con usuario y dispositivo anidados.",
    responses={
        401: {"description": "Token ausente o inválido."},
        403: {"description": "Requiere rol admin o support."},
    },
    dependencies=[Depends(require_admin_or_support)],
)
def list_loan_details(db: DbSession):
    return loan_service.get_all_loans(db)


@router.get(
    "/loans/{loan_id}",
    response_model=LoanDetailResponse,
    summary="Consultar un préstamo por ID",
    description=(
        "Retorna un préstamo específico con su usuario y dispositivo relacionados. "
        "**Códigos:** `200` si existe, `404` si no se encuentra."
    ),
    response_description="Préstamo con información relacionada.",
    responses={404: {"description": "Préstamo no encontrado."}},
)
def get_loan(loan: LoanDep):
    return loan


@router.post(
    "/loans",
    response_model=LoanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo préstamo",
    description=(
        "Crea un préstamo asociando un usuario y un dispositivo. Valida que el "
        "usuario y el dispositivo existan, que el dispositivo esté disponible, y "
        "marca el dispositivo como no disponible. "
        "**Códigos:** `201` creado, `404` usuario o dispositivo inexistente, "
        "`409` dispositivo no disponible, `422` cuerpo inválido."
    ),
    response_description="Préstamo creado con estado 'active'.",
    responses={
        401: {"description": "Token ausente o inválido."},
        404: {"description": "Usuario o dispositivo inexistente."},
        409: {"description": "El dispositivo no está disponible."},
        429: {"description": "Demasiadas solicitudes (rate limit)."},
    },
    dependencies=[Depends(get_current_active_user)],
)
@limiter.limit("10/minute")
def create_loan(data: LoanCreate, db: DbSession, request: Request):
    try:
        return loan_service.create_loan(db, data.user_id, data.device_id)
    except (UserNotFoundError, DeviceNotFoundError) as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    except DeviceNotAvailableError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))


@router.patch(
    "/loans/{loan_id}/return",
    response_model=LoanResponse,
    summary="Devolver un dispositivo prestado",
    description=(
        "Registra la devolución de un préstamo: lo marca como 'returned', asigna "
        "la fecha de devolución y vuelve a marcar el dispositivo como disponible. "
        "**Códigos:** `200` devolución exitosa, `404` préstamo inexistente, "
        "`409` el préstamo ya fue devuelto."
    ),
    response_description="Préstamo actualizado con estado 'returned'.",
    responses={
        401: {"description": "Token ausente o inválido."},
        403: {"description": "Requiere rol admin o support."},
        404: {"description": "Préstamo no encontrado."},
        409: {"description": "El préstamo ya fue devuelto."},
    },
    dependencies=[Depends(require_admin_or_support)],
)
def return_loan(loan: LoanDep, db: DbSession):
    try:
        return loan_service.return_loan(db, loan)
    except LoanAlreadyReturnedError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))


@router.get(
    "/users/{user_id}/loans",
    response_model=list[LoanDetailResponse],
    tags=["Users"],
    summary="Consultar préstamos de un usuario",
    description=(
        "Retorna todos los préstamos asociados a un usuario, con el dispositivo "
        "relacionado. Valida que el usuario exista. "
        "**Códigos:** `200` con la lista, `404` usuario inexistente."
    ),
    response_description="Préstamos del usuario indicado.",
    responses={404: {"description": "Usuario no encontrado."}},
)
def get_user_loans(user: UserDep, db: DbSession):
    return loan_service.get_loans_by_user(db, user.id)


@router.get(
    "/devices/{device_id}/loans",
    response_model=list[LoanDetailResponse],
    tags=["Devices"],
    summary="Consultar historial de préstamos de un dispositivo",
    description=(
        "Retorna el historial de préstamos de un dispositivo, con el usuario "
        "relacionado. Valida que el dispositivo exista. "
        "**Códigos:** `200` con la lista, `404` dispositivo inexistente."
    ),
    response_description="Historial de préstamos del dispositivo indicado.",
    responses={404: {"description": "Dispositivo no encontrado."}},
)
def get_device_loans(device: DeviceDep, db: DbSession):
    return loan_service.get_loans_by_device(db, device.id)
