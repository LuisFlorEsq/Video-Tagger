from pathlib import Path
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from src.ui.styles import AppTheme

from src.core.logger import logger
from src.domain.models.media.video_item import VideoItem
from src.domain.models.project import Project

from src.ui.widgets.media_viewer.video._video_player import VideoPlayer
from src.ui.widgets.media_viewer._base_viewer import BaseViewer


class VideoViewer(BaseViewer):
    """Video clip viewer"""

    def item_type_label(self) -> str:
        return "video"

    # --- Hooks ----
    def build_media_area(self) -> QWidget:
        area = QWidget()
        area.setStyleSheet(f"background-color: {AppTheme.BG_APP};")

        layout = QVBoxLayout(area)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.video_player = VideoPlayer()
        layout.addWidget(self.video_player, stretch=1)

        return area

    def build_info_rows(self, info_layout: QVBoxLayout) -> None:
        self.duration_label = self._info_row("DURACIÓN", "—", info_layout)

    def _setup_extra_shortcuts(self, action_factory) -> None:
        action_factory("Space", self.video_player.toggle_playback)

    def _handle_extra_key(self, key: int) -> bool:
        if key == Qt.Key_Space:
            self.video_player.toggle_playback()
            return True
        return False

    def _on_before_back(self) -> None:
        self.video_player.force_stop()

    def on_item_loaded(self, item: VideoItem, project: Project) -> None:
        if not Path(item.file_path).exists():
            QMessageBox.critical(
                self, "Archivo no encontrado",
                f"No se encontró el archivo de video:\n{item.file_path}"
            )
            return
        self.video_player.load_video(item.file_path)
        mins = int(item.duration) // 60
        secs = int(item.duration) % 60

        self.duration_label.setText(f"{mins:02d}:{secs:02d}")

    def on_reset(self) -> None:
        # logger.debug("VideoViewer.on_reset")
        self.video_player.force_stop()
        self.duration_label.setText("-")

    def stop(self) -> None:
        self.video_player.force_stop()

    stop_video = stop

    # Connect Video Player signals

    def _connect_base_signals(self) -> None:
        super()._connect_base_signals()
        # Signals only present on FragmentViewer
        self.video_player.ready.connect(self._on_video_ready)
        self.video_player.load_failed.connect(
            lambda msg: QMessageBox.critical(
                self, "Error al cargar el video", msg)
        )

    def _on_video_ready(self) -> None:
        if self._current_item:
            pos = int(self._current_item.start_time * 1000)
            QTimer.singleShot(50, lambda: self.video_player.seek_position(pos))
