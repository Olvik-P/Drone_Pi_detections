# Drone Pi Detections

Система детекции человека на дроне (Betaflight) с помощью **Raspberry Pi Zero + OpenCV** и выводом координат в **DJI FPV очки** через MSP DisplayPort.

## Архитектура

```
┌─────────────────┐     ┌────────────────────┐    ┌──────────────────────┐
│  app_detect     │     │  detection_pipeline│    │  app_msp             │
│                 │     │                    │    │                      │
│  Camera ───────►│────►│  YuNet детекция    │───►│  OSDController       │───► DJI Goggles
│  (VideoCapture) │     │  → bbox → OSD grid │    │  (MSP DisplayPort)   │
│                 │     │  → MSP отправка    │    │                      │
└─────────────────┘     └────────────────────┘    └──────────────────────┘
         │                       │
         ▼                       ▼
   app_logger              app_logger
   (logger_detect)         (logger_msp)
```

## Компоненты

| Модуль                                                                     | Назначение                        |
|----------------------------------------------------------------------------|-----------------------------------|
| [`app_detect`](app_detect/__init__.py)                                     | Детекция лиц через YuNet (OpenCV) |
| [`app_detect/detection_pipeline.py`](app_detect/detection_pipeline.py)     | Пайплайн: камера → детекция → OSD |
| [`app_msp`](app_msp/__init__.py)                                           | MSP-протокол для DJI DisplayPort  |
| [`app_msp/osd_controller.py`](app_msp/o----sd_controller.py)               | Высокоуровневый контроллер OSD    |
| [`app_logger`](app_logger/__init__.py)                                     | Логирование (loguru)              |
| [`main.py`](main.py)                                                       | Точка входа                       |

## Установка

```bash
# Клонировать репозиторий
git clone <url>
cd Drone_Pi_detections

# Установить зависимости
python -m pip install -r req.txt
```

## Использование

```bash
# Запуск с автоопределением порта
python main.py

# Windows (тестирование через USB-COM)
python main.py --port COM4

# Raspberry Pi (UART)
python main.py --port /dev/ttyAMA0

# Headless-режим (без окна OpenCV)
python main.py --no-display

# Лимит кадров (100 кадров)
python main.py --max-frames 100

# Другая камера
python main.py --camera-index 1
```

## Принцип работы

1. **Захват кадра** — камера Raspberry Pi (640×360)
2. **Детекция** — YuNet (ONNX) определяет лицо, возвращает bbox
3. **Конвертация** — нормализованные координаты bbox (0.0–1.0) → OSD-сетка (60×22)
4. **Отправка** — MSP DisplayPort пакет: `MSP_DP_CLEAR_SCREEN` → `MSP_DP_WRITE_STRING` → `MSP_DP_DRAW_SCREEN`
5. **Отображение** — (опционально) окно OpenCV с bbox и OSD-координатами

## Зависимости

- Python 3.13+
- opencv-python 4.13.0
- numpy 2.4+
- pyserial 3.5
- loguru 0.7+
- python-dotenv 1.2+

## Формат OSD-сетки (DJI FPV)

- **60 колонок** × **22 строки**
- Координаты: `col` (0–59), `row` (0–21)
- Текст: до 15 символов
- Шрифты: 0–3
- Поддержка мигания