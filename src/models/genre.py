from pydantic import BaseModel


class Genre(BaseModel):
    """Класс для описания жанра"""
    id: str
    name: str
    description: str | None

