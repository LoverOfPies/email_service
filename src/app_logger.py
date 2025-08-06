import logging
from typing import Any

from src.settings.app import settings


class AppLogger(logging.Logger):
    _instance = None

    def __new__(
        cls,
        logger_name: str | None = None,
        fmt: str | None = None,
        log_level: str | int = logging.INFO,
        *args: Any,
        **kwargs: Any,
    ) -> "AppLogger":
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(
        self,
        logger_name: str | None = None,
        fmt: str | None = None,
        log_level: str | int = logging.INFO,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        logger_name = logger_name or __name__
        super().__init__(logger_name, *args, **kwargs)
        fmt = fmt or "[%(asctime)s] [%(levelname)-8s] [%(name)s]: %(message)s"
        formatter = logging.Formatter(fmt=fmt)
        ch = logging.StreamHandler()
        ch.setLevel(level=log_level)
        ch.setFormatter(formatter)
        self.addHandler(ch)


app_logger = AppLogger(log_level=settings.log_level)
