from functools import lru_cache

import orjson
from fastapi import Depends
from src.db.elastic import get_elastic
from src.db.redis import get_redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from redis.asyncio import Redis
from src.models.genre import Genre
from src.services.utils import get_key_by_args

GENRE_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class GenreService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, genre_id: str) -> Genre | None:
        genre = await self._genre_from_cache(genre_id)
        if not genre:
            genre = await self._get_genre_from_elastic(genre_id)
            if not genre:
                return None
            await self._put_genre_to_cache(genre)

        return genre

    async def _get_genre_from_elastic(self, genre_id) -> Genre | None:
        try:
            doc = await self.elastic.get(index='genres', id=genre_id)
        except NotFoundError:
            return None
        return Genre(**doc['_source'])
    
    async def _get_genres_from_elastic(self, **kwargs) -> Genre | None:
        page_size = kwargs.get('page_size', 10)
        page = kwargs.get('page', 1)
        body = {"query":  {"match_all": {}}}
        try:
            docs = await self.elastic.search(index='genres',
                                             body=body,
                                             params={
                                                 'size': page_size,
                                                 'from': (page - 1) * page_size,
                                             })
        except NotFoundError:
            return None

        return [Genre(**doc['_source']) for doc in docs['hits']['hits']]

    async def _genre_from_cache(self, genre_id: str) -> Genre | None:
        key = f'genre: {genre_id}'
        data = await self.redis.get(key)
        if not data:
            return None
        genre = Genre.model_validate_json(data)
        return genre

    async def _put_genre_to_cache(self, genre: Genre):
        key = f'genre: {genre.id}'
        await self.redis.set(key, genre.model_dump_json(), GENRE_CACHE_EXPIRE_IN_SECONDS)

    async def all(self, **kwargs) -> list[Genre]:
        genres = await self._genres_from_cache(**kwargs)
        if not genres:
            genres = await self._get_genres_from_elastic(**kwargs)
            if not genres:
                return []
            await self._put_genres_to_cache(genres, **kwargs)
        return genres

    async def _genres_from_cache(self, **kwargs) -> list[Genre]| None: 
        key = f'genres: {await get_key_by_args(**kwargs)}'
        data = await self.redis.get(key)
        if not data:
            return None
        return [Genre.model_validate_json(item) for item in orjson.loads(data)]

    async def _put_genres_to_cache(self, genres: list[Genre], **kwargs):
        key = f'genres: {await get_key_by_args(**kwargs)}'
        await self.redis.set(key, orjson.dumps([genre.model_dump_json() for genre in genres]), GENRE_CACHE_EXPIRE_IN_SECONDS)

@lru_cache()
def get_genre_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    return GenreService(redis, elastic)
