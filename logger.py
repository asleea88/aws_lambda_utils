import logging
import os

_LOG = None


def get_logger(name='thumb', init=False):

    global _LOG

    if (_LOG is None) or init:
        try:
            log_level = int(os.environ['LOG_LEVEL'])
        except KeyError:
            from src import settings
            log_level = settings.LOG_LEVEL

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(message)s'
        )
        _stream = logging.StreamHandler()
        _stream.setFormatter(formatter)
        _LOG = logging.getLogger(name)
        _LOG.propagate = False
        _LOG.setLevel(log_level)
        _LOG.addHandler(_stream)

    return _LOG
