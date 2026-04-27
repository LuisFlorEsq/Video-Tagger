from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)

from src.ui.styles import AppTheme, btn_ghost
from src.ui.helpers.dividers import make_vline

from src.domain.models.media.signal_item import SignalItem
from src.domain.models.project import Project
from src.infrastructure.array_media import load_signal_array

from src.ui.widgets.media_viewer._base_viewer import BaseViewer
from src.ui.widgets.media_viewer.signal._signal_plot import SignalPlotWidget

from src.core.config import ICON_SIZE
from src.core.resources import icon


class SignalViewer(BaseViewer):
    """Numeric signal viewer with simple zoomable trace plotting."""

    def item_type_label(self) -> str:
        return "señal"

    # --- Hooks ----
    def build_media_area(self) -> QWidget:
        root = QWidget()
        root.setStyleSheet(f"background-color: {AppTheme.BG_APP};")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        self._plot = SignalPlotWidget()

        toolbar = QHBoxLayout()
        toolbar.addStretch()

        for name, factor, tip in [
            ("zoom_out", 0.8, "Reducir zoom"),
            ("reset", None, "Restablecer zoom"),
            ("zoom_in", 1.25, "Ampliar zoom"),
        ]:
            btn = QPushButton("")
            btn.setFixedSize(36, 36)
            btn.setStyleSheet(btn_ghost())
            btn.setToolTip(tip)
            btn.setIcon(icon(f"zoom_controls/{name}.png"))
            btn.setIconSize(QSize(*ICON_SIZE))

            if factor is None:
                btn.clicked.connect(self._plot.reset_zoom)
            else:
                btn.clicked.connect(lambda _=False, f=factor: self._plot.adjust_zoom(f))
            toolbar.addWidget(btn)

        layout.addLayout(toolbar)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(False)
        self._scroll.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self._scroll.setStyleSheet(
            f"QScrollArea {{ background-color: {AppTheme.BG_APP}; border: none; }}"
        )
        self._scroll.setWidget(self._plot)
        layout.addWidget(self._scroll, stretch=1)

        return root

    def build_info_rows(self, info_layout: QVBoxLayout) -> None:
        self._shape_label = self._info_row("FORMA", "--", info_layout)
        self._dtype_label = self._info_row("TIPO", "--", info_layout)
        self._channels_label = self._info_row("CANALES", "--", info_layout)
        self._duration_label = self._info_row("DURACION", "--:--", info_layout)

    def _populate_topbar_extras(self, tb: QHBoxLayout) -> None:
        tb.addWidget(make_vline())
        tb.addSpacing(8)

    def _setup_extra_shortcuts(self, action_factory) -> None:
        action_factory("Ctrl++", lambda: self._plot.adjust_zoom(1.25))
        action_factory("Ctrl+-", lambda: self._plot.adjust_zoom(0.8))
        action_factory("Ctrl+0", self._plot.reset_zoom)

    def on_item_loaded(self, item: SignalItem, project: Project) -> None:
        if not Path(item.file_path).exists():
            QMessageBox.critical(
                self,
                "Archivo no encontrado",
                f"No se encontro la señal:\n{item.file_path}",
            )
            return

        try:
            signal, metadata = load_signal_array(item.file_path)
        except Exception as exc:
            QMessageBox.critical(self, "Error al cargar señal", str(exc))
            return

        # Populate item metadata
        item.shape = metadata.get("shape")
        item.dtype = metadata.get("dtype")
        item.channels = metadata.get("channels")
        item.sample_rate = metadata.get("sample_rate")
        item.duration_s = metadata.get("duration_s")
        item.source_key = metadata.get("source_key")

        self._plot.set_signal_data(signal, sample_rate=item.sample_rate)

        self._shape_label.setText(" x ".join(str(v) for v in item.shape or []))
        self._dtype_label.setText(item.dtype or "--")
        self._channels_label.setText(str(item.channels or "--"))
        self._duration_label.setText(item.duration_label)

    def on_reset(self) -> None:
        self._plot.clear_plot()
        self._shape_label.setText("--")
        self._dtype_label.setText("--")
        self._channels_label.setText("--")
        self._duration_label.setText("--:--")

    def stop(self) -> None:
        self.on_reset()
