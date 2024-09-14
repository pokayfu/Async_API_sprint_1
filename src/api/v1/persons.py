
from http import HTTPStatus
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from src.models.persons import Person, FilmsByPerson
from src.services.persons import PersonService, get_person_service
from fastapi import APIRouter, Depends, HTTPException, Query


router = APIRouter()


@router.get('/search', response_model=list[Person], summary='Search persons by name with pagination'
)
async def get_persons(
        page_size: Annotated[int, Query(description='Pagination page size', ge=1)] = 10,
        page: Annotated[int, Query(description='Pagination page number', ge=1)] = 1,
        query: Annotated[str, Query(description='Search by person name')] = '',
        person_service: PersonService = Depends(get_person_service)
) -> list[Person]:
    """
    Perform a search for persons by their optional name. Supports pagination to handle large result sets.
    The response includes id, full name, films, and the person's specific role in each film, such as actor, writer, etc.
    """
    persons = await person_service.all(page_size=page_size, page=page, query=query)
    return persons


@router.get('/{person_id}', response_model=Person, summary='Retrieve person details by ID')
async def person_details(person_id: str, person_service: PersonService = Depends(get_person_service)) -> Person:
    """
    Fetch detailed information (including ID, full name, films, and the person's specific role in each film,
    such as actor, writer, etc.) about a specific person by providing their unique person ID.
    If the person is not found, a 404 error will be returned.
    """
    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person not found')
    return person.model_dump()


@router.get('/{person_id}/film', response_model=list[FilmsByPerson],
            summary='Retrieve films related to a specific person')
async def films_by_person(person_id: str, person_service: PersonService = Depends(get_person_service)):
    """
    Fetch a list of films in which a specific person was involved, based on their unique person ID.
    If the person or films are not found, a 404 error will be returned.
    """
    films = await person_service.get_films_by_person(person_id)
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person or films by person  not found')
    return films
