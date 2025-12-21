"""
authors_service/app/main.py

Microservicio de Autores (FastAPI) con soporte de consulta de libros asociados.

Objetivo del ejercicio:
- Un autor puede tener varios libros.
- Un libro puede tener uno o varios autores.
- Debe existir relación entre ambos elementos y se debe poder consultar y asignar
  libros a autores y autores a libros.

Decisión práctica (para este ejercicio):
- Ambos microservicios comparten un único PostgreSQL (library_db).
- Aun compartiendo BD, este servicio consulta libros asociados llamando al
  microservicio de libros vía HTTP (BOOKS_SERVICE_URL). Esto demuestra integración
  entre microservicios.

Endpoints principales:
- POST /authors/                 -> crea autor
- GET  /authors/                 -> lista autores
- GET  /authors/{author_id}      -> obtiene un autor por id (útil para validación desde books_service)
- GET  /authors/{author_id}/books-> consulta libros asociados (vía books_service)
- GET  /health                   -> healthcheck con verificación DB
"""

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os
import json
import psycopg2
import urllib.request
import urllib.error

from app.database import engine, Base, get_db
from app import models, schemas

# Crea tablas si no existen (para un ejercicio es aceptable; en producción usar Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Microservicio de Autores",
    description="Servicio encargado de la gestión de autores y consulta de sus libros",
    version="1.0.0",
)


# ---------------------------------------------------------------------
# Helpers: comunicación con books_service (consulta)
# ---------------------------------------------------------------------

def _books_base_url() -> str:
    """
    URL base del microservicio de libros (comunicación interna en Docker).
    Ejemplo: http://books_service:8000
    """
    return os.getenv("BOOKS_SERVICE_URL", "http://books_service:8000").rstrip("/")


def _fetch_books_by_author(author_id: int) -> dict:
    """
    Llama a books_service para obtener libros relacionados con un autor.
    Espera que books_service exponga:
      GET /books/by-author/{author_id}
    """
    url = f"{_books_base_url()}/books/by-author/{author_id}"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # books_service respondió con un error (404/422/500...)
        raise HTTPException(
            status_code=e.code,
            detail=f"Books service error: {e.read().decode('utf-8')}"
        )
    except Exception as e:
        # no se pudo conectar al servicio
        raise HTTPException(status_code=503, detail=f"Books service unavailable: {str(e)}")


# ---------------------------------------------------------------------
# Endpoints principales
# ---------------------------------------------------------------------

@app.post("/authors/", response_model=schemas.Author)
def create_author(author: schemas.AuthorCreate, db: Session = Depends(get_db)):
    """
    Crea un autor.

    Body esperado (según tu schemas.AuthorCreate):
    {
      "name": "Nombre",
      "bio": "opcional"
    }
    """
    db_author = models.Author(name=author.name, bio=author.bio)
    db.add(db_author)
    db.commit()
    db.refresh(db_author)
    return db_author


@app.get("/authors/", response_model=List[schemas.Author])
def read_authors(db: Session = Depends(get_db)):
    """Lista todos los autores."""
    return db.query(models.Author).all()


@app.get("/authors/{author_id}", response_model=schemas.Author)
def read_author(author_id: int, db: Session = Depends(get_db)):
    """
    Obtiene un autor por id.

    Este endpoint es útil para que books_service valide autores existentes:
      GET http://authors_service:8000/authors/{id}
    """
    author = db.query(models.Author).filter(models.Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    return author


@app.get("/authors/{author_id}/books")
def read_author_books(author_id: int, db: Session = Depends(get_db)):
    """
    Devuelve libros asociados a un autor.

    Flujo:
    1) Verifica que el autor exista localmente.
    2) Llama a books_service (/books/by-author/{author_id}) para obtener sus libros.
    """
    author = db.query(models.Author).filter(models.Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    return _fetch_books_by_author(author_id)


# ---------------------------------------------------------------------
# Utilidad / Observabilidad básica
# ---------------------------------------------------------------------

@app.get("/")
def read_root():
    return {
        "service": "Authors Service",
        "status": "Online",
        "db_status": "Conectado",
        "message": "Bienvenido al sistema de gestión de autores",
    }


@app.get("/health")
def health_check():
    """
    Healthcheck simple:
    - Devuelve healthy si puede abrir y cerrar conexión a la BD.
    """
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
