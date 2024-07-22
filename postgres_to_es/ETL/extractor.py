from typing import Dict, List, Optional

import backoff
import psycopg2
from psycopg2 import DatabaseError, InterfaceError, OperationalError
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor

from settings.settings import PostgresDBSettings, SQL_MODIFIED_QUERY, SQL_QUERY


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
        self.modified_query: str = SQL_MODIFIED_QUERY
        self.query: str = SQL_QUERY

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

    def extract(self, modified: Optional[str] = None) -> List[Dict]:
        """
        Извлекает данные из базы данных Postgres, учитывая дату последнего обновления.

        :param modified: Дата последнего обновления для выборки измененных данных.
        :return: Список извлеченных данных.
        """
        data = []
        connection = None
        try:
            connection = self.connect()
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                if modified:
                    cursor.execute(self.modified_query, (modified, modified, modified))
                else:
                    cursor.execute(self.query)
                for record in cursor:
                    data.append(dict(record))
        except (OperationalError, InterfaceError, DatabaseError) as error:
            raise DBConnectionError(f'Ошибка подключения к БД: {error}.')
        finally:
            if connection:
                connection.close()
        return data
