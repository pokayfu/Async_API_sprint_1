
from http import HTTPStatus
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from src.models.genre import Genre
from src.services.genre import GenreService, get_genre_service
from fastapi import APIRouter, Depends, HTTPException, Query


router = APIRouter()

@router.get('/', response_model=list[Genre])
async def get_genres(
        page_size: Annotated[int, Query(description='Pagination page size', ge=1)] = 10,
        page: Annotated[int, Query(description='Pagination page number', ge=1)] = 1,
        genre_service: GenreService = Depends(get_genre_service)
) -> list[Genre]:
    films = await genre_service.all(page_size=page_size, page=page)
    return films

@router.get('/{genre_id}', response_model=Genre)
async def genre_details(genre_id: str, genre_service: GenreService = Depends(get_genre_service)) -> Genre:
    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='genre not found')
    return genre.model_dump()
