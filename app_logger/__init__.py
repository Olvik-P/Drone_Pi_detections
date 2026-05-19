import os

from app_logger.constants import LOG_FILE_MSP
from app_logger.custom_loguru import LoggerLoguru as logger

logger_detect = logger.create()
logger_msp = logger.create(LOG_FILE_MSP)

is_dev = os.getenv('ENV_TYPE', 'dev') == 'dev'

if is_dev:
    logger_detect.info(
        'Режим разработки: логирование настроено для вывода в консоль.'
    )
else:
    logger_detect.info(
        'Режим продакшена: логирование настроено для вывода в консоль и файл.'
    )

__all__ = ['logger_detect', 'logger_msp']
