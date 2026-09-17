"""Dependencias reutilizables para el recurso /loans."""

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Query, status

from app.dependencies.database_dependency import DbSession
from app.models.loan_model import Loan
from app.schemas.loan_schema import LoanStatusEnum
from app.services import loan_service


def loan_filters(
    status: Optional[LoanStatusEnum] = Query(
        None, description="Filtrar por estado del préstamo (active, returned, overdue)"
    ),
    user_email: Optional[str] = Query(
        None, description="Filtrar por email del usuario (coincidencia parcial)"
    ),
    device_type: Optional[str] = Query(
        None, description="Filtrar por tipo de dispositivo"
    ),
) -> dict:
    """Agrupa los query params de filtrado de préstamos (usados con joins)."""
    return {
        "status": status.value if status is not None else None,
        "user_email": user_email,
        "device_type": device_type,
    }


def get_existing_loan(loan_id: int, db: DbSession) -> Loan:
    """Resuelve el préstamo por ID o lanza 404."""
    loan = loan_service.get_loan_by_id(db, loan_id)
    if loan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Préstamo no encontrado"
        )
    return loan


LoanFiltersDep = Annotated[dict, Depends(loan_filters)]
LoanDep = Annotated[Loan, Depends(get_existing_loan)]
