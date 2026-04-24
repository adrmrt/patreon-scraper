import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger with the given name, using the level configured in Config.
    Call this at the top of each module:

        from src.logger import get_logger
        logger = get_logger(__name__)
    """
    from src.config import Config  # local import to avoid circular dependency

    logger = logging.getLogger(name)

    # Only configure handlers once (on the root logger)
    root = logging.getLogger()
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        root.addHandler(handler)
        root.setLevel(Config.LOG_LEVEL)

    return logger
