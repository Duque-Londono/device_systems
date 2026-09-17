"""Modelo ORM para la tabla ``devices``."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base

if TYPE_CHECKING:
    from app.models.loan_model import Loan


class Device(Base):
    """Dispositivo tecnológico disponible para préstamo."""

    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    serial_number: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    device_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    brand: Mapped[str | None] = mapped_column(String(80), nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
    )

    # Un dispositivo puede aparecer en muchos préstamos históricos (One-to-Many).
    loans: Mapped[list["Loan"]] = relationship(
        "Loan", back_populates="device", cascade="all, delete-orphan"
    )
