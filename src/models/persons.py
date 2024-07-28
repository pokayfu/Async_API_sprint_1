from pydantic import BaseModel, Field


class Person(BaseModel):
   person_id: str
   full_name: str
   class FilmEntity(BaseModel):
      id: str
      roles: list[str]
   films: list[FilmEntity]

class FilmsByPerson(BaseModel):
   id: str
   title: str
   imdb_rating: float
   