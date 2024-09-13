from typing import Dict, List

from pydantic import BaseModel, Field


class PersonModel(BaseModel):
    """Model representing a person."""
    person_id: str
    person_name: str
    person_role: str


ROLES: Dict[str, str] = {
    'directors': 'director',
    'actors': 'actor',
    'writers': 'writer'
}


class MovieModel(BaseModel):
    """Model representing a movie."""
    id: str
    imdb_rating: float | None = Field(alias='rating')
    genres: List[str]
    title: str
    persons: List[PersonModel] | None = Field(exclude=True)
    description: str | None

    def _get_persons_by_role(self, role: str) -> List[PersonModel]:
        """Filter persons by role."""
        if self.persons:
            return [person for person in self.persons if person.person_role == role]
        return []

    def _get_persons_names(self, role: str) -> List[str]:
        """Get list of person names for a given role."""
        return [person.person_name for person in self._get_persons_by_role(role)]

    def _get_persons_info(self, role: str) -> List[Dict[str, str]]:
        """Get list of dictionaries with person id and name for a given role."""
        return [
            {'id': person.person_id, 'name': person.person_name}
            for person in self._get_persons_by_role(role)
        ]

    def dict(self, **kwargs) -> Dict:
        """Override dict method to include role-based person information."""
        obj_dict = super().dict(**kwargs)
        for role_key, role_value in ROLES.items():
            obj_dict[role_key] = self._get_persons_info(role_value)
            obj_dict[f'{role_key}_names'] = self._get_persons_names(role_value)
        return obj_dict


class GenreModel(BaseModel):
    """Model for Genre"""
    id: str
    description: str | None
    name: str


class PersonModel(BaseModel):
    """Model for Person"""
    person_id: str
    full_name: str
    class FilmEntity(BaseModel):
        id: str
        roles: List[str]
        title: str
        imdb_rating: int | float | None
    films: list[FilmEntity]
