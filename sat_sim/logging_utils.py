from __future__ import annotations

import logging
import sys
from pathlib import Path


def setup_logger(
    name: str = "sat_sim",
    level: str = "INFO",
    log_file: str | None = None,
) -> logging.Logger:
    """
    Create and configure a logger.

    Parameters
    ----------
    name:
        Logger name.

    level:
        Logging level. Examples: DEBUG, INFO, WARNING, ERROR.

    log_file:
        Optional path to a log file. If provided, logs are written both
        to terminal and to the file.

    Returns
    -------
    logging.Logger
    """

    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if setup_logger() is called multiple times.
    if logger.handlers:
        return logger

    logger.setLevel(level.upper())

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(level.upper())
    logger.addHandler(stream_handler)

    if log_file is not None:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level.upper())
        logger.addHandler(file_handler)

    return logger