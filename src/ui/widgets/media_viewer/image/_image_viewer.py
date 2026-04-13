from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QScrollArea
)

from src.ui.styles import AppTheme, btn_ghost
from src.ui.helpers.dividers import make_vline

from src.domain.models.media.image_item import ImageItem
from src.domain.models.project import Project

from src.ui.widgets.media_viewer._base_viewer import BaseViewer
from src.ui.widgets.media_viewer.image._image_utils import ZoomableImageLabel


class ImageViewer(BaseViewer):
    """Static image viewer with Ctrl+Wheel zoom."""

    def item_type_label(self) -> str:
        return "imagen"

    # --- Hooks ----
    def build_media_area(self) -> QWidget:
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setAlignment(Qt.AlignCenter)
        self._scroll.setStyleSheet(
            f"QScrollArea {{ background-color: {AppTheme.BG_APP}; border: none; }}"
        )

        self._image_label = ZoomableImageLabel()
        self._image_label.setStyleSheet(
            f"background-color: {AppTheme.BG_APP};"
        )
        self._scroll.setWidget(self._image_label)

        return self._scroll

    def build_info_rows(self, info_layout: QVBoxLayout) -> None:
        self.dim_label = self._info_row("DIMENSIONES", "--", info_layout)

    def _populate_topbar_extras(self, tb: QHBoxLayout) -> None:
        """Inject zoom controls between the breadcrumb stretch and position counter"""

        for text, factor, tip in [
            ("-", 0.8,  "Reducir zoom (Ctrl+-)"),
            ("1:1", None, "Restablecer zoom (Ctrl+0)"),
            ("+", 1.25, "Ampliar zoom (Ctrl++)"),
        ]:
            btn = QPushButton(text)
            btn.setFixedSize(36 if text == "1:1" else 28, 28)
            btn.setStyleSheet(btn_ghost())
            btn.setToolTip(tip)

            if factor is None:
                btn.clicked.connect(self._image_label.reset_zoom)
            else:
                btn.clicked.connect(
                    lambda _=False, f=factor: self._image_label.adjust_zoom(f))

            tb.addWidget(btn)

        tb.addSpacing(4)
        tb.addWidget(make_vline())
        tb.addSpacing(8)

    def _setup_extra_shortcuts(self, action_factory) -> None:
        action_factory("Ctrl++", lambda: self._image_label.adjust_zoom(1.25))
        action_factory("Ctrl+-", lambda: self._image_label.adjust_zoom(0.8))
        action_factory("Ctrl+0", self._image_label.reset_zoom)

    def on_item_loaded(self, item: ImageItem, project: Project) -> None:
        px = QPixmap(str(Path(item.file_path)))

        if px.isNull():
            QMessageBox.critical(
                self, "Error al cargar la imagen",
                f"No se pudo cargar la imagen\n{item.file_path}"
            )
            return
        self._image_label.set_pix_map(px)

        # Populate dimensions Lazily
        if not item.has_dimensions:
            item.width = px.width()
            item.height = px.height()
        if item.has_dimensions:
            self.dim_label.setText(f"{item.width} x {item.height} px")

    def _on_reset(self) -> None:
        self._image_label.clear()
        self.dim_label.setText("--")
