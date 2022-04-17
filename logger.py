"""Настраивает логгирование."""

import logging
from sys import stdout


def logger_setup(filename):
    """Задает настройки и возвращает экземляр logger."""
    logging.basicConfig(
        filename=f'{filename}.log',
        filemode='a',
        format='%(asctime)s:%(name)s:%(message)s'
    )
    handler = logging.StreamHandler(stream=stdout)
    logger = logging.getLogger(filename)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger


if __name__ == '__main__':
    logger_setup(__name__)
