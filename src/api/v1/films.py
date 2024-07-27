from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException

from src.models.film import Film, FilmPreview
from src.services.film import FilmService, get_film_service

router = APIRouter()


@router.get('/{film_id}', response_model=Film)
async def film_details(film_id: str, film_service: FilmService = Depends(get_film_service)) -> Film:
    film = await film_service.get_by_id(film_id)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='film not found')

    return Film(**film.model_dump(by_alias=True))


@router.get('/', response_model=list[FilmPreview])
async def get_films(
        page_size: int = 10,
        page: int = 1,
        sort: str = 'imdb_rating',
        genre: str = None,
        film_service: FilmService = Depends(get_film_service)
) -> list[Film]:
    films = await film_service.all(page_size=page_size, page=page, sort=sort, genre=genre)
    return films


@router.get('/search/', response_model=list[FilmPreview])
async def search_films_by_title(
        page_size: int = 10,
        page: int = 1,
        sort: str = 'imdb_rating',
        query: str = None,
        film_service: FilmService = Depends(get_film_service)
) -> list[FilmPreview]:
    films = await film_service.all(page_size=page_size, page=page, sort=sort, query=query)
    return films