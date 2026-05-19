import cv2
import sys

from app_logger import logger_detect
from app_detect import constants
from app_detect.video_detector import FaceDetector, VideoCaptureManager


def run_detection(
    detector: FaceDetector,
    video_manager: VideoCaptureManager,
    no_display: bool,
    max_frames: int = 0
) -> tuple[int, int]:

    frame_count = 0
    detection_count = 0

    while True:
        # Проверка ограничения по кадрам
        if max_frames > 0 and frame_count >= max_frames:
            logger_detect.info(f'Достигнут лимит кадров: {max_frames}')
            break

        # Чтение кадра с камеры
        ret, frame = video_manager.read_frame()
        if not ret:
            logger_detect.warning(constants.ERROR_FRAME_READ)
            break

        frame_count += 1

        # Детекция лиц
        success, detections = detector.detect_faces(frame)

        # Обработка результатов
        if success and detections:
            detection_count += len(detections)

            # Отрисовка обнаружений на кадре
            frame_with_detections, osd_col, osd_row = detector.draw_detections(
                frame, detections)

            # Периодический вывод статистики
            if frame_count % constants.STATS_PRINT_INTERVAL == 0 and not constants.DO_NOT_DISPLAY_STATISTICS:
                logger_detect.info(
                    constants.MESSAGE_FRAME_STATS.format(
                        frame_count=frame_count,
                        faces_count=len(detections)
                    )
                )
        else:
            frame_with_detections = frame

        # Отображение результата (если не отключено)
        if not no_display:
            cv2.imshow(constants.WINDOW_TITLE, frame_with_detections)

            # Выход по нажатию клавиши 'q'
            if cv2.waitKey(constants.WAIT_KEY_DELAY) & 0xFF == ord('q'):
                logger_detect.info(constants.MESSAGE_EXIT_BY_KEY)
                break

    return osd_col, osd_row


def detect_face() -> None:
    logger_detect.info('Начинаем определять лицо в кадре.')

    try:
        with VideoCaptureManager(
            camera_index=constants.DEFAULT_CAMERA_INDEX
        ) as video_manager:
            if not video_manager.is_open:
                logger_detect.error('Не удалось открыть камеру')
                sys.exit(1)

            # Инициализация детектора
            try:
                detector = FaceDetector(
                    model_path=constants.DEFAULT_MODEL_PATH,
                    score_threshold=constants.DEFAULT_SCORE_THRESHOLD,
                    nms_threshold=constants.DEFAULT_NMS_THRESHOLD
                )
            except Exception as e:
                logger_detect.error(
                    constants.ERROR_DETECTOR_INIT_FAILED.format(error=e)
                )
                sys.exit(1)

            logger_detect.info(constants.MESSAGE_DETECTION_STARTED)

            # Запуск цикла детекции
            try:
                osd_col, osd_row = run_detection(
                    detector=detector,
                    video_manager=video_manager,
                    no_display=False,
                    max_frames=0
                )

            except Exception as e:
                logger_detect.error(
                    constants.MESSAGE_UNEXPECTED_ERROR.format(error=e)
                )
                osd_col, osd_row = 0, 0
            logger_detect.info(f'col={osd_col}, row={osd_row}')
            
            return osd_col, osd_row

    except Exception as e:
        logger_detect.error(f'Неожиданная ошибка в main: {e}')
        sys.exit(1)


if __name__ == '__main__':
    detect_face()
    logger_detect.info('Определение лица в кадре завершено.')
