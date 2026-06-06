"""
Главная точка входа для системы детекции человека на дроне.

Запускает пайплайн: камера → детекция лица (YuNet) → OSD-координаты
→ отправка в DJI FPV очки через MSP DisplayPort.

Использование:
    python main.py                          # Автоопределение порта
    python main.py --port COM4              # Windows-тест
    python main.py --port /dev/ttyAMA0      # Raspberry Pi
    python main.py --no-display             # Headless-режим
    python main.py --max-frames 100         # Лимит кадров
    python main.py --camera-index 1         # Другая камера
"""

from __future__ import annotations

import argparse
import sys

import cv2

from app_logger import logger_detect
from app_detect import constants
from app_detect.video_detector import FaceDetector, VideoCaptureManager
from app_detect.detection_pipeline import DetectionPipeline
from app_msp.osd_controller import OSDController


def parse_args() -> argparse.Namespace:
    """Парсит аргументы командной строки."""
    parser = argparse.ArgumentParser(
        description='Детекция человека на дроне с выводом в DJI OSD',
    )
    parser.add_argument(
        '--port',
        type=str,
        default=None,
        help=(
            'Последовательный порт для MSP '
            '(например, COM4, /dev/ttyAMA0).'
        ),
    )
    parser.add_argument(
        '--no-display',
        action='store_true',
        default=False,
        help='Отключить отображение окна OpenCV (headless-режим).',
    )
    parser.add_argument(
        '--max-frames',
        type=int,
        default=0,
        help='Максимальное количество кадров (0 = без лимита).',
    )
    parser.add_argument(
        '--camera-index',
        type=int,
        default=constants.DEFAULT_CAMERA_INDEX,
        help=(
            'Индекс камеры '
            f'(по умолчанию: {constants.DEFAULT_CAMERA_INDEX}).'
        ),
    )
    return parser.parse_args()


def main() -> None:
    """Главная функция запуска системы детекции."""
    args = parse_args()

    logger_detect.info(constants.MESSAGE_STARTUP_HEADER)
    mode_str = 'headless' if args.no_display else 'оконный'
    limit_str = (
        'без лимита' if args.max_frames == 0 else str(args.max_frames)
    )
    logger_detect.info(f'Режим: {mode_str}, лимит кадров: {limit_str}')

    # Определяем порт MSP
    msp_port = args.port or constants.DEFAULT_MSP_PORT
    logger_detect.info(f'MSP порт: {msp_port}')

    # ------------------------------------------------------------------
    # Инициализация компонентов
    # ------------------------------------------------------------------

    # 1. Камера
    try:
        video_manager = VideoCaptureManager(camera_index=args.camera_index)
        video_manager.open()
        if not video_manager.is_open:
            logger_detect.error('Не удалось открыть камеру')
            sys.exit(1)
    except Exception as e:
        logger_detect.error(f'Ошибка инициализации камеры: {e}')
        sys.exit(1)

    # 2. Детектор
    try:
        detector = FaceDetector(
            model_path=constants.DEFAULT_MODEL_PATH,
            score_threshold=constants.DEFAULT_SCORE_THRESHOLD,
            nms_threshold=constants.DEFAULT_NMS_THRESHOLD,
        )
    except Exception as e:
        logger_detect.error(
            constants.ERROR_DETECTOR_INIT_FAILED.format(error=e)
        )
        video_manager.release()
        sys.exit(1)

    # 3. OSD-контроллер (пробуем подключиться, но не фатально при ошибке)
    osd_controller = None
    try:
        osd_controller = OSDController(
            port=msp_port,
            baudrate=constants.MSP_BAUDRATE,
            timeout=constants.MSP_TIMEOUT,
        )
        osd_controller.open()
        logger_detect.info(f'OSD-контроллер подключён к {msp_port}')
    except Exception as e:
        logger_detect.warning(
            f'Не удалось подключиться к MSP-порту {msp_port}: {e}. '
            'Продолжаем без OSD.'
        )

    # ------------------------------------------------------------------
    # Запуск пайплайна
    # ------------------------------------------------------------------

    pipeline = DetectionPipeline(
        detector=detector,
        video_manager=video_manager,
        osd_controller=osd_controller,
        no_display=args.no_display,
        max_frames=args.max_frames,
    )

    try:
        osd_col, osd_row = pipeline.run()
        logger_detect.info(
            f'Пайплайн завершён. Последние OSD-координаты: '
            f'col={osd_col}, row={osd_row}'
        )
    except KeyboardInterrupt:
        logger_detect.info(constants.MESSAGE_INTERRUPTED)
    except Exception as e:
        logger_detect.error(
            constants.MESSAGE_UNEXPECTED_ERROR.format(error=e)
        )
    finally:
        # Освобождение ресурсов
        video_manager.release()
        if osd_controller is not None:
            osd_controller.close()
        cv2.destroyAllWindows()
        logger_detect.info(constants.MESSAGE_PROGRAM_COMPLETED)


if __name__ == '__main__':
    main()
