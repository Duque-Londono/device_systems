from fastapi import FastAPI

from app.routes.user_routes import router as user_router

app = FastAPI(
    title="device_systems API",
    description=(
        "API REST para la gestión de usuarios del sistema de dispositivos. "
        "Permite listar, filtrar, consultar, registrar, reemplazar, actualizar "
        "parcialmente y eliminar usuarios, aplicando validaciones estrictas con "
        "Pydantic v2 y una arquitectura profesional por capas "
        "(routes → services → data)."
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
)

# Incluimos las rutas de usuarios
app.include_router(user_router)
