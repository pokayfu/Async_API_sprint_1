
# Используем pydantic для упрощения работы при перегонке данных из json в объекты
from pydantic import BaseModel


class Film(BaseModel):
    id: str
    title: str
    description: str


class Actor(BaseModel):
    """Класс для описания актёра"""
    uuid: str
    name: str


class Writer(BaseModel):
    """Класс для описания сценариста"""
    uuid: str
    name: str


class Director(BaseModel):
    """Класс для описания режиссёра"""
    uuid: str
    name: str


class FullFilm(BaseModel):
    """Класс для описания всех деталий фильма"""
    id: str
    imdb_rating: float | None
    title: str
    description: str | None
    genres: list[str]
    directors_names: list[str]
    actors_names: list[str]
    writers_names: list[str]
    class PersonEntity(BaseModel):
        id: str
        name: str
    directors: list[PersonEntity]
    actors: list[PersonEntity]
    writers: list[PersonEntity]
