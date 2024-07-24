# Используем pydantic для упрощения работы при перегонке данных из json в объекты
from pydantic import BaseModel


class Film(BaseModel):
    id: str
    title: str
    description: str


class Movie(BaseModel):
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