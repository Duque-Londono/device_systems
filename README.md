# device_systems API

API REST académica para administrar **usuarios, dispositivos y préstamos**. Esta versión evoluciona el CRUD de usuarios incorporando tres capacidades del backend profesional: **migraciones de base de datos con Alembic**, **asociaciones entre modelos** (One-to-Many / Many-to-One) y **consultas avanzadas con joins y filtros**, sobre **FastAPI, SQLAlchemy 2, Pydantic v2 y SQLite**.

## Objetivo

Evolucionar una API REST desde un CRUD de una sola tabla hacia un sistema con relaciones, integridad referencial, migraciones controladas y consultas que combinan información de varias tablas.

## Tecnologías

- Python, FastAPI y Uvicorn.
- SQLAlchemy 2 y SQLite.
- **Alembic** para migraciones de esquema.
- Pydantic v2 y `email-validator`.

## Ejecutar el proyecto

```bash
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
pip install -r requirements.txt

# 1) Crear/actualizar el esquema con Alembic (obligatorio la primera vez)
alembic upgrade head

# 2) Arrancar la API
uvicorn app.main:app --reload
```

> A diferencia de la versión anterior, el esquema **ya no se crea con `create_all`**: ahora lo gestiona Alembic. Debes ejecutar `alembic upgrade head` para crear `device_systems.db` con las tablas `users`, `devices` y `loans`.

Documentación interactiva:

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Arquitectura

```text
device_systems/
├── app/
│   ├── main.py                          # App FastAPI y registro de routers (sin create_all)
│   ├── database/connection.py            # Engine, SessionLocal y Base
│   ├── models/
│   │   ├── user_model.py                 # Tabla users  (+ relación loans)
│   │   ├── device_model.py               # Tabla devices (+ relación loans)
│   │   └── loan_model.py                 # Tabla loans  (FK a users y devices)
│   ├── schemas/
│   │   ├── user_schema.py                # Contratos Pydantic de usuarios
│   │   ├── device_schema.py              # Contratos Pydantic de dispositivos
│   │   └── loan_schema.py                # Contratos Pydantic de préstamos (+ detalle)
│   ├── dependencies/                     # Sesión por petición, filtros y existencia (404)
│   ├── services/                         # Lógica de negocio y consultas SQLAlchemy
│   └── routes/                           # Endpoints HTTP y documentación OpenAPI
├── alembic/
│   ├── env.py                            # Configurado con Base.metadata y DATABASE_URL
│   └── versions/                         # Migraciones generadas
├── alembic.ini
├── requirements.txt
└── README.md
```

El recorrido de una petición es: **cliente → route → service → SQLAlchemy → SQLite**. Los servicios devuelven modelos ORM y los schemas Pydantic (`from_attributes=True`) los convierten a JSON.

## Migraciones con Alembic

Alembic versiona los cambios estructurales de la base de datos. La configuración clave está en `alembic/env.py`:

- `target_metadata = Base.metadata` y se importa el paquete `app.models`, de modo que `--autogenerate` detecta las tablas `users`, `devices` y `loans` y sus claves foráneas.
- `sqlalchemy.url` se toma de `connection.DATABASE_URL` (fuente única de verdad).
- `render_as_batch=True` para permitir cambios de esquema en SQLite (que no soporta `ALTER TABLE` completo).

Comandos usados:

```bash
# Generar la migración inicial a partir de los modelos
alembic revision --autogenerate -m "create users, devices and loans tables"

# Aplicar la migración (crea las tablas)
alembic upgrade head

# Consultar el historial de migraciones
alembic history

# Ver la revisión aplicada actualmente
alembic current
```

## Modelos y relaciones

| Modelo | Tabla     | Campos principales                                                        |
| ------ | --------- | ------------------------------------------------------------------------- |
| User   | `users`   | `id`, `name`, `email` (único), `role`, `is_active`, `created_at`          |
| Device | `devices` | `id`, `name`, `serial_number` (único), `device_type`, `brand`, `is_available`, `created_at` |
| Loan   | `loans`   | `id`, `user_id` (FK), `device_id` (FK), `loan_date`, `return_date`, `status` |

