import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from src import conf


def setup_logging(
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        max_bytes: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 5
) -> logging.Logger:
    """
    Настройка логирования для приложения.

    Args:
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Путь к файлу логов (если None - только консоль)
        max_bytes: Максимальный размер файла лога
        backup_count: Количество backup файлов
    """
    # Создаем директорию для логов, если она не существует
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Настраиваем форматтер
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Получаем корневой логгер
    logger = logging.getLogger("app")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Очищаем существующие обработчики
    logger.handlers.clear()

    # Добавляем консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Добавляем файловый обработчик, если указан файл
    if log_file:
        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Устанавливаем уровень логирования для сторонних библиотек
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    return logger


# Создаем глобальный логгер
app_logger = setup_logging(
    log_level=conf.settings.LOG_LEVEL if hasattr(conf.settings, 'LOG_LEVEL') else "INFO",
    log_file=conf.settings.LOG_FILE if hasattr(conf.settings, 'LOG_FILE') else "logs/app.log"
)


def get_logger(name: str) -> logging.Logger:
    """
    Получить именованный логгер.

    Args:
        name: Имя логгера (обычно __name__)

    Returns:
        Экземпляр логгера
    """
    return logging.getLogger(f"app.{name}")
