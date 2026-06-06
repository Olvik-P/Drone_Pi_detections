import struct
import serial
import time


MSP_DP_COMANDS = {
    'MSP_DISPLAYPORT': 182,     # Главная команда DisplayPort
    'MSP_DP_HEARTBEAT': 0,      # 'Я живой' сигнал
    'MSP_DP_RELEASE': 1,        # Освободить дисплей
    'MSP_DP_CLEAR_SCREEN': 2,   # Очистить экран
    'MSP_DP_WRITE_STRING': 3,   # Написать строку
    'MSP_DP_DRAW_SCREEN': 4,    # Показать кадр
    'MSP_DP_OPTIONS': 5,        # Настройки разрешения
    'MSP_DP_SYS': 6,            # Системные элементы
}


def calculate_checksum(data: bytes) -> int:
    checksum = 0
    for byte in data:
        checksum ^= byte
    return checksum


def create_attribute(font_number: int = 0, blink: bool = False) -> int:
    # Проверяем, что номер шрифта в допустимом диапазон
    if font_number < 0 or font_number > 3:
        raise ValueError(
            f'Не правильный font_number = {
                font_number
            }, должен быть от 0 до 3!'
        )
    attrtribte = font_number
    # Устанавливаем бит 6 если нужно мигание
    if blink:
        attrtribte |= (1 << 6)
    return attrtribte


def build_msp_dp_packet(subcommand: int, payload: bytes = b'') -> bytes:
    # Шаг 1: Собираем payload — подкоманда + данные
    full_payload = bytes([subcommand]) + payload
    # Шаг 2: Считаем размер payload (это только данные, без подкоманды!)
    payload_size = len(full_payload)
    # Шаг 3: Собираем заголовок
    header = b'$M<' + \
        struct.pack('<BB', payload_size, MSP_DP_COMANDS['MSP_DISPLAYPORT'])
    # Шаг 4: Вычисляем контрольную сумму
    checksum_data = struct.pack(
        '<BB', payload_size, MSP_DP_COMANDS['MSP_DISPLAYPORT']) + full_payload
    checksum = calculate_checksum(checksum_data)
    # Шаг 5: Собираем всё вместе
    packet = header + full_payload + bytes([checksum])

    return packet


def create_osd_string(
        row: int = 0,
        col: int = 0,
        text: str = 'Human',
        font_number: int = 0,
        blink: bool = False
) -> bytes:
    if len(text) > 15:
        print(f'Текст обрезан до 15 символов (было {len(text)})')
        text = text[:15]
    # Шаг 1: Создаем атрибуты текста
    attribute = create_attribute(font_number, blink)
    # Шаг 2: Собираем данные для MSP_DP_WRITE_STRING
    data = struct.pack('<BBB', row, col, attribute)
    # Шаг 3: Добавляем текст
    text_bytes = text.encode('utf-8')
    if len(text_bytes) > 30:
        print(f'Текст в байтах больше 30 ({len(text_bytes)}), обрезаем')
        text_bytes = text_bytes[:30]
    data += text_bytes
    # Шаг 4: Добавляем признак конца строки
    data += b'\x00'
    # Шаг 5: Собираем MSP пакет с подкомандой MSP_DP_WRITE_STRING (3)
    packet = build_msp_dp_packet(MSP_DP_COMANDS['MSP_DP_WRITE_STRING'], data)

    return packet


def show_string_dji_googles(
        port: str,
        row: int,
        col: int,
        text: str = 'Human',
        font: int = 0,
        blink: bool = False,
        clear: bool = False
) -> None:
    try:
        print(f'Открываем порт {port}')
        ser = serial.Serial(port, 115200, timeout=0.1)
        time.sleep(0.1)

        # 1. Очистка экрана ДО отрисовки нового текста
        if clear:
            print('🧹 Очистка экрана...')
            clear_packet = build_msp_dp_packet(
                MSP_DP_COMANDS['MSP_DP_CLEAR_SCREEN'])
            ser.write(clear_packet)
            ser.flush()
            time.sleep(0.1)  # Даем время на обработку

        # 2. Отправка текста
        print(f'📝 Отправка текста: {text} в row={row}, col={col}')
        write_packet = create_osd_string(row, col, text, font, blink)
        print(f'   Пакет ({len(write_packet)} байт): {write_packet.hex()}')
        ser.write(write_packet)
        ser.flush()
        time.sleep(0.01)

        # 3. Команда на отрисовку кадра
        print('🎬 Отрисовка кадра...')
        draw_packet = build_msp_dp_packet(MSP_DP_COMANDS['MSP_DP_DRAW_SCREEN'])
        ser.write(draw_packet)
        ser.flush()
        time.sleep(0.01)

        print('✅ Успешно!')
        return True

    except serial.SerialException as e:
        print(f'❌ Ошибка последовательного порта: {e}')
        return False
    except Exception as e:
        print(f'❌ Неожиданная ошибка: {e}')
        return False
    finally:
        if ser and ser.is_open:
            ser.close()
            print('🔌 Порт закрыт')


if __name__ == '__main__':
    show_string_dji_googles('COM4', 0, 0)
