import logging

_LOG = None


def get_logger() -> logging.Logger:
    global _LOG
    if _LOG is None:
        _LOG = logging.getLogger(__name__)
    return _LOG
