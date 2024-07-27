
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from src.models.persons import Person, FilmsByPerson
from src.services.persons import PersonService, get_person_service

router = APIRouter()

@router.get('/search', response_model=list[Person])
async def get_persons(
        page_size: int = 10,
        page: int = 1,
        query: str = "",
        person_service: PersonService = Depends(get_person_service)
) -> list[Person]:
    persons = await person_service.all(page_size=page_size, page=page, query=query)
    return persons



@router.get('/{person_id}', response_model=Person)
async def person_details(person_id: UUID, person_service: PersonService = Depends(get_person_service)) -> Person:
    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person not found')
    return person.model_dump()

@router.get('/{id}/film/', response_model=list[FilmsByPerson])
async def films_by_person(person_id: UUID, person_service: PersonService = Depends(get_person_service)):
    films = await person_service.get_films_by_person(person_id)
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person or films by person  not found')
    return films
