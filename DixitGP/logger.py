import functools
import logging
import os
import sys
import time
from logging.handlers import RotatingFileHandler

FOLDER = 'logs'
FILE_NAME = 'bot.log'
LEVEL = logging.INFO


def get_path():
    return os.path.join(FOLDER, FILE_NAME)


def init_logging():
    os.makedirs(FOLDER, exist_ok=True)

    logger = logging.root
    logger.setLevel(LEVEL)

    formatter = logging.Formatter(
        '%(levelname)-6s [%(asctime)s] %(message)-100s      <%(name)s:%(filename)s:%(lineno)d ~%(threadName)s~>')

    path = get_path()
    fh = RotatingFileHandler(path, maxBytes=30 * 1024 * 1024, backupCount=1, encoding="utf-8")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    ch = logging.StreamHandler(stream=sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger


def benchmark(message, log_func):
    def _wrap(func):
        @functools.wraps(func)
        def _new_func(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            log_func(f'{message} {kwargs} {time.time() - start:0.2f}s')
            return result

        return _new_func

    return _wrap
