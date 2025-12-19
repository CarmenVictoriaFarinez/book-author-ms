from pydantic import BaseModel
from typing import List, Optional

class AuthorBase(BaseModel):
    name: str
    bio: Optional[str] = None

class AuthorCreate(AuthorBase):
    pass

class Author(AuthorBase):
    id: int
    
    class Config:
        from_attributes = True # Esto permite que Pydantic lea modelos de SQLAlchemy
