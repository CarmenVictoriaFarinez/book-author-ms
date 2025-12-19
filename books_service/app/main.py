from fastapi import FastAPI, Depends, HTTPException
import os
import psycopg2
from sqlalchemy.orm import Session
from typing import List
from app.database import engine, Base, get_db
from app import models, schemas
from app.schemas import AuthorForBook

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Microservicio de Libros",
    description="Servicio encargado de la gestión de libros y sus autores",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {
        "service": "Books Service",
        "status": "Online",
        "port": 8001,
        "message": "Bienvenido al sistema de gestión de libros"
    }

@app.get("/health")
def health_check():
    try:
        # Verificamos si podemos conectar a la DB
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.post("/books/", response_model=schemas.Book)
def create_book(book: schemas.BookCreate, db: Session = Depends(get_db)):
    # Creamos el objeto Libro
    db_book = models.Book(title=book.title, description=book.description)

    # Asociamos los autores existentes al libro
    for author_id in book.author_ids:
        # Buscamos el autor en la base de datos
        author = db.query(AuthorModel).get(author_id)
        if not author:
            raise HTTPException(status_code=404, detail=f"Author {author_id} not found")
        # Usamos la relación definida en models.py para añadir el autor al libro
        db_book.authors.append(author)

    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book
