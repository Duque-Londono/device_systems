"""Modelo ORM para la tabla ``loans`` (préstamos de dispositivos)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base

if TYPE_CHECKING:
    from app.models.device_model import Device
    from app.models.user_model import User


class Loan(Base):
    """Préstamo que asocia un usuario con un dispositivo (Many-to-One a ambos)."""

    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id"), nullable=False, index=True
    )
    loan_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
    )
    return_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", index=True
    )

    # Cada préstamo pertenece a un usuario y a un dispositivo (integridad referencial).
    user: Mapped["User"] = relationship("User", back_populates="loans")
    device: Mapped["Device"] = relationship("Device", back_populates="loans")
