import datetime
import logging

logger = logging.getLogger(__name__)


class JsonFileStorage:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def write(self, modified: str) -> None:
        try:
            with open(self.file_path, 'w') as file:
                file.write(modified)
                logger.info(f'write new state {modified}')
        except IOError as e:
            logger.error(f'Error writing state to file: {e}')

    def read(self) -> str | None:
        try:
            with open(self.file_path, 'r') as file:
                return file.read()
        except IOError as e:
            logger.error(f'Error reading state from file: {e}')
            return None


class State:
    def __init__(self, storage: JsonFileStorage) -> None:
        self.storage = storage

    def get_state(self) -> str | None:
        return self.storage.read()

    def set_state(self) -> None:
        modified = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f+00")
        self.storage.write(modified)