Relaciones definidas con `relationship()` y `back_populates`:

- **Usuario → préstamos** (One-to-Many): `User.loans` ↔ `Loan.user`.
- **Dispositivo → préstamos** (One-to-Many): `Device.loans` ↔ `Loan.device`.
- **Préstamo → usuario y dispositivo** (Many-to-One): cada `Loan` pertenece a un `User` y a un `Device`, garantizando integridad referencial mediante `ForeignKey`.

## Recurso `/users`

| Método | Ruta                | Operación                       |
| ------ | ------------------- | ------------------------------- |
| GET    | `/users`            | Lista, filtra y ordena usuarios |
| GET    | `/users/{user_id}`  | Consulta un usuario             |
| POST   | `/users`            | Crea un usuario (`201`)         |
| PUT    | `/users/{user_id}`  | Reemplazo completo              |
| PATCH  | `/users/{user_id}`  | Actualización parcial           |
| DELETE | `/users/{user_id}`  | Elimina un usuario (`204`)      |
| GET    | `/users/{user_id}/loans` | Préstamos del usuario (join) |

El DELETE conserva la seguridad simulada del proyecto anterior (`X-API-Key: device-systems-2026`).

## Recurso `/devices`

| Método | Ruta                       | Operación                          |
| ------ | -------------------------- | ---------------------------------- |
| GET    | `/devices`                 | Lista y filtra dispositivos        |
| GET    | `/devices/{device_id}`     | Consulta un dispositivo            |
| POST   | `/devices`                 | Crea un dispositivo (`201`)        |
| PUT    | `/devices/{device_id}`     | Reemplazo completo                 |
| PATCH  | `/devices/{device_id}`     | Actualización parcial              |
| DELETE | `/devices/{device_id}`     | Elimina un dispositivo (`204`)     |
| GET    | `/devices/{device_id}/loans` | Historial de préstamos (join)    |

Filtros del listado (query params): `device_type`, `is_available`, `brand` (parcial) y `search` (busca en nombre, serie y marca con `ilike`). Ejemplos:

```
GET /devices?device_type=laptop
GET /devices?is_available=true
GET /devices?brand=lenovo
GET /devices?search=thinkpad
```

## Recurso `/loans`

| Método | Ruta                      | Operación                                        |
| ------ | ------------------------- | ------------------------------------------------ |
| GET    | `/loans`                  | Lista préstamos con joins y filtros              |
| GET    | `/loans/details`          | Lista préstamos con usuario y dispositivo anidados |
| GET    | `/loans/{loan_id}`        | Consulta un préstamo con información relacionada  |
| POST   | `/loans`                  | Crea un préstamo (`201`)                          |
| PATCH  | `/loans/{loan_id}/return` | Registra la devolución del dispositivo           |

Reglas de negocio:

- **POST /loans**: valida que el usuario y el dispositivo existan, que el dispositivo esté disponible, crea el préstamo (`status="active"`) y marca el dispositivo como **no disponible**.
- **PATCH /loans/{id}/return**: valida que el préstamo exista y no esté ya devuelto, lo marca como `returned`, asigna `return_date` y vuelve a marcar el dispositivo como **disponible**.

## Consultas con joins y filtros

Las consultas combinan varias tablas usando `join()`, `where()`, `ilike()` y `or_()`, con precarga (`joinedload`) para evitar N+1:

```
GET /loans?status=active
GET /loans?user_email=ana@sena.edu.co
GET /loans?device_type=laptop
GET /users/{user_id}/loans
GET /devices/{device_id}/loans
```

Ejemplo de respuesta detallada (`/loans/details`):

```json
[
  {
    "id": 1,
    "status": "active",
    "loan_date": "2026-09-17T11:59:57",
    "return_date": null,
    "user": { "id": 1, "name": "Ana Perez", "email": "ana@sena.edu.co" },
    "device": { "id": 1, "name": "Laptop Lenovo ThinkPad", "serial_number": "LEN-2024-001", "device_type": "laptop" }
  }
]
```

