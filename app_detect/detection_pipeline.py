"""
Пайплайн детекции человека с отправкой координат в DJI OSD.

Связывает модули:
  - app_detect.video_detector (FaceDetector, VideoCaptureManager)
  - app_msp.osd_controller (OSDController)

Основной цикл:
  1. Захват кадра с камеры
  2. Детекция лица через YuNet
  3. Конвертация bbox в OSD-координаты (сетка 60×22)
  4. Отправка координат в DJI очки через MSP DisplayPort
  5. (Опционально) отображение кадра в окне OpenCV
"""

from __future__ import annotations

import cv2
from typing import Optional, Tuple

from app_logger import logger_detect
from app_detect import constants
from app_detect.video_detector import (
    FaceDetector,
    VideoCaptureManager,
    DetectionResult,
)
from app_msp.osd_controller import OSDController


class DetectionPipeline:
    """
    Пайплайн: камера → детекция → OSD-координаты → DJI очки.

    Управляет жизненным циклом детекции: инициализация, основной цикл,
    освобождение ресурсов.

    Атрибуты:
        detector: Детектор лиц YuNet
        video_manager: Менеджер захвата видео
        osd_controller: Контроллер OSD для DJI очков
        no_display: Не показывать окно OpenCV (headless-режим)
        max_frames: Максимальное количество кадров (0 = без лимита)
    """

    def __init__(
        self,
        detector: FaceDetector,
        video_manager: VideoCaptureManager,
        osd_controller: Optional[OSDController] = None,
        no_display: bool = False,
        max_frames: int = 0,
    ) -> None:
        self.detector = detector
        self.video_manager = video_manager
        self.osd_controller = osd_controller
        self.no_display = no_display
        self.max_frames = max_frames

        # Статистика
        self.frame_count: int = 0
        self.detection_count: int = 0

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> Tuple[int, int]:
        """
        Запускает основной цикл детекции.

        Возвращает:
            tuple: (osd_col, osd_row) — последние обнаруженные координаты
                   или (0, 0), если ничего не обнаружено.
        """
        last_osd_col, last_osd_row = 0, 0
        person_present = False

        logger_detect.info(constants.MESSAGE_DETECTION_STARTED)

        while True:
            # Проверка лимита кадров
            if self.max_frames > 0 and self.frame_count >= self.max_frames:
                logger_detect.info(
                    f'Достигнут лимит кадров: {self.max_frames}'
                )
                break

            # Чтение кадра
            ret, frame = self.video_manager.read_frame()
            if not ret:
                logger_detect.warning(constants.ERROR_FRAME_READ)
                break

            self.frame_count += 1

            # Детекция
            success, detections = self.detector.detect_faces(frame)

            if success and detections:
                self.detection_count += len(detections)

                # Берём первое (самое уверенное) обнаружение
                best: DetectionResult = detections[0]

                # Конвертация bbox в OSD-координаты
                frame_h, frame_w = frame.shape[:2]
                bbox_norm = (
                    best.x / frame_w,
                    best.y / frame_h,
                    (best.x + best.width) / frame_w,
                    (best.y + best.height) / frame_h,
                )
                osd_col, osd_row = DetectionResult.bbox_to_osd_grid(bbox_norm)
                last_osd_col, last_osd_row = osd_col, osd_row

                # Отправка в DJI OSD (если контроллер подключён)
                if self.osd_controller is not None:
                    self._update_osd(osd_col, osd_row)

                # Отрисовка на кадре
                frame = self.detector.draw_detections(frame, detections)

                if not person_present:
                    person_present = True
                    logger_detect.info(
                        f'Человек обнаружен! OSD: col={osd_col}, row={osd_row}'
                    )

                # Статистика
                if (self.frame_count % constants.STATS_PRINT_INTERVAL == 0
                        and not constants.DO_NOT_DISPLAY_STATISTICS):
                    logger_detect.info(
                        constants.MESSAGE_FRAME_STATS.format(
                            frame_count=self.frame_count,
                            faces_count=len(detections),
                        )
                    )
            else:
                if person_present:
                    person_present = False
                    logger_detect.info('Человек потерян из кадра')
                    # Очищаем OSD при потере человека
                    if self.osd_controller is not None:
                        self._clear_osd()

            # Отображение
            if not self.no_display:
                cv2.imshow(constants.WINDOW_TITLE, frame)
                if cv2.waitKey(constants.WAIT_KEY_DELAY) & 0xFF == ord('q'):
                    logger_detect.info(constants.MESSAGE_EXIT_BY_KEY)
                    break

        # Финальная статистика
        self._print_stats()

        return last_osd_col, last_osd_row

    # ------------------------------------------------------------------
    # OSD helpers
    # ------------------------------------------------------------------

    def _update_osd(self, col: int, row: int) -> None:
        """Обновляет OSD-дисплей DJI: очистка + текст + отрисовка."""
        try:
            self.osd_controller.clear_screen()
            self.osd_controller.write_string(
                row=row,
                col=col,
                text=constants.OSD_DEFAULT_TEXT,
                font_number=constants.OSD_FONT_DEFAULT,
                blink=constants.OSD_BLINK_DEFAULT,
            )
            self.osd_controller.draw_screen()
        except Exception as e:
            logger_detect.error(f'Ошибка отправки OSD: {e}')

    def _clear_osd(self) -> None:
        """Очищает OSD-дисплей при потере человека."""
        try:
            self.osd_controller.clear_screen()
            self.osd_controller.draw_screen()
        except Exception as e:
            logger_detect.error(f'Ошибка очистки OSD: {e}')

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def _print_stats(self) -> None:
        """Выводит итоговую статистику работы."""
        logger_detect.info(constants.MESSAGE_STATS_HEADER)
        logger_detect.info(
            constants.MESSAGE_FRAMES_PROCESSED.format(
                frame_count=self.frame_count,
            )
        )
        logger_detect.info(
            constants.MESSAGE_FACES_DETECTED.format(
                detection_count=self.detection_count,
            )
        )
        if self.frame_count > 0:
            avg = self.detection_count / self.frame_count
            logger_detect.info(
                constants.MESSAGE_AVERAGE_FACES_PER_FRAME.format(average=avg)
            )
