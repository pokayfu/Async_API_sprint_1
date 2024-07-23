import logging
import os

from pydantic import Extra, Field
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s %(levelname)s]: %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S%p')


class PostgresDBSettings(BaseSettings):
    dbname: str = Field(alias='DB_NAME')
    user: str = Field(alias='DB_USER')
    password: str = Field(alias='DB_PASSWORD')
    host: str = Field(alias='DB_HOST')
    port: str = Field(alias='DB_PORT')

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
        extra = Extra.ignore


class ElasticsearchSettings(BaseSettings):
    scheme: str = Field(alias='ES_SCHEMA')
    host: str = Field(alias='ES_HOST')
    port: int = Field(alias='ES_PORT')

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
        extra = Extra.ignore


db_settings = PostgresDBSettings()
es_settings = ElasticsearchSettings()

SQL_MODIFIED_QUERY = """SELECT
   fw.id,
   fw.title,
   fw.description,
   fw.rating,
   fw.type,
   COALESCE (
       json_agg(
           DISTINCT jsonb_build_object(
               'person_role', pfw.role,
               'person_id', p.id,
               'person_name', p.full_name
           )
       ) FILTER (WHERE p.id is not null),
       '[]'
   ) as persons,
   array_agg(DISTINCT g.name) as genres
FROM content.film_work fw
LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
LEFT JOIN content.person p ON p.id = pfw.person_id
LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
LEFT JOIN content.genre g ON g.id = gfw.genre_id
WHERE fw.updated_at > %s OR g.updated_at > %s OR p.updated_at > %s
GROUP BY fw.id
ORDER BY fw.updated_at;"""

SQL_QUERY = """
    SELECT
   fw.id,
   fw.title,
   fw.description,
   fw.rating,
   fw.type,
   COALESCE (
       json_agg(
           DISTINCT jsonb_build_object(
               'person_role', pfw.role,
               'person_id', p.id,
               'person_name', p.full_name
           )
       ) FILTER (WHERE p.id is not null),
       '[]'
   ) as persons,
   array_agg(DISTINCT g.name) as genres
FROM content.film_work fw
LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
LEFT JOIN content.person p ON p.id = pfw.person_id
LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
LEFT JOIN content.genre g ON g.id = gfw.genre_id
GROUP BY fw.id
ORDER BY fw.updated_at;
"""