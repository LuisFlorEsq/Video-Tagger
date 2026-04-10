from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QLabel,
    QSizePolicy
)
from src.domain.models.media.media_item import MediaItem
from src.domain.models.media.image_item import ImageItem

class _ZoomableImageLabel(QLabel):
    """QLabel that supports Ctrl + Wheel zoom."""
    
    def __init__(self, text, parent = None) -> None:
        super().__init__(parent)
        self._pixmap_orig: QPixmap | None = None
        self._zoom = 1.0
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(200, 200)
        
    def set_pix_map(self, px: QPixmap) -> None:
        self._pixmap_orig = px
        self._zoom = 1.0
        self._render()
        
    def wheelEvent(self, event) -> None:
        if event.modifiers() & Qt.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else (1 / 1.15)
            self._zoom =  max(0.1, min(self._zoom * factor), 8.0)
            self._render()
            event.accept()
        else: 
            super.wheelEvent(event)
            
    def adjust_zoom(self, factor: float) -> None:
        self._zoom = max(0.1, min(self._zoom * factor, 8.0))
        self._render()
        
    def reset_zoom(self) -> None:
        self._zoom = 1.0
        if self._pixmap_orig:
            self._render()
            
    def _render(self) -> None:
        if self._pixmap_orig is None:
            return
        w = int(self._pixmap_orig.width() * self._zoom)
        h = int(self._pixmap_orig.height() * self._zoom)
        self.setPixmap(
            self._pixmap_orig.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )