from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database.connection import Base, engine
# Importar el modelo antes de create_all registra la tabla users en Base.metadata.
from app.models import User  # noqa: F401
from app.routes.user_routes import router as user_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Inicializa las tablas necesarias al arrancar la aplicación."""
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="device_systems API",
    description=(
        "API REST para la gestión de usuarios del sistema de dispositivos. "
        "Permite listar, filtrar, consultar, registrar, reemplazar, actualizar "
        "parcialmente y eliminar usuarios, aplicando validaciones estrictas con "
        "Pydantic v2 y una arquitectura profesional por capas "
        "(routes → services → SQLAlchemy → SQLite)."
    ),
    version="2.0.0",
    terms_of_service="https://example.com/terms-of-service",
    contact={
        "name": "Juan - Aprendiz SENA ADSO",
        "email": "juan@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "Users",
            "description": (
                "Operaciones CRUD sobre el recurso /users: listar con filtros, "
                "consultar por ID, crear, reemplazar completo (PUT), actualizar "
                "parcial (PATCH) y eliminar."
            ),
        },
    ],
    lifespan=lifespan,
)

# Incluimos las rutas de usuarios
app.include_router(user_router)
