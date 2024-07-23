from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException

from src.models.genre import Genre
from src.services.genre import GenreService, get_genre_service

router = APIRouter(tags=['genre'])


@router.get('/{genre_id}', response_model=Genre)
async def film_details(genre_id: str, genre_service: GenreService = Depends(get_genre_service)) -> Genre:
    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='genre not found')

    return Genre(name=genre.name)


@router.get('/', response_model=list[Genre])
async def get_genres(
        page_size: int = 10,
        page: int = 1,
        sort: str = 'name',
        genre_service: GenreService = Depends(get_genre_service)
) -> list[Genre]:
    genres = await genre_service.all(page_size, page, sort)
    return genres


@router.get('/search')
async def search_genres_by_name(
        page_size: int = 10,
        page: int = 1,
        sort: str = 'name',
        query: str = None,
        genre_service: GenreService = Depends(get_genre_service)
):
    genres = await genre_service.search(page_size, page, sort, query)
    return genres
