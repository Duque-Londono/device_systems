# Capa de datos: base de datos simulada (lista de diccionarios en memoria).
# Aquí vive la "persistencia". Si mañana se cambia a SQL o MongoDB,
# solo esta capa (y el servicio) deberían verse afectados.

fake_users_db = [
    {"id": 1, "name": "Ana Silva", "email": "ana@example.com", "role": "admin", "is_active": True},
    {"id": 2, "name": "Luis Gomez", "email": "luis@example.com", "role": "user", "is_active": True},
    {"id": 3, "name": "Marta Rios", "email": "marta@example.com", "role": "support", "is_active": False},
]
