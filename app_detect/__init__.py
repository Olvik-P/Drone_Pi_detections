"""
Модуль детекции лиц с использованием OpenCV.

Этот модуль предоставляет обнаружение лиц в реальном времени с использованием
модели YuNet от OpenCV. Включает классы для детекции лиц, управления захватом
видео и вспомогательные утилиты.

Экспортирует:
    FaceDetector: Основной класс детекции лиц
    VideoCaptureManager: Класс управления камерой
    DetectionResult: Класс данных для результатов обнаружения
    constants: Константы модуля
"""

from .video_detector import FaceDetector, VideoCaptureManager, DetectionResult
from . import constants

__version__ = '1.0.0'
__author__ = 'Drone_Pi_detections'
__all__ = [
    'FaceDetector',
    'VideoCaptureManager',
    'DetectionResult',
    'constants',
]
