from fastapi import FastAPI, Depends, HTTPException
import os
import psycopg2
from sqlalchemy.orm import Session
from typing import List
from app.database import engine, Base, get_db
from app import models, schemas

# Intentamos la creación
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Servicio de Autores")

@app.post("/authors/", response_model=schemas.Author)
def create_author(author: schemas.AuthorCreate, db: Session = Depends(get_db)):
    db_author = models.Author(name=author.name, bio=author.bio)
    db.add(db_author)
    db.commit()
    db.refresh(db_author)
    return db_author

@app.get("/authors/", response_model=List[schemas.Author])
def read_authors(db: Session = Depends(get_db)):
    return db.query(models.Author).all()


# Prueba de conexión rápida a la base de datos
@app.get("/")
def read_root():
    return {"message": "El servicio de Autores está funcionando", "db_status": "Conectado"}

@app.get("/health")
def health_check():
    # Intentamos conectar a la DB para verificar que hay comunicación
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        conn.close()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
