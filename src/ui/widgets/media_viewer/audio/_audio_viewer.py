from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from src.core.logger import logger
from src.domain.models.media.audio_item import AudioItem
from src.domain.models.project import Project
from src.ui.widgets.media_viewer._base_viewer import BaseViewer
from src.ui.widgets.media_viewer.audio._audio_utils import AudioPlayerWidget


class AudioViewer(BaseViewer):
    """Audio clip viewer with playback controls."""

    def item_type_label(self) -> str:
        return "audio"

    def build_media_area(self) -> QWidget:
        self._audio_player = AudioPlayerWidget()
        return self._audio_player

    def build_info_rows(self, info_layout: QVBoxLayout) -> None:
        self.dur_label = self._info_row("DURACIÓN", "—", info_layout)

    def _setup_extra_shortcuts(self, action_factory) -> None:
        action_factory("Space", self._audio_player.toggle_playback)

    def _handle_extra_key(self, key: int) -> bool:
        if key == Qt.Key_Space:
            self._audio_player.toggle_playback()
            return True
        return False

    def _on_before_back(self) -> None:
        logger.debug(
            "AudioViewer._on_before_back | item_id=%s",
            getattr(self._current_item, "item_id", None),
        )
        self._audio_player.stop()

    def on_item_loaded(self, item: AudioItem, project: Project) -> None:
        logger.debug(
            "AudioViewer.on_item_loaded | item_id=%s | filename=%s | path=%s",
            item.item_id,
            item.get_filename(),
            item.file_path,
        )
        if not Path(item.file_path).exists():
            logger.warning(
                "AudioViewer.on_item_loaded missing file | item_id=%s | path=%s",
                item.item_id,
                item.file_path,
            )
            QMessageBox.critical(
                self,
                "Archivo no encontrado",
                f"No se encontró el audio:\n{item.file_path}",
            )
            return

        try:
            self._audio_player.load(item.file_path, item.get_filename())
        except Exception:
            logger.exception(
                "AudioViewer.on_item_loaded failed during player load | item_id=%s | path=%s",
                item.item_id,
                item.file_path,
            )
            raise

        self.dur_label.setText(item.duration_label)

    def on_reset(self) -> None:
        # logger.debug("AudioViewer.on_reset")
        self._audio_player.stop()
        self.dur_label.setText("—")

    def stop(self) -> None:
        # logger.debug(
        #     "AudioViewer.stop | item_id=%s",
        #     getattr(self._current_item, "item_id", None),
        # )
        self._audio_player.stop()
