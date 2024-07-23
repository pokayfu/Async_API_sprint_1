import logging
from typing import List

import backoff
import elastic_transport
from elasticsearch import Elasticsearch, helpers

from models import MovieModel
from movies_index import movies_index
from settings.settings import ElasticsearchSettings


class ESConnectionError(Exception):
    """Кастомное исключение для ошибок подключения к Elasticsearch."""
    pass


class ESLoader:
    """Класс для загрузки данных в Elasticsearch."""

    def __init__(self, es_settings: ElasticsearchSettings) -> None:
        """
        Инициализация загрузчика с настройками Elasticsearch.

        :param es_settings: Настройки Elasticsearch.
        """
        self.elastic = Elasticsearch([es_settings.dict()], timeout=5)
        self.index_name = "movies"
        self.index_settings = movies_index

    @backoff.on_exception(
        backoff.expo,
        (elastic_transport.ConnectionError, elastic_transport.ConnectionTimeout),
        max_tries=5,
        max_time=5,
    )
    def create_index(self) -> None:
        """
        Создает индекс в Elasticsearch, если он не существует.

        :raises: ConnectionError, ConnectionTimeout
        """
        if not self.elastic.indices.exists(index=self.index_name):
            self.elastic.indices.create(
                index=self.index_name,
                body=self.index_settings
            )

    @backoff.on_exception(
        backoff.expo,
        (elastic_transport.ConnectionError, elastic_transport.ConnectionTimeout),
        max_tries=5,
        max_time=5
    )
    def bulk_data_load(self, data: List[MovieModel]) -> None:
        """
        Загружает данные в Elasticsearch пакетами.

        :param data: Преобразованные данные для загрузки.
        :raises: ConnectionError, ConnectionTimeout
        """
        bulk_data = [
            {
                '_op_type': 'index',
                '_id': item.id,
                '_index': self.index_name,
                '_source': item.dict()
            }
            for item in data
        ]
        helpers.bulk(self.elastic, bulk_data)

    def load(self, data: List[MovieModel]) -> None:
        """
        Метод для загрузки данных в Elasticsearch с обработкой исключений.

        :param data: Преобразованные данные для загрузки.
        :raises: ESConnectionError
        """
        try:
            self.create_index()
            self.bulk_data_load(data)
        except (elastic_transport.ConnectionError, elastic_transport.ConnectionTimeout) as error:
            logging.error(f'Ошибка загрузки данных в Elasticsearch: {error}')
            raise ESConnectionError(
                f'{error}. Failed to load data into Elasticsearch: '
                f'{data}'
            )
        finally:
            if self.elastic:
                self.elastic.close()
