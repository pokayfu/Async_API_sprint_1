from pydantic import BaseModel, Field
from uuid import UUID

class Person(BaseModel):
   person_id: UUID #= Field(alias='person_id')
   full_name: str
   class FilmEntity(BaseModel):
      id: UUID
      roles: list[str]
   films: list[FilmEntity]

class FilmsByPerson(BaseModel):
   id: UUID
   title: str
   imdb_rating: float
   