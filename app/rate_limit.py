"""Configuración compartida de rate limiting con slowapi.

Se define un único ``Limiter`` que se importa tanto en ``main.py`` (para
registrarlo en la app y su manejador de errores) como en las rutas que aplican
límites mediante el decorador ``@limiter.limit``.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Identifica al cliente por su dirección IP para contabilizar las peticiones.
limiter = Limiter(key_func=get_remote_address)
