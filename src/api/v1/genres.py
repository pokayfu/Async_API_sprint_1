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
