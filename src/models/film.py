# Используем pydantic для упрощения работы при перегонке данных из json в объекты
from pydantic import BaseModel


# class Film(BaseModel):
#     id: str
#     title: str
#     description: str | None


class Genre(BaseModel):
    name: str


class Person(BaseModel):
    name: str


class Film(BaseModel):
    id: str
    title: str
    imdb_rating: float = 0.0
    description: str | None
    genre: list = []
    actors: list[Person] = []
    writers: list[Person] = []
    directors: list[Person] = []