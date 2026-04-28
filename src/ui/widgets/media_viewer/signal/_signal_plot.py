import math

import numpy as np
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from src.ui.styles import AppTheme


class WaveformWidget(QWidget):
    """Lightweight single-envelope waveform display with a playhead."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._envelope = np.zeros(0, dtype=np.float32)
        self._progress = 0.0
        self._message = "Waveform unavailable"
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def clear_waveform(self) -> None:
        self._envelope = np.zeros(0, dtype=np.float32)
        self._progress = 0.0
        self._message = "Waveform unavailable"
        self.update()

    def set_loading(self, message: str = "Loading waveform...") -> None:
        self._envelope = np.zeros(0, dtype=np.float32)
        self._progress = 0.0
        self._message = message
        self.update()

    def set_message(self, message: str) -> None:
        self._envelope = np.zeros(0, dtype=np.float32)
        self._progress = 0.0
        self._message = message
        self.update()

    def set_waveform(self, envelope: np.ndarray) -> None:
        self._envelope = np.asarray(envelope, dtype=np.float32)
        self._message = ""
        self.update()

    def set_progress(self, ratio: float) -> None:
        self._progress = max(0.0, min(1.0, float(ratio)))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(AppTheme.BG_SUBTLE))

        if self._envelope.size == 0:
            painter.setPen(QColor(AppTheme.TEXT_MUTED))
            painter.drawText(
                self.rect(),
                Qt.AlignCenter,
                self._message or "Waveform unavailable",
            )
            return

        rect = self.rect().adjusted(10, 10, -10, -10)
        center_y = rect.center().y()
        width = max(1, rect.width())
        step = width / max(1, self._envelope.size - 1)

        painter.setPen(QPen(QColor(AppTheme.BORDER), 1))
        painter.drawLine(rect.left(), center_y, rect.right(), center_y)

        pen = QPen(QColor(AppTheme.SUCCESS), 1.4)
        painter.setPen(pen)

        for index, value in enumerate(self._envelope):
            x = rect.left() + (index * step)
            amp = float(value) * (rect.height() / 2.2)
            painter.drawLine(int(x), int(center_y - amp), int(x), int(center_y + amp))

        playhead_x = rect.left() + int(self._progress * rect.width())
        painter.setPen(QPen(QColor(AppTheme.PRIMARY), 2))
        painter.drawLine(playhead_x, rect.top(), playhead_x, rect.bottom())


class SignalPlotWidget(QWidget):
    """Scrollable multi-trace numeric signal plot."""

    TRACE_COLORS = [
        QColor("#1f9d8b"),
        QColor("#0f6cbd"),
        QColor("#d97706"),
        QColor("#c2410c"),
    ]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._signals = np.zeros((0, 0), dtype=np.float32)
        self._zoom = 1.0
        self._sample_rate: int | None = None
        self.setMinimumHeight(320)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self._update_canvas_width()

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(self.width(), 360)

    def clear_plot(self) -> None:
        self._signals = np.zeros((0, 0), dtype=np.float32)
        self._zoom = 1.0
        self._update_canvas_width()
        self.update()

    def set_signal_data(self, signals: np.ndarray, sample_rate: int | None = None) -> None:
        self._signals = np.asarray(signals, dtype=np.float32)
        self._sample_rate = sample_rate
        self._zoom = 1.0
        self._update_canvas_width()
        self.update()

    def adjust_zoom(self, factor: float) -> None:
        self._zoom = max(0.25, min(self._zoom * factor, 12.0))
        self._update_canvas_width()
        self.update()

    def reset_zoom(self) -> None:
        self._zoom = 1.0
        self._update_canvas_width()
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(AppTheme.BG_SUBTLE))

        if self._signals.size == 0:
            painter.setPen(QColor(AppTheme.TEXT_MUTED))
            painter.drawText(self.rect(), Qt.AlignCenter, "No signal loaded")
            return

        rect = self.rect().adjusted(16, 16, -16, -16)
        channels, samples = self._signals.shape
        channel_height = rect.height() / max(1, channels)

        for idx in range(channels):
            channel_rect_top = rect.top() + (idx * channel_height)
            channel_rect_bottom = channel_rect_top + channel_height
            channel_rect_center = (channel_rect_top + channel_rect_bottom) / 2

            painter.setPen(QPen(QColor(AppTheme.BORDER), 1))
            painter.drawLine(
                rect.left(),
                int(channel_rect_center),
                rect.right(),
                int(channel_rect_center),
            )

            signal = self._signals[idx]
            max_abs = float(np.max(np.abs(signal))) if signal.size else 0.0
            if max_abs <= 0:
                max_abs = 1.0

            path = QPainterPath()
            step_x = rect.width() / max(1, samples - 1)
            scale_y = (channel_height * 0.42) / max_abs
            for sample_idx, sample in enumerate(signal):
                x = rect.left() + (sample_idx * step_x)
                y = channel_rect_center - (float(sample) * scale_y)
                if sample_idx == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)

            painter.setPen(QPen(self.TRACE_COLORS[idx % len(self.TRACE_COLORS)], 1.5))
            painter.drawPath(path)

            label = f"Ch {idx + 1}"
            if self._sample_rate:
                seconds = samples / self._sample_rate
                label = f"{label}  {seconds:.2f}s"
            painter.setPen(QColor(AppTheme.TEXT_SECONDARY))
            painter.drawText(
                rect.left() + 4,
                int(channel_rect_top + 16),
                label,
            )

    def _update_canvas_width(self) -> None:
        samples = int(self._signals.shape[1]) if self._signals.ndim == 2 else 0
        if samples <= 0:
            width = 640
        else:
            width = max(640, int(math.ceil(samples * self._zoom * 0.4)))
        self.setMinimumWidth(width)
        self.resize(width, self.height())
