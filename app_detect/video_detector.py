"""
Модуль детекции лиц в реальном времени.

Использует OpenCV и модель YuNet для обнаружения лиц в видеопотоках.

Основные возможности:
- Обнаружение лиц в видеопотоке веб-камеры
- Визуализация с ограничивающими рамками и метками уверенности
- Поддержка headless-режима (без отображения окна)
"""

import cv2
import numpy as np
from typing import Optional, Tuple, List
from dataclasses import dataclass
from app_logger import logger_detect
from app_detect import constants
from pathlib import Path


@dataclass
class DetectionResult:
    """Представляет результат обнаружения одного лица."""
    x: int
    y: int
    width: int
    height: int
    confidence: float

    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        """Возвращает ограничивающую рамку в формате (x1, y1, x2, y2)."""
        return (self.x, self.y, self.x + self.width, self.y + self.height)

    @staticmethod
    def bbox_to_osd_grid(
        bbox_normalized,
        canvas_cols: int = 60,
        canvas_rows: int = 22
    ) -> tuple:
        """
        Конвертирует нормализованный BBox YuNet в координаты OSD-сетки.

        YuNet возвращает координаты в диапазоне 0.0–1.0 относительно
        размеров кадра. Этот метод масштабирует их в OSD-сетку
        (60 колонок x 22 строки для DJI FPV).

        Аргументы:
            bbox_normalized: кортеж/список [x1, y1, x2, y2] в диапазоне 0.0-1.0
            canvas_cols: ширина OSD-холста (60 для DJI)
            canvas_rows: высота OSD-холста (22 для DJI)

        Возвращает:
            tuple: (center_col, center_row) — координаты OSD
        """
        x1, y1, x2, y2 = bbox_normalized

        # Вычисляем геометрический центр рамки (в нормализованных координатах)
        center_x = (x1 + x2) / 2.0
        center_y = (y1 + y2) / 2.0

        # Масштабируем в OSD-сетку
        osd_col = int(center_x * canvas_cols)
        osd_row = int(center_y * canvas_rows)

        # Защита от выхода за границы
        osd_col = max(0, min(osd_col, canvas_cols - 1))
        osd_row = max(0, min(osd_row, canvas_rows - 1))

        return osd_col, osd_row

    @classmethod
    def from_array(cls, arr: np.ndarray) -> 'DetectionResult':
        """Создает DetectionResult из массива [x, y, w, h, confidence]."""
        return cls(
            x=int(arr[0]),
            y=int(arr[1]),
            width=int(arr[2]),
            height=int(arr[3]),
            confidence=float(arr[4])
        )


