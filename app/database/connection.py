"""Configuración central de SQLAlchemy para SQLite."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DATABASE_URL = "sqlite:///./device_systems.db"

# SQLite necesita esta opción porque FastAPI puede atender una petición desde
# un hilo distinto al que abrió inicialmente la conexión.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Clase base que comparten todos los modelos ORM."""

