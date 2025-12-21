from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class AuthorBase(BaseModel):
    name: str
    bio: Optional[str] = None

class AuthorCreate(AuthorBase):
    pass

class Author(AuthorBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class SetAuthorBooksRequest(BaseModel):
    book_ids: List[int]

