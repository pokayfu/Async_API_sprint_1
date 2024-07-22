import time

from state import JsonFileStorage, State
from ETL import ETL

if __name__ == '__main__':
    storage = JsonFileStorage(r'tmp_storage.txt')
    state = State(storage)
    while True:
        etl = ETL(state)
        etl.start()
        time.sleep(5)
