from typing import Dict, List, Optional

import backoff
import psycopg2
from psycopg2 import DatabaseError, InterfaceError, OperationalError
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor

from settings.settings import (PostgresDBSettings, SQL_GENRES_QUERY, SQL_MODIFIED_GENRES_QUERY, SQL_MODIFIED_QUERY,
                               SQL_QUERY)


class DBConnectionError(Exception):
    """Кастомное исключение для ошибок подключения к Postgres."""
    pass


class PsExtractor:
    """Класс для извлечения данных из Postgres."""

    def __init__(self, db_settings: PostgresDBSettings) -> None:
        """
        Инициализация экстрактора с настройками базы данных.

        :param db_settings: Настройки базы данных.
        """
        self.db_settings = db_settings
        # self.modified_query: str = SQL_MODIFIED_QUERY
        self.query = {"movies": SQL_QUERY, "genres": SQL_GENRES_QUERY}
        self.modified_query = {"movies": SQL_MODIFIED_QUERY, "genres": SQL_MODIFIED_GENRES_QUERY}

    @backoff.on_exception(
        backoff.expo,
        (OperationalError, InterfaceError, DatabaseError),
        max_tries=5,
        max_time=5,
    )
    def connect(self) -> connection:
        """
        Устанавливает соединение с базой данных Postgres с использованием экспоненциального бэкоффа.

        :return: Соединение с базой данных.
        """
        return psycopg2.connect(**self.db_settings.dict(), connect_timeout=5)

    def extract(self, modified: Optional[str] = None) -> Dict[str, List[Dict]]:
        """
        Извлекает данные из базы данных Postgres, учитывая дату последнего обновления.

        :param modified: Дата последнего обновления для выборки измененных данных.
        :return: Список извлеченных данных.
        """
        data = {
            'movies': [],
            'genres': []
        }
        connection = None
        try:
            connection = self.connect()
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                for data_type in data.keys():
                    if modified:
                        if data_type == 'movies':
                            cursor.execute(self.modified_query[data_type], (modified, modified, modified))
                        elif data_type == 'genres':
                            cursor.execute(self.modified_query[data_type], (modified,))
                    else:
                        cursor.execute(self.query[data_type])
                    for record in cursor:
                        data[data_type].append(dict(record))
        except (OperationalError, InterfaceError, DatabaseError) as error:
            raise DBConnectionError(f'Ошибка подключения к БД: {error}.')
        finally:
            if connection:
                connection.close()
        return data
