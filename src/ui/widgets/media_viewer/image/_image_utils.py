from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy


class ZoomableImageLabel(QLabel):
    """QLabel that supports Ctrl + Wheel zoom."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._pixmap_orig: QPixmap | None = None
        self._zoom = 1.0
        self._viewport = None
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setMinimumSize(1, 1)

    def set_viewport(self, viewport) -> None:
        self._viewport = viewport
        self._viewport.installEventFilter(self)

    def set_pix_map(self, px: QPixmap) -> None:
        self._pixmap_orig = px
        self._zoom = 1.0
        self._render()

    def wheelEvent(self, event) -> None:  # noqa: N802
        if event.modifiers() & Qt.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else (1 / 1.15)
            self._zoom = max(0.1, min(self._zoom * factor, 8.0))
            self._render()
            event.accept()
        else:
            super().wheelEvent(event)

    def adjust_zoom(self, factor: float) -> None:
        self._zoom = max(0.1, min(self._zoom * factor, 8.0))
        self._render()

    def reset_zoom(self) -> None:
        self._zoom = 1.0
        if self._pixmap_orig:
            self._render()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self._pixmap_orig and self._zoom == 1.0:
            self._render()

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if watched is self._viewport and event.type() == QEvent.Resize:
            if self._pixmap_orig and self._zoom == 1.0:
                self._render()
        return super().eventFilter(watched, event)

    def _fit_scale(self) -> float:
        if self._pixmap_orig is None or self._viewport is None:
            return 1.0

        viewport_size = self._viewport.size()
        if viewport_size.width() <= 0 or viewport_size.height() <= 0:
            return 1.0

        width_scale = viewport_size.width() / self._pixmap_orig.width()
        height_scale = viewport_size.height() / self._pixmap_orig.height()
        return min(width_scale, height_scale, 1.0)

    def _render(self) -> None:
        if self._pixmap_orig is None:
            return

        scale = max(0.1, self._fit_scale() * self._zoom)
        w = max(1, int(self._pixmap_orig.width() * scale))
        h = max(1, int(self._pixmap_orig.height() * scale))
        scaled = self._pixmap_orig.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(scaled)
        self.resize(scaled.size())
