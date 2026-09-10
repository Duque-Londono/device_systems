"""Dependencia de FastAPI para entregar y cerrar sesiones SQLAlchemy."""

from typing import Annotated, Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Crea una sesión por petición y la cierra incluso si ocurre un error."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]
