import logging
import sys


_bot_logger_formatter = logging.Formatter(
    fmt='%(asctime)s - %(name)s - %(levelname)s %(funcName)s(): %(message)s')


def create_logger(name: str, level: int = logging.DEBUG, stream=sys.stderr, filename=None) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if stream is not None:
        handler = logging.StreamHandler(stream)
        handler.setLevel(level)
        handler.setFormatter(_bot_logger_formatter)
        logger.addHandler(handler)
    if (filename is not None) and (filename != ''):
        handler = logging.FileHandler(filename, mode='at', encoding='utf-8')
        handler.setLevel(level)
        handler.setFormatter(_bot_logger_formatter)
        logger.addHandler(handler)
    return logger
