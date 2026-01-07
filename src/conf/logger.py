import sys
import logging
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler

from src import conf


def setup_logging(
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        max_bytes: int = 10 * 1024 * 1024,
        backup_count: int = 5
) -> logging.Logger:
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logger = logging.getLogger("app")
    logger.setLevel(getattr(logging, log_level.upper()))

    logger.handlers.clear()
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    return logger


app_logger = setup_logging(
    log_level=conf.settings.LOG_LEVEL if hasattr(conf.settings, 'LOG_LEVEL') else "INFO",
    log_file=conf.settings.LOG_FILE if hasattr(conf.settings, 'LOG_FILE') else "logs/app.log"
)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"app.{name}")
