from pathlib import Path

from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSlider,
    QStyle,
)

from src.core.logger import logger
from src.core.resources import image
from src.ui.styles import AppTheme, btn_primary


class AudioPlayerWidget(QWidget):
    """
    Self-contained audio playback controls.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._player = QMediaPlayer(self)
        self._audio = QAudioOutput(self)
        self._player.setAudioOutput(self._audio)

        self._load_token = 0
        self._media_ready_connected = False

        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # -------------------------------------
        # Metadata
        # -------------------------------------

        self._waveform = QLabel()
        self._waveform.setAlignment(Qt.AlignCenter)
        waveform_pixmap = image("zoom_controls/music_notes.png")

        # Scale the pixmap to fit well inside the widget (adjust dimensions as needed)
        if not waveform_pixmap.isNull():
            scaled_pixmap = waveform_pixmap.scaled(
                400, 200,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self._waveform.setPixmap(scaled_pixmap)
        else:
            logger.warning("Waveform image could not be loaded.")

        self._waveform.setStyleSheet(
            f"background-color: {AppTheme.BG_SUBTLE}; border-radius: 12px;"
        )
        self._waveform.setMinimumHeight(180)
        layout.addWidget(self._waveform, stretch=1)

        self._filename_lbl = QLabel("")
        self._filename_lbl.setAlignment(Qt.AlignCenter)
        self._filename_lbl.setStyleSheet(
            f"font-size: {AppTheme.FONT_BASE}; font-weight: bold; "
            f"color: {AppTheme.TEXT_PRIMARY};"
        )
        layout.addWidget(self._filename_lbl)

        # -------------------------------------
        # Timeline and slider
        # -------------------------------------

        timeline = QHBoxLayout()
        self._time_label = QLabel("00:00 / 00:00")
        self._time_label.setStyleSheet(
            f"font-size: {AppTheme.FONT_SM}; color: {AppTheme.TEXT_SECONDARY};"
        )
        self._time_label.setMinimumWidth(100)
        timeline.addWidget(self._time_label)

        self._slider = QSlider(Qt.Horizontal)
        self._slider.setRange(0, 0)
        timeline.addWidget(self._slider)
        layout.addLayout(timeline)

        # -------------------------------------
        # Controls (Play/Pause)
        # -------------------------------------

        controls = QHBoxLayout()
        controls.addStretch()

        self._play_btn = QPushButton()
        self._play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self._play_btn.setFixedSize(40, 40)
        self._play_btn.setStyleSheet(btn_primary())

        controls.addWidget(self._play_btn)
        controls.addStretch()
        layout.addLayout(controls)

    def _connect_signals(self) -> None:

        self._player.positionChanged.connect(self._on_position)
        self._player.durationChanged.connect(self._on_duration)

        self._player.playbackStateChanged.connect(self._on_state)
        self._player.errorOccurred.connect(self._on_error)

        self._play_btn.clicked.connect(self.toggle_playback)
        self._slider.sliderReleased.connect(self._on_slider_released)

    def load(self, file_path: str, filename: str) -> None:
        path = Path(file_path)

        self._load_token += 1
        # current_token = self._load_token

        # logger.debug(
        #     "AudioPlayerWidget.load | token=%s | file=%s",
        #     current_token, path
        # )

        if not path.exists():
            # logger.warning(
            #     "AudioPlayerWidget.load missing file | token=%s | path=%s",
            #     current_token, path
            # )
            self._reset_ui()
            self._filename_lbl.setText(filename)
            return

        if self._media_ready_connected:
            try:
                self._player.mediaStatusChanged.disconnect(
                    self._on_media_status_changed
                )
            except RuntimeError:
                pass
            self._media_ready_connected = False

        self._reset_ui()
        self._filename_lbl.setText(filename)

        self._player.mediaStatusChanged.connect(self._on_media_status_changed)
        self._media_ready_connected = True
        self._player.setSource(QUrl.fromLocalFile(str(path.absolute())))

        # logger.debug(
        #     "AudioPlayerWidget.load source set | token=%s", current_token
        # )

    def _on_media_status_changed(self, status) -> None:

        if status != QMediaPlayer.LoadedMedia:
            return

        if self._media_ready_connected:
            try:
                self._player.mediaStatusChanged.disconnect(
                    self._on_media_status_changed
                )
            except RuntimeError:
                pass
            self._media_ready_connected = False

        token = self._load_token

        # logger.debug(
        #     "AudioPlayerWidget._on_media_status_changed LoadedMedia | token=%s",
        #     token
        # )

        self._player.play()
        self._player.pause()
        self._player.setPosition(0)

        self._play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        QTimer.singleShot(0, lambda: self._finalize_load(token))

    def _finalize_load(self, token: int) -> None:
        if token != self._load_token:
            # logger.debug(
            #     "AudioPlayerWidget._finalize_load stale token | token=%s | current=%s",
            #     token, self._load_token
            # )
            return

        # logger.debug(
        #     "AudioPlayerWidget._finalize_load ready | token=%s", token
        # )

    # -------------------------------------
    # Playback controls
    # -------------------------------------

    def toggle_playback(self) -> None:
        if self._player.playbackState() == QMediaPlayer.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def stop(self) -> None:
        self._load_token += 1

        # logger.debug(
        #     "AudioPlayerWidget.stop | token=%s | state=%s | has_source=%s",
        #     self._load_token,
        #     self._player.playbackState(),
        #     self._player.source().isValid(),
        # )

        # Disconnect any pending status listener
        if self._media_ready_connected:
            try:
                self._player.mediaStatusChanged.disconnect(
                    self._on_media_status_changed
                )
            except RuntimeError:
                pass
            self._media_ready_connected = False

        self._player.pause()
        self._player.stop()
        self._player.setPosition(0)
        self._player.setSource(QUrl())
        self._reset_ui()

    # -------------------------------------
    # UI helpers
    # -------------------------------------

    def _reset_ui(self) -> None:
        self._play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

        self._slider.blockSignals(True)
        self._slider.setRange(0, 0)
        self._slider.setValue(0)

        self._slider.blockSignals(False)
        self._time_label.setText("00:00 / 00:00")

    def _on_slider_released(self) -> None:
        self._player.setPosition(self._slider.value())

    def _on_position(self, pos: int) -> None:
        if not self._slider.isSliderDown():
            self._slider.blockSignals(True)
            self._slider.setValue(pos)
            self._slider.blockSignals(False)
        self._time_label.setText(
            f"{self.fmt(pos)} / {self.fmt(self._player.duration())}"
        )

    def _on_duration(self, dur: int) -> None:
        if dur > 0:
            # logger.debug("AudioPlayerWidget._on_duration | dur=%s", dur)
            self._slider.setRange(0, dur)

    def _on_state(self, state) -> None:
        playing = state == QMediaPlayer.PlayingState
        self._play_btn.setIcon(
            self.style().standardIcon(
                QStyle.SP_MediaPause if playing else QStyle.SP_MediaPlay
            )
        )

    def _on_error(self, error, error_string) -> None:
        logger.error(
            "AudioPlayerWidget._on_error | error=%s | message=%s",
            error, error_string
        )

    @staticmethod
    def fmt(ms: int) -> str:
        s = ms // 1000
        return f"{s // 60:02d}:{s % 60:02d}"
