import copy
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from loguru import logger

from app_logger.constants import (
    LOG_ENCODING,
    LOG_FILE_DETECT,
    LOG_FILE_MSP,
    LOG_FORMAT,
    LOG_LEVEL_DEV,
    LOG_LEVEL_PROD,
    LOG_RETENTION,
    LOG_ROTATION,
    LOG_STR_SYSTEM_NAME,
    LOG_USE_CONSOLE,
    LOG_VALUE_ZERO,
    LOG_LEVEL
)

load_dotenv('.env')


class LoggerLoguru:
    """Логгер на основе Loguru для приложения ERKNM.

    Предоставляет структурированное логирование с поддержкой консоли и файла,
    автоматической ротацией, привязкой пользовательского контекста
    (username, user_id). Настройки зависят от переменной окружения
    ENV_TYPE (dev/prod).

    Пример использования:
        from src.app_logger import logger_api

        logger_api.info('Сообщение', username='john', user_id=42)
        logger_api.error('Ошибка', username='SYSTEM')

    Атрибуты:
        log_file (str): Путь к файлу логов (по умолчанию LOG_FILE_API).
    """

    def __init__(self, log_file: str = LOG_FILE_DETECT) -> None:
        """Инициализация логгера.

        Args:
            log_file: Путь к файлу логов.
                По умолчанию используется LOG_FILE_API.
        """
        self._logger = logger
        self._logger.remove()  # Очищаем стандартные обработчики
        # Создаем независимый logger объект для работы с лог_файлами
        self._logger = copy.deepcopy(logger)
        self._setup_logger(log_file)

    def _get_username_and_user_id(self, kwargs: dict) -> tuple[str, str, dict]:
        """Извлекает username и user_id из kwargs.

        Args:
            kwargs: Словарь ключевых аргументов,
                переданных в метод логирования.

        Returns:
            Кортеж (username, user_id, extra), где extra — это kwargs без
            ключей 'username' и 'user_id'.
        """
        extra = kwargs.copy()
        username = str(extra.pop('username', LOG_STR_SYSTEM_NAME))
        user_id = str(extra.pop('user_id', LOG_VALUE_ZERO))
        return username, user_id, extra

    def _setup_logger(self, log_file: str) -> None:
        """Настройка логгера (вызывается один раз).

        В зависимости от ENV_TYPE настраивает вывод:
          - dev: только консоль с уровнем DEBUG.
          - prod: консоль (если разрешено) и файл с уровнем INFO,
                  ротация 10 MB, retention 7 дней, сериализация JSON.
        """
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        is_dev = os.getenv('ENV_TYPE', 'dev') == 'dev'
        level = LOG_LEVEL_DEV if is_dev else LOG_LEVEL_PROD

        common_params = {
            'format': LOG_FORMAT,
            'backtrace': True,
            'diagnose': True,
        }

        # Консольный вывод для dev режима или если явно разрешено
        if is_dev or LOG_USE_CONSOLE:
            self._logger.add(
                sys.stdout, level=level, colorize=True, **common_params
            )

        # Файловый вывод только для prod режима
        if not is_dev:
            self._logger.add(
                log_path,
                level=level,
                rotation=LOG_ROTATION,
                retention=LOG_RETENTION,
                encoding=LOG_ENCODING,
                serialize=True,
                **common_params,
            )

    def _log(self, level: LOG_LEVEL, message: str, **kwargs: Any) -> None:
        """Внутренний метод для логирования с извлечением username и user_id.

        Args:
            level: Уровень логирования ('info', 'debug', и т.д.).
            message: Текст сообщения.
            **kwargs: Дополнительные аргументы, включая username и user_id.
        """
        username, user_id, extra = self._get_username_and_user_id(kwargs)
        bound_logger = self._logger.bind(
            username=username, user_id=user_id, **extra
        )
        log_method = getattr(bound_logger, level)
        log_method(message)

    @classmethod
    def create(cls, log_file: str = LOG_FILE_DETECT) -> 'LoggerLoguru':
        """Создает и возвращает экземпляр логгера.

        Args:
            log_file: Путь к файлу логов.

        Returns:
            Настроенный экземпляр LoggerLoguru.
        """
        return cls(log_file=log_file)

    def info(self, message: str, **kwargs: Any) -> None:
        """Запись лога уровня INFO с привязкой пользовательского контекста.

        Args:
            message: Текст сообщения.
            username: Имя пользователя (по умолчанию 'SYSTEM').
            user_id: ID пользователя (по умолчанию 0).
            **kwargs: Дополнительные поля, добавляемые в лог как extra.
        """
        self._log('info', message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Запись лога уровня DEBUG с привязкой пользовательского контекста.

        Args:
            message: Текст сообщения.
            username: Имя пользователя (по умолчанию 'SYSTEM').
            user_id: ID пользователя (по умолчанию 0).
            **kwargs: Дополнительные поля, добавляемые в лог как extra.
        """
        self._log('debug', message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Запись лога уровня WARNING с привязкой пользовательского контекста.

        Args:
            message: Текст сообщения.
            username: Имя пользователя (по умолчанию 'SYSTEM').
            user_id: ID пользователя (по умолчанию 0).
            **kwargs: Дополнительные поля, добавляемые в лог как extra.
        """
        self._log('warning', message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Запись лога уровня ERROR с привязкой пользовательского контекста.

        Args:
            message: Текст сообщения.
            username: Имя пользователя (по умолчанию 'SYSTEM').
            user_id: ID пользователя (по умолчанию 0).
            **kwargs: Дополнительные поля, добавляемые в лог как extra.
        """
        self._log('error', message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Запись лога уровня CRITICAL с привязкой пользовательского контекста.

        Args:
            message: Текст сообщения.
            username: Имя пользователя (по умолчанию 'SYSTEM').
            user_id: ID пользователя (по умолчанию 0).
            **kwargs: Дополнительные поля, добавляемые в лог как extra.
        """
        self._log('critical', message, **kwargs)

    def exception(self, message: str, **kwargs: Any) -> None:
        """Запись лога уровня ERROR с traceback исключения.

        Используется внутри блока except для логирования исключения
        с полным стектрейсом.

        Args:
            message: Текст сообщения.
            username: Имя пользователя (по умолчанию 'SYSTEM').
            user_id: ID пользователя (по умолчанию 0).
            **kwargs: Дополнительные поля, добавляемые в лог как extra.
        """
        username, user_id, extra = self._get_username_and_user_id(kwargs)
        self._logger.bind(
            username=username, user_id=user_id, **extra
        ).exception(message)

    def __getattr__(self, name: str) -> Any:
        """Проксирование нереализованных методов к внутреннему логгеру."""
        return getattr(self._logger, name)
