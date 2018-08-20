import logging
import os

_LOG = None


def get_logger(name='thumb', init=False):

    global _LOG

    if (_LOG is None) or init:
        log_level = int(os.environ.get('LOG_LEVEL', 10))
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)7s - %(message)s'
        )
        _stream = logging.StreamHandler()
        _stream.setFormatter(formatter)
        _LOG = logging.getLogger(name)
        _LOG.propagate = False
        _LOG.setLevel(log_level)
        _LOG.handlers = []
        _LOG.addHandler(_stream)

    return _LOG
