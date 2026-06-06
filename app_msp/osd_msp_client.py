import struct
import serial
import time
import sys

from app_msp.constants import MSP_DP_COMMANDS
from app_logger import logger_msp as logger


class OSDMSPClient:

    @staticmethod
    def _calculate_checksum(data: bytes) -> int:
        checksum = 0
        for byte in data:
            checksum ^= byte
        return checksum

    @staticmethod
    def _create_attribute(font_number: int = 0, blink: bool = False) -> int:
        if not (0 <= font_number <= 3):
            raise ValueError(
                f'Неверный font_number = {font_number}, должен быть от 0 до 3!')
        attr = font_number
        if blink:
            attr |= (1 << 6)
        return attr

    def _build_msp_dp_packet(self, subcommand: int, payload: bytes = b"") -> bytes:
        full_payload = bytes([subcommand]) + payload
        payload_size = len(full_payload)
        header = b'$M<' + \
            struct.pack('<BB', payload_size,
                        MSP_DP_COMMANDS['MSP_DISPLAYPORT'])
        checksum_data = struct.pack(
            '<BB', payload_size, MSP_DP_COMMANDS['MSP_DISPLAYPORT']) + full_payload
        checksum = self._calculate_checksum(checksum_data)
        return header + full_payload + bytes([checksum])

    def _create_osd_string(
            self,
            row: int = 0,
            col: int = 0,
            text: str = 'Human',
            font_number: int = 0,
            blink: bool = False
    ) -> bytes:
        if len(text) > 15:
            logger.warning(f'Текст обрезан до 15 символов (было {len(text)})')
            text = text[:15]

        attribute = self._create_attribute(font_number, blink)
        data = struct.pack('<BBB', row, col, attribute)
        text_bytes = text.encode('utf-8')
        if len(text_bytes) > 30:
            logger.warning(
                f"Текст в байтах больше 30 ({len(text_bytes)}), обрезаем")
            text_bytes = text_bytes[:30]
        data += text_bytes + b'\x00'
        return self._build_msp_dp_packet(MSP_DP_COMMANDS['MSP_DP_WRITE_STRING'], data)

    def show_string_dji_googles(
            self,
            port: str,
            row: int,
            col: int,
            text: str = 'Human',
            font: int = 0,
            blink: bool = False,
            clear: bool = False
    ) -> bool:
        ser = None
        try:
            logger.info(f'Открываем порт {port}')
            ser = serial.Serial(port, 115200, timeout=0.1)
            time.sleep(0.1)

            if clear:
                logger.info('🧹 Очистка экрана...')
                clear_packet = self._build_msp_dp_packet(
                    MSP_DP_COMMANDS['MSP_DP_CLEAR_SCREEN'])
                ser.write(clear_packet)
                ser.flush()
                time.sleep(0.1)

            logger.info(f'📝 Отправка текста: "{text}" в row={row}, col={col}')
            write_packet = self._create_osd_string(row, col, text, font, blink)
            logger.debug(
                f'   Пакет ({len(write_packet)} байт): {write_packet.hex()}')
            ser.write(write_packet)
            ser.flush()
            time.sleep(0.01)

            logger.info('🎬 Отрисовка кадра...')
            draw_packet = self._build_msp_dp_packet(
                MSP_DP_COMMANDS['MSP_DP_DRAW_SCREEN'])
            ser.write(draw_packet)
            ser.flush()
            time.sleep(0.01)

            logger.info('✅ Успешно!')
            return True

        except serial.SerialException as e:
            logger.error(f'❌ Ошибка последовательного порта: {e}')
            return False
        except Exception as e:
            logger.error(f'❌ Неожиданная ошибка: {e}')
            return False
        finally:
            if ser and ser.is_open:
                ser.close()
                logger.info('🔌 Порт закрыт')


msp_client = OSDMSPClient()
