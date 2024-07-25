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

SQL_GENRES_QUERY = """
    SELECT
        g.id,
        g.name,
        g.description,
        g.updated_at
    FROM content.genre g
    ORDER BY g.updated_at;
"""

SQL_MODIFIED_GENRES_QUERY = """
    SELECT
        g.id,
        g.name,
        g.description,
        g.updated_at
    FROM content.genre g
    WHERE g.updated_at > %s
    ORDER BY g.updated_at;
"""

SQL_MODIFIED_PERSONS_QUERY= """
    SELECT 
            person_with_films.person_id, 
            person_with_films.full_name,
            ARRAY_AGG(distinct
                jsonb_build_object('id', person_with_films.film_id, 'roles', roles, 'title', person_with_films.film_title, 'imdb_rating', person_with_films.film_rating)) AS films,
            person_with_films.updated_at
    FROM (
            SELECT 
                film.id as film_id,
                film.title as film_title,
                film.rating as film_rating,
                person.id as person_id, 
                person.full_name as full_name,
                ARRAY_AGG(DISTINCT (person_film.role)) AS roles,
                GREATEST(film.updated_at, MAX(genre.updated_at), MAX(person.updated_at)) as updated_at
            FROM 
                content.film_work film
                LEFT JOIN content.genre_film_work AS genre_film ON film.id = genre_film.film_work_id
                LEFT JOIN content.genre AS genre ON genre_film.genre_id = genre.id
                LEFT JOIN content.person_film_work AS person_film ON film.id = person_film.film_work_id
                LEFT JOIN content.person as person on person.id = person_film.person_id
            WHERE person.id is not null and GREATEST(film.updated_at, genre.updated_at, person.updated_at) >= %s
            GROUP BY 
                film.id, person.id, person.full_name
        ) AS person_with_films
    GROUP BY 
        person_with_films.person_id, person_with_films.full_name, person_with_films.updated_at
    ORDER BY updated_at;
"""




SQL_PERSONS_QUERY = """
    SELECT 
            person_with_films.person_id, 
            person_with_films.full_name,
            ARRAY_AGG(distinct
                jsonb_build_object('id', person_with_films.film_id, 'roles', roles, 'title', person_with_films.film_title, 'imdb_rating', person_with_films.film_rating)) AS films,
            person_with_films.updated_at
    FROM (
            SELECT 
                film.id as film_id,
                film.title as film_title,
                film.rating as film_rating,
                person.id as person_id, 
                person.full_name as full_name,
                ARRAY_AGG(DISTINCT (person_film.role)) AS roles,
                GREATEST(film.updated_at, MAX(genre.updated_at), MAX(person.updated_at)) as updated_at
            FROM 
                content.film_work film
                LEFT JOIN content.genre_film_work AS genre_film ON film.id = genre_film.film_work_id
                LEFT JOIN content.genre AS genre ON genre_film.genre_id = genre.id
                LEFT JOIN content.person_film_work AS person_film ON film.id = person_film.film_work_id
                LEFT JOIN content.person as person on person.id = person_film.person_id
            WHERE person.id is not null and GREATEST(film.updated_at, genre.updated_at, person.updated_at) >= 'epoch'
            GROUP BY 
                film.id, person.id, person.full_name
        ) AS person_with_films
    GROUP BY 
        person_with_films.person_id, person_with_films.full_name, person_with_films.updated_at
    ORDER BY updated_at;
"""