"""
Модуль MSP-протокола для связи с DJI FPV очками.

Предоставляет низкоуровневые функции сборки MSP-пакетов
(osd_msp_client) и высокоуровневый контроллер OSD (OSDController).

Экспортирует:
    OSDController: Контроллер OSD с поддержкой контекстного менеджера
    build_msp_dp_packet: Сборка сырого MSP-пакета
    create_osd_string: Сборка пакета для вывода строки
    show_string_dji_googles: Упрощённая функция для разового вывода
"""

from app_msp.osd_controller import OSDController
from app_msp.osd_msp_client import (
    MSP_DP_COMANDS,
    build_msp_dp_packet,
    create_osd_string,
    show_string_dji_googles,
)

__all__ = [
    'OSDController',
    'MSP_DP_COMANDS',
    'build_msp_dp_packet',
    'create_osd_string',
    'show_string_dji_googles',
]
