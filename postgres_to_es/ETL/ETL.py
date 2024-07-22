from extractor import DBConnectionError, PsExtractor
from loader import ESConnectionError, ESLoader
from settings.settings import db_settings, es_settings, logger
from state import State
from transformer import DataTransformer


class ETL:

    def __init__(self, state: State) -> None:
        self.extractor = PsExtractor(db_settings)
        self.transformer = DataTransformer()
        self.loader = ESLoader(es_settings)
        self.state = state

    def start(self) -> None:
        """
        ETL: extract + transform + load
        """
        state = self.state.get_state()
        if state:
            logger.info(f'ETL started with state: modified at = {state}')
        else:
            logger.info(f'ETL started first time')
        try:
            data = self.extractor.extract(state)
            transformed_data = self.transformer.transform(data)
            self.loader.load(transformed_data)
            self.state.set_state()
        except (DBConnectionError, ESConnectionError) as error:
            logger.error(f'Complete ETLProcess with error: {error}')
        except Exception as error:
            logger.exception(f'ETL finished with error: {error}')
        logger.info('Done')
