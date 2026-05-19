'''
Константы для модуля детекции лиц.

Содержит текстовые константы, магические числа и параметры по умолчанию,
используемые в video_detector.py и других модулях.
'''
from typing import Tuple
from pathlib import Path

# ============================================================================
# Model Default Parameters
# ============================================================================
DEFAULT_MODEL_NAME = 'face_detection_yunet_2023mar.onnx'
DEFAULT_MODEL_PATH: str = Path(__file__).parent / DEFAULT_MODEL_NAME
DEFAULT_INPUT_SIZE: Tuple[int, int] = (320, 320)
DEFAULT_SCORE_THRESHOLD: float = 0.7
DEFAULT_NMS_THRESHOLD: float = 0.3
DEFAULT_TOP_K: int = 5000

# ============================================================================
# Camera Parameters
# ============================================================================
CAMERA_WIDTH: int = 640
CAMERA_HEIGHT: int = 360
DEFAULT_CAMERA_INDEX: int = 0

# ============================================================================
# Visualization Parameters
# ============================================================================
COLOR_GREEN: Tuple[int, int, int] = (0, 255, 0)
LINE_THICKNESS: int = 2
FONT_SCALE: float = 0.7
TEXT_Y_OFFSET: int = -10

# ============================================================================
# Timing and Intervals
# ============================================================================
STATS_PRINT_INTERVAL: int = 30  # Print stats every N frames
DO_NOT_DISPLAY_STATISTICS = True
WAIT_KEY_DELAY: int = 1  # Delay in ms for cv2.waitKey

# ============================================================================
# String Formatting
# ============================================================================
LABEL_FORMAT: str = 'Face: {confidence:.2f}'
WINDOW_TITLE: str = 'Real-time Human Detection'
SEPARATOR_LENGTH: int = 40

# ============================================================================
# Log Messages
# ============================================================================
# Error messages
ERROR_CAMERA_OPEN: str = (
    'Ошибка: не удалось открыть камеру с индексом {camera_index}'
)
ERROR_CAMERA_OPEN_GENERIC: str = 'Ошибка при открытии камеры: {error}'
ERROR_DETECTOR_INIT: str = 'Ошибка при инициализации детектора: {error}'
ERROR_FRAME_READ: str = 'Ошибка: не удалось получить кадр'
ERROR_DETECTOR_INIT_FAILED: str = (
    'Не удалось инициализировать детектор: {error}'
)

# Informational messages
MESSAGE_CAMERA_OPENED: str = 'Камера открыта: {width}x{height} @ {fps} FPS'
MESSAGE_DETECTOR_INITIALIZED: str = (
    'Детектор инициализирован с моделью: {model_path}'
)
MESSAGE_RESOURCES_RELEASED: str = 'Ресурсы камеры освобождены'
MESSAGE_DETECTION_STARTED: str = 'Детекция запущена. Нажмите "q" для выхода.'
MESSAGE_EXIT_BY_KEY: str = 'Запрошен выход по клавише "q"'
MESSAGE_INTERRUPTED: str = 'Прервано пользователем (Ctrl+C)'
MESSAGE_UNEXPECTED_ERROR: str = 'Неожиданная ошибка: {error}'
MESSAGE_STATS_HEADER: str = 'Статистика работы:'
MESSAGE_FRAMES_PROCESSED: str = 'Обработано кадров: {frame_count}'
MESSAGE_FACES_DETECTED: str = 'Обнаружено лиц: {detection_count}'
MESSAGE_AVERAGE_FACES_PER_FRAME: str = (
    'Среднее количество лиц на кадр: {average:.2f}'
)
MESSAGE_PROGRAM_COMPLETED: str = 'Программа завершена'
MESSAGE_STARTUP_HEADER: str = 'Запуск детекции лиц в реальном времени'
MESSAGE_FRAME_STATS: str = 'Кадр {frame_count}: обнаружено {faces_count} лиц'
