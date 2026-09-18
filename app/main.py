import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Importar el paquete de modelos registra User, Device y Loan en Base.metadata.
from app import models  # noqa: F401
from app.auth.auth_routes import router as auth_router
from app.config import settings
from app.middlewares.request_middleware import RequestContextMiddleware
from app.rate_limit import limiter
from app.routes.device_routes import router as device_router
from app.routes.loan_routes import router as loan_router
from app.routes.user_routes import router as user_router

# Configuración básica de logging para que el middleware registre las peticiones.
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="device_systems API",
    description=(
        "API REST **segura** para la gestión de usuarios, dispositivos y préstamos. "
        "Incorpora autenticación OAuth2 con tokens JWT, hash de contraseñas con "
        "passlib, protección de rutas por rol, validaciones avanzadas con Pydantic v2, "
        "middleware personalizado de trazabilidad, configuración de CORS y rate "
        "limiting. Persiste sobre una arquitectura por capas "
        "(routes → services → SQLAlchemy → SQLite) con migraciones Alembic; "
        "ejecuta `alembic upgrade head` antes de arrancar."
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
            "name": "Auth",
            "description": (
                "Registro, inicio de sesión (OAuth2 + JWT) y consulta del usuario "
                "autenticado."
            ),
        },
        {
            "name": "Users",
            "description": (
                "Operaciones CRUD sobre el recurso /users y consulta de sus préstamos. "
                "Las lecturas requieren usuario autenticado."
            ),
        },
        {
            "name": "Devices",
            "description": (
                "Operaciones CRUD sobre el recurso /devices, con filtros avanzados "
                "e historial de préstamos por dispositivo. La escritura requiere rol "
                "admin o support; el borrado, rol admin."
            ),
        },
        {
            "name": "Loans",
            "description": (
                "Gestión de préstamos: creación con validación de disponibilidad, "
                "devolución y consultas con joins y filtros."
            ),
        },
        {
            "name": "Security",
            "description": (
                "Mecanismos transversales de seguridad: OAuth2/JWT, hash de "
                "contraseñas, rate limiting, CORS y middleware de trazabilidad."
            ),
        },
    ],
)

# --- Rate limiting (slowapi) ---
# El limiter se registra en el estado de la app y se conecta su manejador para
# responder 429 Too Many Requests cuando se supera un límite.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Middlewares ---
# El middleware personalizado se añade primero (queda más interno); CORS se añade
# después para envolver toda la cadena y aplicarse a cada respuesta.
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Rutas ---
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(device_router)
app.include_router(loan_router)
