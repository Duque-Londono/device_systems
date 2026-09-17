from fastapi import FastAPI

# Importar el paquete de modelos registra User, Device y Loan en Base.metadata.
from app import models  # noqa: F401
from app.routes.device_routes import router as device_router
from app.routes.loan_routes import router as loan_router
from app.routes.user_routes import router as user_router

app = FastAPI(
    title="device_systems API",
    description=(
        "API REST para la gestión de usuarios, dispositivos y préstamos. "
        "Incorpora migraciones de base de datos con Alembic, asociaciones entre "
        "modelos (User, Device y Loan) y consultas avanzadas con joins y filtros, "
        "sobre una arquitectura profesional por capas "
        "(routes → services → SQLAlchemy → SQLite). El esquema de la base de datos "
        "se gestiona con Alembic; ejecuta `alembic upgrade head` antes de arrancar."
    ),
    version="3.0.0",
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
                "Operaciones CRUD sobre el recurso /users y consulta de sus préstamos."
            ),
        },
        {
            "name": "Devices",
            "description": (
                "Operaciones CRUD sobre el recurso /devices, con filtros avanzados "
                "e historial de préstamos por dispositivo."
            ),
        },
        {
            "name": "Loans",
            "description": (
                "Gestión de préstamos: creación con validación de disponibilidad, "
                "devolución y consultas con joins y filtros."
            ),
        },
    ],
)

# Incluimos las rutas de cada recurso
app.include_router(user_router)
app.include_router(device_router)
app.include_router(loan_router)
