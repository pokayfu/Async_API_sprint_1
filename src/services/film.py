import json
from functools import lru_cache
from fastapi import Depends
from orjson import orjson

from src.db.elastic import get_elastic
from src.db.redis import get_redis
from typing import Optional
from elasticsearch import AsyncElasticsearch, NotFoundError
from redis.asyncio import Redis
from src.models.film import Film, Genre, Person

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class FilmService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, film_id: str) -> Optional[Film]:
        # film = self._film_from_cache(film_id)
        film = None
        if not film:
            film = await self._get_film_from_elastic(film_id)
            if not film:
                return None
            await self._put_film_to_cache(film)

        return film

    async def all(self, **kwargs) -> list[Film]:
        # films = await self._films_from_cache(**kwargs)
        films = None
        if not films:
            films = await self._get_films_from_elastic(**kwargs)
            if not films:
                return []
            await self._put_films_to_cache(films, **kwargs)
        return films

    async def _get_film_from_elastic(self, film_id: str) -> Film | None:
        try:
            doc = await self.elastic.get(index='movies', id=film_id)
        except NotFoundError:
            return None
        source = doc['_source']
        return Film(**source)

    async def _get_films_from_elastic(self, **kwargs) -> list[Film] | None:
        page_size = kwargs.get('page_size', 10)
        page = kwargs.get('page', 1)
        sort = kwargs.get('sort', '')
        genre = kwargs.get('genre', None)
        query = kwargs.get('query', None)
        body = {"query": {"bool": {"must": []}}}

        if genre:
            body["query"]["bool"]["must"].append({
                "match": {
                    "genres": genre
                }
            })

        if query:
            body["query"]["bool"]["must"].append({
                "match": {
                    "title": {
                        "query": query,
                        "fuzziness": 1,
                        "operator": "and"
                    }
                }
            })

        # Если нет условий для must, устанавливаем match_all
        if not body["query"]["bool"]["must"]:
            body["query"] = {"match_all": {}}

        try:
            docs = await self.elastic.search(index='movies',
                                             body=body,
                                             params={
                                                 'size': page_size,
                                                 'from': (page - 1) * page_size,
                                                 'sort': sort,
                                             })
        except NotFoundError:
            return None

        return [await FilmService._make_film_from_es_doc(doc) for doc in docs['hits']['hits']]

    async def _film_from_cache(self, film_id: str) -> Optional[Film]:
        data = await self.redis.get(film_id)
        if not data:
            return None
        film = Film.parse_raw(data)
        return film

    async def _films_from_cache(self, **kwargs) -> list[Film] | None:
        key = await self.get_key_by_args(**kwargs)
        data = await self.redis.get(key)
        if not data:
            return None

        return [Film.parse_raw(item) for item in orjson.loads(data)]

    async def _put_film_to_cache(self, film: Film):
        await self.redis.set(film.id, film.json(), FILM_CACHE_EXPIRE_IN_SECONDS)

    async def _put_films_to_cache(self, films: list[Film], **kwargs):
        key = await self.get_key_by_args(**kwargs)
        await self.redis.set(key, orjson.dumps([film.json() for film in films]), FILM_CACHE_EXPIRE_IN_SECONDS)

    @staticmethod
    async def _make_film_from_es_doc(doc: dict) -> Film:
        source = doc['_source']
        return Film(**source)

    async def get_key_by_args(self, *args, **kwargs) -> str:
        return f'{args}:{json.dumps({'kwargs': kwargs}, sort_keys=True)}'

@lru_cache()
def get_film_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(redis, elastic)