from datetime import datetime
from logging import Formatter, Logger, INFO
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
from typing import Union, Optional


class ScopusClientLogger(Logger):
    _current_file: Path = Path(__file__).resolve()

    _instance: Optional['ScopusClientLogger'] = None

    def __new__(cls, name: str = 'ScopusClient', level: Union[int, str] = INFO):
        if cls._instance is None:
            cls._instance = super(ScopusClientLogger, cls).__new__(cls)
            cls._instance.__init__(name, level)
        return cls._instance

    def __init__(self, name: str = 'ScopusClient', level: Union[int, str] = INFO):
        self._level = level

        logs_dir = ScopusClientLogger._current_file.parent / 'logs'
        os.makedirs(logs_dir, exist_ok=True)
        self._logs_filename = os.path.join(
            logs_dir,
            f'scopus_client_{datetime.now().strftime(format="%Y-%m-%d_%H-%M-%S")}.log'
        )

        super().__init__(name=name, level=level)
        self._add_file_handler()

    def _add_file_handler(self) -> None:
        file_handler = RotatingFileHandler(
            filename=self._logs_filename,
            mode='a',
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(self._level)
        file_handler.setFormatter(Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        self.addHandler(file_handler)


if __name__ == '__main__':
    print(ScopusClientLogger().__hash__())
    print(ScopusClientLogger().__hash__())

