"""
books_service/app/main.py

Microservicio de Libros (FastAPI) con relación Muchos-a-Muchos Libros <-> Autores.

Objetivo del ejercicio:
- Un autor puede tener varios libros.
- Un libro puede tener uno o varios autores.
- Debe existir relación entre ambos y se debe poder consultar y asignar libros/autores.

Decisión práctica (para este ejercicio):
- Se comparte un único PostgreSQL (library_db) entre ambos microservicios.
- Aun compartiendo BD, mantenemos comunicación entre servicios vía HTTP para validar
  la existencia de autores (AUTHORS_SERVICE_URL), lo cual demuestra integración
  entre microservicios.

Endpoints clave:
- POST /books/                 -> crea libro (opcionalmente asigna author_ids)
- PUT  /books/{id}/authors     -> reemplaza autores del libro
- GET  /books/by-author/{id}   -> devuelve libros de un autor (para authors_service)
- GET  /health                 -> healthcheck con verificación DB
"""

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from typing import List, Dict, Any
import os
import psycopg2
import urllib.request
import urllib.error

from app.database import engine, Base, get_db
from app import models, schemas

# Crea tablas si no existen (para un ejercicio es aceptable; en producción usar Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Microservicio de Libros",
    description="Servicio encargado de la gestión de libros y su relación con autores",
    version="1.0.0",
)


# ---------------------------------------------------------------------
# Helpers: comunicación con authors_service (validación)
# ---------------------------------------------------------------------

def _authors_base_url() -> str:
    """
    URL base del microservicio de autores (comunicación interna en Docker).
    Ejemplo: http://authors_service:8000
    """
    return os.getenv("AUTHORS_SERVICE_URL", "http://authors_service:8000").rstrip("/")


def _assert_author_exists(author_id: int) -> None:
    """
    Comprueba que el autor existe consultando el microservicio authors_service.
    Si el servicio está caído, devolvemos 503.
    Si el autor no existe, devolvemos 404.

    Esto demuestra integración entre microservicios (aunque compartan BD).
    """
    url = f"{_authors_base_url()}/authors/{author_id}"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            if resp.status != 200:
                raise HTTPException(status_code=404, detail=f"Author {author_id} not found")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise HTTPException(status_code=404, detail=f"Author {author_id} not found")
        raise HTTPException(status_code=502, detail=f"Authors service error ({e.code})")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Authors service unavailable: {str(e)}")


# ---------------------------------------------------------------------
# Endpoints principales
# ---------------------------------------------------------------------

# -------------------------------
# GET /books/ (listar libros)
# -------------------------------
@app.get("/books/", response_model=List[schemas.Book])
def list_books(db: Session = Depends(get_db)):
    """
    Lista todos los libros.

    Devuelve una lista de libros incluyendo sus autores (si los tiene).
    """
    stmt = (
        select(models.Book)
        .options(joinedload(models.Book.authors))
        .order_by(models.Book.id)
    )
    return db.execute(stmt).scalars().unique().all()


# -------------------------------
# GET /books/{book_id} (detalle)
# -------------------------------
@app.get("/books/{book_id}", response_model=schemas.Book)
def get_book(book_id: int, db: Session = Depends(get_db)):
    """
    Devuelve el detalle de un libro por ID.

    Incluye lista de autores gracias a la relación ORM.
    """
    stmt = (
        select(models.Book)
        .options(joinedload(models.Book.authors))
        .where(models.Book.id == book_id)
    )
    book = db.execute(stmt).scalars().unique().first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


# -------------------------------
# GET /books/{book_id}/authors
# -------------------------------
@app.get("/books/{book_id}/authors", response_model=List[schemas.AuthorForBook])
def get_book_authors(book_id: int, db: Session = Depends(get_db)):
    """
    Devuelve SOLO los autores de un libro.
    """
    stmt = (
        select(models.Book)
        .options(joinedload(models.Book.authors))
        .where(models.Book.id == book_id)
    )
    book = db.execute(stmt).scalars().unique().first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book.authors


# -------------------------------
# POST /books (Crea libro)
# -------------------------------
@app.post("/books/", response_model=schemas.Book)
def create_book(book: schemas.BookCreate, db: Session = Depends(get_db)):
    """
    Crea un libro.

    Nota:
    - Valida autores vía authors_service (HTTP).
    - Inserta relación usando el ORM: book.authors.append(author)
    """
    db_book = models.Book(title=book.title, description=book.description)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)

    author_ids = getattr(book, "author_ids", None) or []
    author_ids = [int(a) for a in author_ids]

    if author_ids:
        for aid in author_ids:
            _assert_author_exists(aid)

        for aid in author_ids:
            author = db.scalar(select(models.Author).where(models.Author.id == aid))
            if not author:
                raise HTTPException(status_code=404, detail=f"Author {aid} not found in DB")
            db_book.authors.append(author)

        db.commit()
        db.refresh(db_book)

    return db_book


# -------------------------------
# PUT /books/{book_id}/authors (replace)
# -------------------------------
@app.put("/books/{book_id}/authors")
def set_book_authors(book_id: int, payload: schemas.SetBookAuthorsRequest, db: Session = Depends(get_db)):
    """
    Reemplaza la lista de autores de un libro (modo 'replace').

    Body esperado:
      { "author_ids": [1, 2, 3] }
    """
    book = db.scalar(select(models.Book).where(models.Book.id == book_id))
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # ✅ Pydantic model -> se accede por atributo
    author_ids = payload.author_ids
    if not isinstance(author_ids, list):
        raise HTTPException(status_code=422, detail="author_ids must be a list")

    author_ids = [int(a) for a in author_ids]

    # Validar por microservicio
    for aid in author_ids:
        _assert_author_exists(aid)

    # Traer autores de BD (compartida) y validar "missing"
    stmt = select(models.Author).where(models.Author.id.in_(author_ids))
    authors = db.execute(stmt).scalars().all()

    found = {a.id for a in authors}
    missing = [aid for aid in author_ids if aid not in found]
    if missing:
        raise HTTPException(status_code=404, detail=f"Authors not found in DB: {missing}")

    # Replace completo
    book.authors = authors
    db.commit()

    return {"book_id": book_id, "author_ids": [a.id for a in book.authors]}


# -------------------------------
# GET /books/by-author/{author_id}
# -------------------------------
@app.get("/books/by-author/{author_id}")
def get_books_by_author(author_id: int, db: Session = Depends(get_db)):
    """
    Devuelve libros asociados a un autor.
    Este endpoint lo consume authors_service en:
      GET /authors/{author_id}/books
    """
    stmt = (
        select(models.Book.id, models.Book.title, models.Book.description)
        .join(models.book_authors, models.book_authors.c.book_id == models.Book.id)
        .where(models.book_authors.c.author_id == author_id)
        .order_by(models.Book.id)
    )
    rows = db.execute(stmt).mappings().all()
    return {"author_id": author_id, "books": list(rows)}



# ---------------------------------------------------------------------
# Utilidad / Observabilidad básica
# ---------------------------------------------------------------------

@app.get("/")
def read_root():
    return {
        "service": "Books Service",
        "status": "Online",
        "db_status": "Conectado",
        "message": "Bienvenido al sistema de gestión de libros",
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
