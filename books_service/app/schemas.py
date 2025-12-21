from pydantic import BaseModel, ConfigDict
from typing import List, Optional

# Definimos una versión local (ligera) del Autor solo para mostrarlo dentro del libro
class AuthorForBook(BaseModel):
    id: int
    name: str
    bio: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class BookBase(BaseModel):
    title: str
    description: Optional[str] = None

class BookCreate(BookBase):
    # Cuando creas un libro, envías los IDs de los autores existentes
    author_ids: List[int] = []

class Book(BookBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
    # Cuando obtienes un libro, quieres ver la lista de autores
    authors: List[AuthorForBook] = []

class SetBookAuthorsRequest(BaseModel):
    author_ids: List[int]

