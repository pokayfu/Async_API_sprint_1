from functools import lru_cache
from fastapi import Depends
from src.db.elastic import get_elastic
from src.db.redis import get_redis
from typing import Optional
from elasticsearch import AsyncElasticsearch, NotFoundError
from redis.asyncio import Redis
from src.models.persons import Person

PERSON_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class PersonService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, person_id: str) -> Optional[Person]:
        #person = await self._person_from_cache(person_id)
        person = None
        if not person:
            person = await self._get_person_from_elastic(person_id)
            if not person:
                return None
            #await self._put_person_to_cache(person)
        return person

    async def _get_person_from_elastic(self, person_id) -> Optional[Person]:
        try:
            doc = await self.elastic.get(index='persons', id=person_id)
        except NotFoundError:
            return None
        return Person(**doc['_source'])
    
    async def _get_persons_from_elastic(self, **kwargs) -> Optional[Person]:
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

    async def _person_from_cache(self, person_id: str) -> Optional[Person]:
        data = await self.redis.get(person_id)
        if not data:
            return None
        person = person.parse_raw(data)
        return person

    async def _put_person_to_cache(self, person: Person):
        await self.redis.set(person.id, person.json(), PERSON_CACHE_EXPIRE_IN_SECONDS)

    async def all(self, **kwargs) -> list[Person]:
        #persons = await self._persons_from_cache(**kwargs)
        persons = None
        if not persons:
            persons = await self._get_persons_from_elastic(**kwargs)
            if not persons:
                return []
            #await self._put_person_to_cache(persons, **kwargs)
        return persons

@lru_cache()
def get_person_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    return PersonService(redis, elastic)