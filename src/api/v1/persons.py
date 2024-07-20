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