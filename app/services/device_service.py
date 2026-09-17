"""Operaciones CRUD y filtros persistentes para el recurso de dispositivos."""

from typing import Optional

from sqlalchemy import Select, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.device_model import Device
from app.schemas.device_schema import DeviceCreate, DevicePatch, DeviceUpdate


class DuplicateSerialError(ValueError):
    """El número de serie viola la restricción única de la tabla devices."""


def get_all_devices(
    db: Session,
    device_type: Optional[str] = None,
    is_available: Optional[bool] = None,
    brand: Optional[str] = None,
    search: Optional[str] = None,
) -> list[Device]:
    """Lista dispositivos aplicando filtros avanzados con where() e ilike()."""
    statement: Select[tuple[Device]] = select(Device)

    if device_type is not None:
        statement = statement.where(Device.device_type == device_type)
    if is_available is not None:
        statement = statement.where(Device.is_available == is_available)
    if brand is not None:
        statement = statement.where(Device.brand.ilike(f"%{brand}%"))
    if search is not None:
        pattern = f"%{search}%"
        statement = statement.where(
            or_(
                Device.name.ilike(pattern),
                Device.serial_number.ilike(pattern),
                Device.brand.ilike(pattern),
            )
        )

    statement = statement.order_by(Device.name.asc())
    return list(db.scalars(statement).all())


def get_device_by_id(db: Session, device_id: int) -> Optional[Device]:
    """Busca un dispositivo por su clave primaria."""
    return db.get(Device, device_id)


def get_device_by_serial(db: Session, serial_number: str) -> Optional[Device]:
    """Busca un dispositivo por su número de serie (campo único e indexado)."""
    return db.scalar(select(Device).where(Device.serial_number == serial_number))


def create_device(db: Session, data: DeviceCreate) -> Device:
    """Crea y confirma un dispositivo; traduce la restricción única a error de negocio."""
    payload = data.model_dump()
    payload["device_type"] = payload["device_type"].value
    device = Device(**payload)
    db.add(device)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise DuplicateSerialError("El número de serie ya está registrado") from error
    db.refresh(device)
    return device


def _commit_device(db: Session, device: Device, duplicate_message: str) -> Device:
    """Confirma cambios y conserva la sesión utilizable si falla la unicidad."""
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise DuplicateSerialError(duplicate_message) from error
    db.refresh(device)
    return device


def update_device_full(db: Session, device: Device, data: DeviceUpdate) -> Device:
    """Reemplaza todos los campos editables de un dispositivo existente."""
    payload = data.model_dump()
    payload["device_type"] = payload["device_type"].value
    for field, value in payload.items():
        setattr(device, field, value)
    return _commit_device(db, device, "El número de serie ya está registrado por otro dispositivo")


def update_device_partial(db: Session, device: Device, data: DevicePatch) -> Device:
    """Actualiza solo los campos explícitamente enviados por el cliente."""
    changes = data.model_dump(exclude_unset=True)
    if not changes:
        raise ValueError("No se enviaron datos para actualizar")
    if "device_type" in changes and changes["device_type"] is not None:
        changes["device_type"] = changes["device_type"].value
    for field, value in changes.items():
        setattr(device, field, value)
    return _commit_device(db, device, "El número de serie ya está registrado por otro dispositivo")


def delete_device(db: Session, device: Device) -> None:
    """Elimina un dispositivo existente y confirma la transacción."""
    db.delete(device)
    db.commit()