## Manejo de errores

| Caso                                  | Código             |
| ------------------------------------- | ------------------ |
| Registro creado                       | `201 Created`      |
| Consulta / devolución exitosa         | `200 OK`           |
| Eliminación exitosa                   | `204 No Content`   |
| Recurso no encontrado                 | `404 Not Found`    |
| Dato duplicado (email / serie)        | `400 Bad Request`  |
| Regla de negocio incumplida           | `409 Conflict`     |
| Error de validación                   | `422 Unprocessable Entity` |

Reglas de negocio que devuelven `409`: intentar prestar un dispositivo **no disponible** e intentar **devolver un préstamo ya devuelto**.

## Pruebas funcionales realizadas

Se verificaron manualmente (Uvicorn + `curl`) los escenarios mínimos de la guía, todos con el código HTTP esperado:

1. Ejecutar migraciones con Alembic (`upgrade head`, `history`, `current`). ✅
2. Crear usuario (`201`). ✅
3. Crear dispositivo (`201`) y serie duplicada (`400`). ✅
4. Crear préstamo (`201`). ✅
5. Intentar prestar un dispositivo no disponible (`409`). ✅
6. Préstamo con usuario/dispositivo inexistente (`404`). ✅
7. Listar préstamos con información de usuario y dispositivo (joins). ✅
8. Filtrar préstamos por estado, email de usuario y tipo de dispositivo. ✅
9. Consultar préstamos de un usuario y el historial de un dispositivo. ✅
10. Devolver un dispositivo (`200`) y verificar que vuelve a estar disponible. ✅
11. Devolver un préstamo ya devuelto (`409`) e inexistente (`404`). ✅
12. Filtro inválido (`422`). ✅

## Evidencias de funcionamiento

Las capturas del CRUD de usuarios de la versión anterior se conservan en `docs/`. Para esta entrega deben agregarse a `docs/` las siguientes evidencias (referenciadas aquí):

### Migraciones con Alembic

- Captura de `alembic init` (o de la carpeta `alembic/` configurada).
- Captura de `alembic revision --autogenerate -m "create users, devices and loans tables"`.
- Captura de `alembic upgrade head`.
- Captura de la estructura de tablas generadas (por ejemplo `alembic history` o el esquema en un visor de SQLite).

### Swagger UI y ReDoc

Swagger permite probar los endpoints desde `/docs`, organizados por tags **Users**, **Devices** y **Loans**.

![Swagger UI de device_systems](docs/swagger-ui.png)
![ReDoc de device_systems](docs/redoc.png)

### CRUD del recurso users (evidencias existentes)

| Evidencia             | Captura                                       |
| --------------------- | --------------------------------------------- |
| Listado y filtros     | [get-users.png](docs/get-users.png)           |
| Consulta por ID       | [get-user-by-id.png](docs/get-user-by-id.png) |
| Creación              | [post-users.png](docs/post-users.png)         |
| Reemplazo completo    | [put-users.png](docs/put-users.png)           |
| Actualización parcial | [patch-users.png](docs/patch-users.png)       |
| Eliminación           | [delete-users.png](docs/delete-users.png)     |
| Validaciones          | [validaciones.png](docs/validaciones.png)     |

### Evidencias nuevas sugeridas

- Creación de usuario, dispositivo y préstamo.
- Consultas con joins (`/loans/details`).
- Filtros aplicados (`/loans?status=active`, `/devices?search=...`).
- Devolución de dispositivo y verificación de disponibilidad.

## Reflexión

Las **migraciones** permiten evolucionar el esquema de forma controlada y versionada, sin perder datos ni depender de `create_all`. Las **relaciones** con claves foráneas y `relationship()` garantizan integridad referencial y modelan el dominio real (un usuario tiene muchos préstamos; un dispositivo acumula un historial). Las **consultas con joins y filtros** convierten la API en una herramienta de análisis: no solo almacena datos, sino que responde preguntas que cruzan varias tablas.
