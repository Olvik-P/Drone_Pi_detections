"""
Главная точка входа для системы детекции человека на дроне.

Запускает пайплайн: камера → детекция лица (YuNet) → OSD-координаты
→ отправка в DJI FPV очки через MSP DisplayPort.
"""

import sys

import cv2

from app_logger import logger_detect
from app_detect import constants
from app_detect.video_detector import FaceDetector, VideoCaptureManager
from app_msp.osd_msp_client import OSDController


def main() -> None:
    """Главная функция запуска системы детекции."""
    # ------------------------------------------------------------------
    # Инициализация компонентов
    # ------------------------------------------------------------------

    # 1. Камера
    try:
        video_manager = VideoCaptureManager(
            camera_index=constants.DEFAULT_CAMERA_INDEX
        )
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
            port=constants.DEFAULT_MSP_PORT,
            baudrate=constants.MSP_BAUDRATE,
            timeout=constants.MSP_TIMEOUT,
        )
        osd_controller.open()
        logger_detect.info(
            f'OSD-контроллер подключён к {constants.DEFAULT_MSP_PORT}')
    except Exception as e:
        logger_detect.warning(
            f'Не удалось подключиться к MSP-порту {constants.DEFAULT_MSP_PORT}: {e}. '
            'Продолжаем без OSD.'
        )

    # ------------------------------------------------------------------
    # Запуск пайплайна
    # ------------------------------------------------------------------

    pipeline = DetectionPipeline(
        detector=detector,
        video_manager=video_manager,
        osd_controller=osd_controller
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