class FaceDetector:
    """
    Детектор лиц с использованием модели YuNet от OpenCV.

    YuNet (You Only Look Once for Face) — это легкая нейронная сеть
    для обнаружения лиц, оптимизированная для работы в реальном времени.
    """

    def __init__(
        self,
        model_path: str = constants.DEFAULT_MODEL_PATH,
        input_size: Tuple[int, int] = constants.DEFAULT_INPUT_SIZE,
        score_threshold: float = constants.DEFAULT_SCORE_THRESHOLD,
        nms_threshold: float = constants.DEFAULT_NMS_THRESHOLD,
        top_k: int = constants.DEFAULT_TOP_K
    ):
        """
        Инициализирует детектор лиц.

        Аргументы:
            model_path: Путь к файлу модели ONNX
            input_size: Размер входного изображения для модели (ширина, высота)
            score_threshold: Порог уверенности для обнаружения
            nms_threshold: Порог подавления немаксимумов (NMS)
            top_k: Максимальное количество обнаружений для возврата
        """
        self.model_path = model_path
        self.input_size = input_size
        self.score_threshold = score_threshold
        self.nms_threshold = nms_threshold
        self.top_k = top_k

        self.detector = None
        self._initialize_detector()

    def _initialize_detector(self) -> None:
        """Инициализирует детектор OpenCV с обработкой ошибок."""
        model_path = Path(self.model_path)
        if not model_path.exists():
            logger_detect.error(f'Model file not found: {model_path}')
            raise FileNotFoundError(f'Model file not found: {model_path}')

        try:
            self.detector = cv2.FaceDetectorYN_create(
                str(model_path),
                '',
                self.input_size,
                self.score_threshold,
                self.nms_threshold,
                self.top_k
            )
            logger_detect.info(
                constants.MESSAGE_DETECTOR_INITIALIZED.format(
                    model_path=model_path
                )
            )
        except Exception as e:
            logger_detect.error(
                constants.ERROR_DETECTOR_INIT.format(error=e)
            )
            raise RuntimeError(
                f'Failed to initialize face detector: {e}'
            ) from e

    def detect_faces(
        self, frame: cv2.Mat
    ) -> Tuple[bool, Optional[List[DetectionResult]]]:
        """
        Обнаруживает лица в кадре.

        Аргументы:
            frame: Входной кадр (изображение в формате BGR)

        Возвращает:
            Кортеж (успех, список объектов DetectionResult)
        """
        if self.detector is None:
            return False, None

        # Get frame dimensions
        height, width = frame.shape[:2]
        self.detector.setInputSize((width, height))

        # Run detection
        success, faces = self.detector.detect(frame)

        if not success or faces is None:
            return success, []

        # Convert numpy array to list of DetectionResult objects
        detections = [
            DetectionResult.from_array(face)
            for face in faces
        ]

        return success, detections

    def draw_detections(
        self,
        frame: cv2.Mat,
        detections: List[DetectionResult]
    ) -> cv2.Mat:
        """
        Рисует ограничивающие рамки и метки для обнаруженных лиц.

        Аргументы:
            frame: Исходный кадр
            detections: Список обнаруженных лиц

        Возвращает:
            Кадр с нарисованными обнаружениями
        """
        frame_with_detections = frame.copy()

        for detection in detections:
            x1, y1, x2, y2 = detection.bbox

            # Нормализованные координаты для OSD-сетки
            frame_height, frame_width = frame.shape[:2]
            bbox_norm = (
                x1 / frame_width,
                y1 / frame_height,
                x2 / frame_width,
                y2 / frame_height,
            )
            label_osd_col, label_osd_row = DetectionResult.bbox_to_osd_grid(
                bbox_norm
            )

            # Draw rectangle around face
            cv2.rectangle(
                frame_with_detections,
                (x1, y1),
                (x2, y2),
                constants.COLOR_GREEN,
                constants.LINE_THICKNESS
            )

            # Add confidence label
            label = f'Human: col={label_osd_col}, row={label_osd_row}'

            cv2.putText(
                frame_with_detections,
                label,
                (x1, y1 + constants.TEXT_Y_OFFSET),
                cv2.FONT_HERSHEY_SIMPLEX,
                constants.FONT_SCALE,
                constants.COLOR_GREEN,
                constants.LINE_THICKNESS
            )

        return frame_with_detections, label_osd_col, label_osd_row


class VideoCaptureManager:
    """Менеджер захвата видеопотока с поддержкой контекстного менеджера."""

    def __init__(self, camera_index: int = constants.DEFAULT_CAMERA_INDEX):
        """
        Инициализирует менеджер захвата видео.

        Аргументы:
            camera_index: Индекс камеры (0 для камеры по умолчанию)
        """
        self.camera_index = camera_index
        self.cap = None
        self._is_open = False

    def __enter__(self):
        """Вход в контекстный менеджер."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Выход из контекстного менеджера."""
        self.release()

    def open(self) -> bool:
        """Открывает камеру для захвата видео."""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                logger_detect.error(
                    constants.ERROR_CAMERA_OPEN.format(
                        camera_index=self.camera_index
                    )
                )
                return False

            # Try to set preferred resolution, but don't fail if not supported
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, constants.CAMERA_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, constants.CAMERA_HEIGHT)

            # Get actual camera properties
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(self.cap.get(cv2.CAP_PROP_FPS))

            logger_detect.info(
                constants.MESSAGE_CAMERA_OPENED.format(
                    width=width, height=height, fps=fps
                )
            )
            self._is_open = True
            return True

        except Exception as e:
            logger_detect.error(
                constants.ERROR_CAMERA_OPEN_GENERIC.format(error=e)
            )
            return False

    def read_frame(self) -> Tuple[bool, Optional[cv2.Mat]]:
        """
        Читает следующий кадр с камеры.

        Возвращает:
            Кортеж (успех, кадр). Возвращает (False, None),
            если камера не открыта.
        """
        if not self._is_open or self.cap is None:
            return False, None

        ret, frame = self.cap.read()
        if not ret:
            logger_detect.warning(constants.ERROR_FRAME_READ)

        return ret, frame

    def release(self) -> None:
        """Освобождает ресурсы камеры."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            self._is_open = False
            logger_detect.info(constants.MESSAGE_RESOURCES_RELEASED)

    @property
    def is_open(self) -> bool:
        """Проверяет, открыта ли камера и готова ли к работе."""
        return self._is_open and self.cap is not None
