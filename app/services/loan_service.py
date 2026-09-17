"""Gestión de préstamos: reglas de negocio y consultas con joins y filtros."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from app.models.device_model import Device
from app.models.loan_model import Loan
from app.models.user_model import User


class UserNotFoundError(ValueError):
    """El usuario referenciado por el préstamo no existe."""


class DeviceNotFoundError(ValueError):
    """El dispositivo referenciado por el préstamo no existe."""


class DeviceNotAvailableError(ValueError):
    """El dispositivo no está disponible para préstamo (regla de negocio)."""


class LoanAlreadyReturnedError(ValueError):
    """Se intenta devolver un préstamo que ya fue devuelto (regla de negocio)."""


def _detailed_query() -> Select[tuple[Loan]]:
    """Consulta base que precarga usuario y dispositivo con joins (evita N+1)."""
    return select(Loan).options(joinedload(Loan.user), joinedload(Loan.device))


def get_loan_by_id(db: Session, loan_id: int) -> Optional[Loan]:
    """Busca un préstamo por su clave primaria."""
    return db.get(Loan, loan_id)


def get_all_loans(
    db: Session,
    status: Optional[str] = None,
    user_email: Optional[str] = None,
    device_type: Optional[str] = None,
) -> list[Loan]:
    """Lista préstamos combinando información de varias tablas con joins y filtros.

    Usa join() con las tablas users y devices para poder filtrar por email del
    usuario o tipo de dispositivo, además del estado del préstamo.
    """
    statement = _detailed_query()

    if status is not None:
        statement = statement.where(Loan.status == status)
    if user_email is not None:
        statement = statement.join(User, Loan.user_id == User.id).where(
            User.email.ilike(f"%{user_email}%")
        )
    if device_type is not None:
        statement = statement.join(Device, Loan.device_id == Device.id).where(
            Device.device_type == device_type
        )

    statement = statement.order_by(Loan.loan_date.desc())
    return list(db.scalars(statement).unique().all())


def get_loans_by_user(db: Session, user_id: int) -> list[Loan]:
    """Consulta todos los préstamos de un usuario con su dispositivo asociado."""
    statement = _detailed_query().where(Loan.user_id == user_id).order_by(
        Loan.loan_date.desc()
    )
    return list(db.scalars(statement).unique().all())


def get_loans_by_device(db: Session, device_id: int) -> list[Loan]:
    """Consulta el historial de préstamos de un dispositivo con su usuario asociado."""
    statement = _detailed_query().where(Loan.device_id == device_id).order_by(
        Loan.loan_date.desc()
    )
    return list(db.scalars(statement).unique().all())


def create_loan(db: Session, user_id: int, device_id: int) -> Loan:
    """Crea un préstamo validando integridad referencial y disponibilidad.

    - Valida que el usuario exista (404 en la capa de rutas).
    - Valida que el dispositivo exista (404).
    - Valida que el dispositivo esté disponible (409).
    - Crea el préstamo y marca el dispositivo como no disponible.
    """
    user = db.get(User, user_id)
    if user is None:
        raise UserNotFoundError("El usuario indicado no existe")

    device = db.get(Device, device_id)
    if device is None:
        raise DeviceNotFoundError("El dispositivo indicado no existe")

    if not device.is_available:
        raise DeviceNotAvailableError("El dispositivo no está disponible para préstamo")

    loan = Loan(user_id=user_id, device_id=device_id, status="active")
    device.is_available = False
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return loan


def return_loan(db: Session, loan: Loan) -> Loan:
    """Registra la devolución de un préstamo y libera el dispositivo.

    - Valida que el préstamo no esté ya devuelto (409).
    - Marca el préstamo como 'returned' y asigna la fecha de devolución.
    - Vuelve a marcar el dispositivo como disponible.
    """
    if loan.status == "returned":
        raise LoanAlreadyReturnedError("El préstamo ya fue devuelto")

    loan.status = "returned"
    loan.return_date = datetime.utcnow()

    device = db.get(Device, loan.device_id)
    if device is not None:
        device.is_available = True

    db.commit()
    db.refresh(loan)
    return loan
