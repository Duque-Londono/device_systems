"""Middleware personalizado de trazabilidad de peticiones.

Por cada petición HTTP:
- Mide el tiempo de respuesta y lo expone en la cabecera ``X-Process-Time``.
- Añade la cabecera ``X-App-Name: device_systems``.
- Genera o propaga un ``X-Request-ID`` (correlation ID) para trazabilidad.
- Registra en el log el método, la ruta y el código de estado de la respuesta.
"""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("device_systems.requests")

APP_NAME = "device_systems"


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware global que instrumenta cada petición."""

    async def dispatch(self, request: Request, call_next):
        # Propaga el X-Request-ID entrante o genera uno nuevo.
        request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex[:8])

        start = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start

        # Cabeceras de trazabilidad añadidas a la respuesta.
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        response.headers["X-App-Name"] = APP_NAME
        response.headers["X-Request-ID"] = request_id

        # Registro de la petición: método, ruta y código de estado.
        logger.info(
            "%s %s -> %s (%.4fs) [request_id=%s]",
            request.method,
            request.url.path,
            response.status_code,
            process_time,
            request_id,
        )
        return response
