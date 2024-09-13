import os
from logging import config as logging_config
from pydantic import Field
from src.core.logger import LOGGING
from pydantic_settings import BaseSettings, SettingsConfigDict


# Применяем настройки логирования
logging_config.dictConfig(LOGGING)

# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')
    project_name: str = Field('movies', alias='PROJECT_NAME')
    redis_host: str = Field(..., alias='REDIS_HOST')
    redis_port: int = Field(6379, alias='REDIS_PORT')
    es_schema: str = Field('http://', alias='ES_SCHEMA')
    es_host: str = Field(..., alias='ES_HOST')
    es_port: int = Field(9200, alias='ES_PORT')
    base_dir: str = Field(BASE_DIR, alias='BASE_DIR')


settings = Settings()
