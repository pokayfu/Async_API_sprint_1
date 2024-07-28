from pydantic import BaseModel
from typing import Optional


class Genre(BaseModel):
    """Класс для описания жанра"""
    id: str
    name: str
    description: Optional[str]

