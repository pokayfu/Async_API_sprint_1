from functools import lru_cache
from fastapi import Depends
from orjson import orjson

from src.db.elastic import get_elastic
from src.db.redis import get_redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from redis.asyncio import Redis
from src.models.film import Film, FilmPreview
from src.services.utils import get_key_by_args

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class FilmService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, film_id: str) -> Film | None:
        film = await self._film_from_cache(film_id)
        if not film:
            film = await self._get_film_from_elastic(film_id)
            if not film:
                return None
            await self._put_film_to_cache(film)

        return film

    async def all(self, **kwargs) -> list[FilmPreview]:
        films = await self._films_from_cache(**kwargs)
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

    async def _get_films_from_elastic(self, **kwargs) -> list[FilmPreview] | None:
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

        return [FilmPreview(**doc['_source']) for doc in docs['hits']['hits']]

    async def _film_from_cache(self, film_id: str) -> Film | None:
        key = f'film: {film_id}'
        data = await self.redis.get(key)
        if not data:
            return None
        film = Film.parse_raw(data)
        return film

    async def _films_from_cache(self, **kwargs) -> list[FilmPreview] | None:
        key = f'films: {await get_key_by_args(**kwargs)}'
        data = await self.redis.get(key)
        if not data:
            return None

        return [FilmPreview.parse_raw(item) for item in orjson.loads(data)]

    async def _put_film_to_cache(self, film: Film):
        key = f'film: {film.id}'
        await self.redis.set(key, film.json(), FILM_CACHE_EXPIRE_IN_SECONDS)

    async def _put_films_to_cache(self, films: list[FilmPreview], **kwargs):
        key = f'films: {await get_key_by_args(**kwargs)}'
        await self.redis.set(key, orjson.dumps([film.json() for film in films]), FILM_CACHE_EXPIRE_IN_SECONDS)


@lru_cache()
def get_film_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(redis, elastic)
