import time
from state import JsonFileStorage, State
from ETL import ETL
import os


if __name__ == '__main__':
    if not os.path.exists('tmp_storage.txt'):
        open('tmp_storage.txt', 'w').close()
    storage = JsonFileStorage(r'tmp_storage.txt')
    state = State(storage)
    while True:
        etl = ETL(state)
        etl.start()
        time.sleep(5)
