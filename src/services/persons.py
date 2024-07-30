from functools import lru_cache

import orjson
from fastapi import Depends
from src.db.elastic import get_elastic
from src.db.redis import get_redis
from typing import Optional
from elasticsearch import AsyncElasticsearch, NotFoundError
from redis.asyncio import Redis
from src.models.persons import Person
from src.models.film import FilmPreview
from src.services.film import FilmService
from src.services.utils import get_key_by_args

PERSON_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class PersonService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_films_by_person(self, person_id: str) -> Optional[list[FilmPreview]]:
        films = await self._films_by_person_from_cache(person_id)
        if not films:
            films = await self._get_films_by_person_from_elastic(person_id)
            if not films:
                return None
            await self._put_films_by_person_to_cache(person_id=person_id, films=films)
        return films

    async def _get_films_by_person_from_elastic(self, person_id: str):
        films_by_person = []
        app_film_service = FilmService(self.redis, self.elastic)
        person_data = await self._get_person_from_elastic(person_id)
        if not person_data:
            return None
        films_id = [film['id'] for film in person_data.model_dump()['films']]
        if not films_id:
            return None
        for id in films_id:
            film = await app_film_service.get_by_id(id)
            films_by_person.append(FilmPreview(**film.model_dump()))
        return films_by_person

    async def get_by_id(self, person_id: str) -> Optional[Person]:
        person = await self._person_from_cache(person_id)
        if not person:
            person = await self._get_person_from_elastic(person_id)
            if not person:
                return None
            await self._put_person_to_cache(person)
        return person

    async def all(self, **kwargs) -> list[Person]:
        persons = await self._persons_from_cache(**kwargs)
        if not persons:
            persons = await self._get_persons_from_elastic(**kwargs)
            if not persons:
                return []
            await self._put_persons_to_cache(persons, **kwargs)
        return persons

    async def _get_person_from_elastic(self, person_id) -> Optional[Person]:
        try:
            doc = await self.elastic.get(index='persons', id=person_id)
        except NotFoundError:
            return None
        return Person(**doc['_source'])
    
    async def _get_persons_from_elastic(self, **kwargs) -> list[Person] | None:
        page_size = kwargs.get('page_size', 10)
        page = kwargs.get('page', 1)
        query = kwargs.get('query', None)
        body = {"query": {"bool": {"must": []}}}
        if query:
            body["query"]["bool"]["must"].append({
                "match": {
                    "full_name": {
                        "query": query,
                        "fuzziness": 1,
                        "operator": "and"
                    }
                }
            })
        if not body["query"]["bool"]["must"]:
            body["query"] = {"match_all": {}}
        try:
            docs = await self.elastic.search(index='persons',
                                             body=body,
                                             params={
                                                 'size': page_size,
                                                 'from': (page - 1) * page_size,
                                             })
        except NotFoundError:
            return None

        return [Person(**doc['_source']) for doc in docs['hits']['hits']]

    async def _put_person_to_cache(self, person: Person):
        await self.redis.set(person.person_id, person.json(), PERSON_CACHE_EXPIRE_IN_SECONDS)

    async def _put_persons_to_cache(self, persons: list[Person], **kwargs):
        key = await get_key_by_args(**kwargs)
        await self.redis.set(key, orjson.dumps([person.json() for person in persons]), PERSON_CACHE_EXPIRE_IN_SECONDS)

    async def _person_from_cache(self, person_id: str) -> Optional[Person]:
        data = await self.redis.get(person_id)
        if not data:
            return None
        person = Person.parse_raw(data)
        return person

    async def _persons_from_cache(self, **kwargs) -> Optional[list[Person]]:
        key = await get_key_by_args(**kwargs)
        data = await self.redis.get(key)
        if not data:
            return None
        return [Person.parse_raw(item) for item in orjson.loads(data)]

    async def _put_films_by_person_to_cache(self, person_id: str, films: list[FilmPreview], **kwargs):
        key = f'_{person_id}'
        await self.redis.set(key, orjson.dumps([film.json() for film in films]), PERSON_CACHE_EXPIRE_IN_SECONDS)

    async def _films_by_person_from_cache(self, *args, **kwargs) -> Optional[list[FilmPreview]]:
        key = f'_{args[0]}'
        data = await self.redis.get(key)
        if not data:
            return None
        return [FilmPreview.parse_raw(item) for item in orjson.loads(data)]


@lru_cache()
def get_person_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    return PersonService(redis, elastic)
