# book-author-ms

Sistema de gestión de **libros** y **autores** implementado con **microservicios (FastAPI)**, persistencia en **PostgreSQL** y despliegue local con **Docker Compose**.

---

## 1) Enunciado y alcance

**Relación requerida:**
- Un **autor** puede tener **varios libros**.
- Un **libro** puede tener **uno o varios autores**.
- Se debe poder **consultar** y **asignar** autores ↔ libros.

---

## 2) Arquitectura

Servicios incluidos:

- **authors_service** (FastAPI)
  - CRUD de autores.
  - Consulta de libros asociados a un autor.
  - Endpoint para “asignar libros a un autor” (sin duplicar lógica de relación).

- **books_service** (FastAPI)
  - CRUD de libros.
  - Consulta de autores de un libro.
  - Endpoint para asignar/reemplazar autores de un libro.

- **postgres_db** (PostgreSQL 16)
  - Persistencia SQL con volumen Docker.

- *(Opcional)* **redis_broker** (Redis)
  - Incluido como infraestructura proyectada para escalabilidad.
  **Justificación:** Se previó inicialmente la implementación de lógica asíncrona para la sincronización de datos. Se eligió Redis sobre Kafka por su ligereza y menor complejidad operativa, curva de aprendizaje, y porque Redis es mucho más rápido para notificaciones en tiempo real entre servicios pequeños.

---

## 3) Decisiones técnicas (justificación)

### 3.1 Microservicios y separación de responsabilidades
Se separa el dominio en dos servicios independientes:
- `authors_service` se responsabiliza de **autores**.
- `books_service` se responsabiliza de **libros**.

Esto permite evolucionar cada servicio por separado (código, tests, escalado, despliegue).

### 3.2 Persistencia (PostgreSQL) y relación muchos-a-muchos
Se usa PostgreSQL y una tabla intermedia `book_authors` para modelar la relación **M:N**:
- `authors` ↔ `books` (N:N) mediante `book_authors`.

### 3.3 Base de datos compartida (decisión práctica del ejercicio)
Ambos servicios apuntan al mismo `library_db`.

**Pros:**
- Reduce complejidad en un ejercicio corto (no hace falta consistencia eventual ni eventos).
- Permite consultas y joins sencillos para validar rápidamente la relación M:N.

**Contras (en un entorno productivo):**
- Acopla servicios a un mismo esquema y complica independencia total.
- Lo ideal sería base de datos por servicio y sincronización por eventos/contratos.

> En esta entrega se prioriza una solución estable y demostrable en local.

### 3.4 Comunicación entre microservicios (HTTP interno en Docker)
Además de compartir BD, se implementa comunicación HTTP interna para demostrar integración:
- `books_service` valida autores consultando `authors_service` (por ID).
- `authors_service` consulta libros asociados llamando a `books_service`.

Esto se configura con variables de entorno:
- `AUTHORS_SERVICE_URL=http://authors_service:8000`
- `BOOKS_SERVICE_URL=http://books_service:8000`

### 3.5 Observabilidad mínima (logs + métricas)
Cada servicio incluye:
- **Logging por request**: método, path, status, duración y request_id.
- **Métricas Prometheus** en `/metrics`:
  - `http_requests_total{method,path,status}`
  - `http_request_duration_seconds_*`

### 3.6 Tests
Se incluyen tests básicos con `pytest` (smoke tests) para validar que el servicio responde.

---

## 4) Persistencia: no perder datos

La base de datos se persiste con un volumen nombrado:

- `postgres_data:/var/lib/postgresql/data`

✅ Esto mantiene datos aunque reinicies contenedores o cierres la sesión.

⚠️ No ejecutar:
docker compose down -v

## 5) Cómo levantar el proyecto

### Requisitos
- Docker + Docker Compose

### Levantar todo (build + run)
docker compose up -d --build

## 6) Puertos y Swagger

- **Authors Service**: `http://localhost:8000`
  - Swagger: `http://localhost:8000/docs`
  - OpenAPI: `http://localhost:8000/openapi.json`

- **Books Service**: `http://localhost:8001`
  - Swagger: `http://localhost:8001/docs`
  - OpenAPI: `http://localhost:8001/openapi.json`

Healthchecks:
- `GET http://localhost:8000/health`
- `GET http://localhost:8001/health`

---

## 7) Observabilidad: logs y métricas

### Logs por request
Cada servicio registra por request:
- `request_id` (header `X-Request-Id`)
- método + path
- status code
- duración (ms)

Ver logs en vivo:
docker compose logs -f authors_service
docker compose logs -f books_service

## 8) Métricas (Prometheus)

Cada microservicio expone métricas en:

- Authors: `GET http://localhost:8000/metrics`
- Books: `GET http://localhost:8001/metrics`

> Nota: `/metrics` **no aparece en Swagger** porque normalmente se marca con `include_in_schema=False`.

### Probar métricas rápidamente
curl -s http://localhost:8000/metrics | head -n 30
curl -s http://localhost:8001/metrics | head -n 30

## 9) Tests (pytest)

Los tests se ejecutan dentro de los contenedores para asegurar que corren en el mismo entorno que Docker.

### Ejecutar tests
docker compose exec authors_service pytest -q
docker compose exec books_service pytest -q

## 10) Endpoints

### Authors Service (Puerto 8000)

**Base URL**
- `http://localhost:8000`

**Swagger**
- `http://localhost:8000/docs`

#### Endpoints funcionales
- `POST /authors/`  
  Crea un autor.

- `GET /authors/`  
  Lista todos los autores.

- `GET /authors/{author_id}`  
  Obtiene el detalle de un autor (y sirve para validación desde `books_service`).

- `GET /authors/{author_id}/books`  
  Lista libros asociados a un autor (consultando al microservicio de libros).

- `PUT /authors/{author_id}/books`
  Asigna (agrega) libros a un autor.  
  **Body:**
  ```json
  { "book_ids": [1, 2, 3] }

  #### Endpoints operativos

- `GET /health`  
  Healthcheck con verificación de conexión a DB.

- `GET /metrics`  
  Métricas Prometheus.

---

## Books Service (Puerto 8001)

### Base URL
- `http://localhost:8001`

### Swagger
- `http://localhost:8001/docs`

### Endpoints funcionales

- `POST /books/`  
  Crea un libro (opcionalmente con autores existentes).  
  **Body:**
  ```json
  { "title": "Mi libro", "description": "Desc", "author_ids": [1,2] }

- `GET /books/`  
  Lista libros.

- `GET /books/{book_id}`  
  Detalle de libro.

- `GET /books/{book_id}/authors`  
  Lista autores asociados a un libro.

- `PUT /books/{book_id}/authors`  
  Reemplaza por completo la lista de autores del libro (modo **replace**).  
  **Body:**
  ```json
  { "author_ids": [1,2,3] }

- `GET /books/by-author/{author_id}`
    Lista libros asociados a un autor (endpoint consumido por authors_service).

Endpoints operativos

- `GET /health`
Healthcheck con verificación de conexión a DB.

- `GET /metrics`  
Métricas Prometheus.
