from pydantic import BaseModel, ConfigDict
from typing import List, Optional

# Definimos una versión local (ligera) del Autor solo para mostrarlo dentro del libro
class AuthorForBook(BaseModel):
    id: int
    name: str
    bio: Optional[str] = None
    class Config:
        from_attributes = True

class BookBase(BaseModel):
    title: str
    description: Optional[str] = None

class BookCreate(BookBase):
    # Cuando creas un libro, envías los IDs de los autores existentes
    author_ids: List[int] = []

class Book(BookBase):
    id: int
    # Cuando obtienes un libro, quieres ver la lista completa de objetos Author
    authors: List[AuthorForBook] = [] # Usamos la clase localmente definida

    class Config:
        from_attributes = True

class SetBookAuthorsRequest(BaseModel):
    author_ids: List[int]

