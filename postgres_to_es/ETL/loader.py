import logging
from typing import Dict, List

import backoff
import elastic_transport
from elasticsearch import Elasticsearch, helpers

from genres_index import genres_index
from models import GenreModel, MovieModel
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
        self.indexes = {"movies": movies_index, "genres": genres_index}

    @backoff.on_exception(
        backoff.expo,
        (elastic_transport.ConnectionError, elastic_transport.ConnectionTimeout),
        max_tries=5,
        max_time=5,
    )
    def create_indexes(self) -> None:
        """
        Создает индексы в Elasticsearch, если они не существуют.

        :raises: ConnectionError, ConnectionTimeout
        """
        for index_name, index_setting in self.indexes.items():
            if not self.elastic.indices.exists(index=index_name):
                self.elastic.indices.create(
                    index=index_name,
                    body=index_setting
                )

    @backoff.on_exception(
        backoff.expo,
        (elastic_transport.ConnectionError, elastic_transport.ConnectionTimeout),
        max_tries=5,
        max_time=5
    )
    def bulk_data_load(self, data) -> None:
        """
        Загружает данные в Elasticsearch пакетами.

        :param data: Преобразованные данные для загрузки.
        :raises: ConnectionError, ConnectionTimeout
        """
        # for index_name in self.indexes:
        #     bulk_data = [
        #         {
        #             '_op_type': 'index',
        #             '_id': item.id,
        #             '_index': index_name,
        #             '_source': item.dict()
        #         }
        #         for item in data
        #     ]
        #     helpers.bulk(self.elastic, bulk_data)

        for index_name, items in data.items():
            bulk_data = [
                {
                    '_op_type': 'index',
                    '_id': item.id,
                    '_index': index_name,
                    '_source': item.dict()
                }
                for item in items
            ]
            helpers.bulk(self.elastic, bulk_data)

    def load(self, data: Dict[str, List[MovieModel | GenreModel]]) -> None:
        """
        Метод для загрузки данных в Elasticsearch с обработкой исключений.

        :param data: Преобразованные данные для загрузки.
        :raises: ESConnectionError
        """
        try:
            self.create_indexes()
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
