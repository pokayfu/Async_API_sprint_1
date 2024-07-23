from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException

from src.models.person import Person
from src.services.person import get_person_service, PersonService

router = APIRouter(tags=['person'])


@router.get('/{person_id}', response_model=Person)
async def film_details(person_id: str, person_service: PersonService = Depends(get_person_service)) -> Person:
    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person not found')

    return Person(name=person.name)


@router.get('/', response_model=list[Person])
async def get_persons(
        page_size: int = 10,
        page: int = 1,
        sort: str = 'imdb_rating',
        person_service: PersonService = Depends(get_person_service)
) -> list[Person]:
    persons = await person_service.all(page_size, page, sort)
    return persons


@router.get('/search')
async def search_persons_by_name(
        page_size: int = 10,
        page: int = 1,
        sort: str = 'imdb_rating',
        query: str = None,
        person_service: PersonService = Depends(get_person_service)
):
    persons = await person_service.search(page_size, page, sort, query)
    return persons
