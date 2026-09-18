"""Configuración central de la aplicación cargada desde variables de entorno.

Usa python-dotenv para leer el archivo ``.env`` (no versionado). Nunca se deben
subir secretos reales al repositorio: el archivo ``.env.example`` documenta las
variables necesarias con valores de ejemplo.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

# Carga las variables definidas en .env al entorno del proceso (si el archivo existe).
load_dotenv()


class Settings:
    """Agrupa la configuración de seguridad y CORS leída del entorno."""

    # Clave para firmar los tokens JWT. En producción DEBE venir del entorno.
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "cambia-esta-clave-en-produccion-device-systems-2026",
    )
    # Algoritmo de firma de los JWT.
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    # Minutos de validez del token de acceso.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )

    # Orígenes autorizados para CORS (separados por comas en el .env).
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://localhost:3000",
        ).split(",")
        if origin.strip()
    ]


settings = Settings()
