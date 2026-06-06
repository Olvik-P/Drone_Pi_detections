"""
Высокоуровневый контроллер для отправки OSD-строк в DJI FPV очки
через MSP DisplayPort протокол.

Использует низкоуровневый модуль osd_msp_client.py для сборки пакетов
и управления последовательным портом.

Пример использования:
    with OSDController(port='/dev/ttyAMA0') as osd:
        osd.clear_screen()
        osd.write_string(row=5, col=10, text='Human')
        osd.draw_screen()
"""

from __future__ import annotations

import time
from typing import Optional

import serial

from app_logger import logger_msp
from app_msp.osd_msp_client import (
    MSP_DP_COMANDS,
    build_msp_dp_packet,
    create_osd_string,
)


class OSDController:
    """
    Контроллер OSD для DJI FPV очков через MSP DisplayPort.

    Управляет подключением к UART-порту полётного контроллера,
    отправкой команд очистки экрана, вывода текста и отрисовки кадра.

    Поддерживает работу как контекстный менеджер.

    Атрибуты:
        port: Имя последовательного порта (например, '/dev/ttyAMA0' или 'COM4')
        baudrate: Скорость передачи (по умолчанию 115200)
        timeout: Таймаут чтения в секундах (по умолчанию 0.1)
        ser: Объект Serial (None, если порт не открыт)
    """

    def __init__(
        self,
        port: str = '/dev/ttyAMA0',
        baudrate: int = 115200,
        timeout: float = 0.1,
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser: Optional[serial.Serial] = None

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> 'OSDController':
        self.open()
        return self

    def __exit__(self, *args) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Port management
    # ------------------------------------------------------------------

    def open(self) -> None:
        """Открывает последовательный порт."""
        try:
            logger_msp.info(
                f'Открытие порта {self.port} @ {self.baudrate} бод')
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
            )
            time.sleep(0.1)  # Даём время на инициализацию
            logger_msp.info(f'Порт {self.port} открыт')
        except serial.SerialException as e:
            logger_msp.error(f'Ошибка открытия порта {self.port}: {e}')
            raise

    def close(self) -> None:
        """Закрывает последовательный порт, если он открыт."""
        if self.ser is not None and self.ser.is_open:
            self.ser.close()
            logger_msp.info(f'Порт {self.port} закрыт')
        self.ser = None

    @property
    def is_open(self) -> bool:
        """Проверяет, открыт ли порт."""
        return self.ser is not None and self.ser.is_open

    # ------------------------------------------------------------------
    # Low-level send
    # ------------------------------------------------------------------

    def _send_packet(self, packet: bytes) -> None:
        """Отправляет сырой MSP-пакет в порт."""
        if not self.is_open:
            raise RuntimeError(f'Порт {self.port} не открыт')
        self.ser.write(packet)
        self.ser.flush()

    # ------------------------------------------------------------------
    # OSD commands
    # ------------------------------------------------------------------

    def clear_screen(self) -> None:
        """Очищает OSD-экран (MSP_DP_CLEAR_SCREEN)."""
        logger_msp.debug('Очистка экрана OSD')
        packet = build_msp_dp_packet(MSP_DP_COMANDS['MSP_DP_CLEAR_SCREEN'])
        self._send_packet(packet)
        time.sleep(0.05)

    def write_string(
        self,
        row: int = 0,
        col: int = 0,
        text: str = 'Human',
        font_number: int = 0,
        blink: bool = False,
    ) -> None:
        """
        Отправляет строку текста в OSD-буфер (MSP_DP_WRITE_STRING).

        Аргументы:
            row: Строка OSD-сетки (0–21)
            col: Колонка OSD-сетки (0–59)
            text: Текст для отображения (макс. 15 символов)
            font_number: Номер шрифта (0–3)
            blink: Мигание текста
        """
        logger_msp.debug(
            f'OSD write_string: row={row}, col={col}, text="{text}"'
        )
        packet = create_osd_string(
            row=row, col=col, text=text,
            font_number=font_number, blink=blink,
        )
        self._send_packet(packet)

    def draw_screen(self) -> None:
        """Финализирует и отображает кадр (MSP_DP_DRAW_SCREEN)."""
        logger_msp.debug('Отрисовка кадра OSD')
        packet = build_msp_dp_packet(MSP_DP_COMANDS['MSP_DP_DRAW_SCREEN'])
        self._send_packet(packet)
        time.sleep(0.01)

    def heartbeat(self) -> None:
        """Отправляет heartbeat (MSP_DP_HEARTBEAT)."""
        packet = build_msp_dp_packet(MSP_DP_COMANDS['MSP_DP_HEARTBEAT'])
        self._send_packet(packet)

    # ------------------------------------------------------------------
    # High-level helpers
    # ------------------------------------------------------------------

    def show_text(
        self,
        row: int,
        col: int,
        text: str,
        font_number: int = 0,
        blink: bool = False,
        clear: bool = True,
    ) -> None:
        """
        Высокоуровневый метод: очистка + запись + отрисовка за один вызов.

        Аргументы:
            row: Строка OSD-сетки
            col: Колонка OSD-сетки
            text: Текст для отображения
            font_number: Номер шрифта (0–3)
            blink: Мигание текста
            clear: Очищать ли экран перед выводом
        """
        if clear:
            self.clear_screen()
        self.write_string(
            row=row, col=col, text=text,
            font_number=font_number, blink=blink,
        )
        self.draw_screen()
        logger_msp.info(
            f'OSD показан: row={row}, col={col}, text="{text}"'
        )
