from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.services.film import FilmService, get_film_service

router = APIRouter()


class UUIDMixin(BaseModel):
    uuid: str = Field(alias='id')


class FullFilm(UUIDMixin):
    imdb_rating: float | None
    title: str
    description: str | None
    genres: list[str]
    directors_names: list[str]
    actors_names: list[str]
    writers_names: list[str]
    class PersonEntity(UUIDMixin):
        name: str
    directors: list[PersonEntity]
    actors: list[PersonEntity]
    writers: list[PersonEntity]


class Film(BaseModel):
    id: str
    title: str


@router.get('/{film_id}', response_model=Film)
async def film_details(film_id: str, film_service: FilmService = Depends(get_film_service)) -> Film:
    film = await film_service.get_by_id(film_id)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='film not found')

    return Film(id=film.id, title=film.title)


@router.get('/search')
async def search_films_by_title(
        page_size: int = 10,
        page: int = 1,
        sort: str = 'imdb_rating',
        query: str = None,
        film_service: FilmService = Depends(get_film_service)
):
    films = await film_service.all(page_size=page_size, page=page, sort=sort, query=query)
    return films


@router.get('/', response_model=list[Film])
async def get_films(
        page_size: int = 10,
        page: int = 1,
        sort: str = 'imdb_rating',
        genre: str = None,
        film_service: FilmService = Depends(get_film_service)
) -> list[Film]:
    films = await film_service.all(page_size=page_size, page=page, sort=sort, genre=genre)
    return films

