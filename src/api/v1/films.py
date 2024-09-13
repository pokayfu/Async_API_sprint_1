from http import HTTPStatus
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
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
        page_size: Annotated[int, Query(description='Pagination page size', ge=1)] = 10,
        page: Annotated[int, Query(description='Pagination page number', ge=1)] = 1,
        sort: Annotated[str, Query(description='Sorting field')] = 'imdb_rating',
        genre: Annotated[str, Query(description='Filter by genre')] = None,
        film_service: FilmService = Depends(get_film_service)
) -> list[Film]:
    films = await film_service.all(page_size=page_size, page=page, sort=sort, genre=genre)
    return films

@router.get('/search/', response_model=list[FilmPreview])
async def search_films_by_title(
        page_size: Annotated[int, Query(description='Pagination page size', ge=1)] = 10,
        page: Annotated[int, Query(description='Pagination page number', ge=1)] = 1,
        sort: Annotated[str, Query(description='Sorting field')] = 'imdb_rating',
        query: Annotated[str, Query(description='Search by film name')] = None,
        film_service: FilmService = Depends(get_film_service)
) -> list[FilmPreview]:
    films = await film_service.all(page_size=page_size, page=page, sort=sort, query=query)
    return films