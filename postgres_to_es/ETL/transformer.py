from settings.settings import logger
from models import MovieModel


class DataTransformer:
    """Класс для преобразования данных из Postgres для загрузки в Elastic."""
    @staticmethod
    def transform(rows_from_postgres: list[dict]) -> list[MovieModel]:
        """Преобразование сырых данных из БД в объекты для загрузки в Elastic."""
        data = []
        for row in rows_from_postgres:
            try:
                data.append(MovieModel(**row))
            except Exception as er:
                logger.error(f'Ошибка преобразования данных {row=}, {er=}')
                continue
        return data
