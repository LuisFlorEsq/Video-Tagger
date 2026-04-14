from pathlib import Path
from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSlider,
    QStyle
)
from src.ui.styles import AppTheme, btn_primary


class AudioPlayerWidget(QWidget):
    """Self-contained audio playback controls."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._player = QMediaPlayer()
        self._audio = QAudioOutput()
        self._player.setAudioOutput(self._audio)
        self._status_connected = False

        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # -------------------------------------
        # Metadata
        # -------------------------------------

        self._waveform = QLabel("Musica")
        self._waveform.setAlignment(Qt.AlignCenter)
        self._waveform.setStyleSheet(
            f"font-size: 64px; color: {AppTheme.BORDER}; "
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
        self._play_btn.clicked.connect(self.toggle_playback)

        self._slider.sliderReleased.connect(
            lambda: self._player.setPosition(self._slider.value())
        )

    def load(self, file_path: str, filename: str) -> None:
        path = Path(file_path)
        if not path.exists():
            self.stop()
            self._filename_lbl.setText(filename)
            return

        self.stop()

        if self._status_connected:
            try:
                self._player.mediaStatusChanged.disconnect(self._on_status)
            except RuntimeError:
                pass
            self._status_connected = False

        self._filename_lbl.setText(filename)
        self._player.mediaStatusChanged.connect(self._on_status)
        self._status_connected = True

        self._player.setSource(QUrl.fromLocalFile(str(path.absolute())))
        self._play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self._slider.setRange(0, 0)
        self._slider.setValue(0)
        self._time_label.setText("00:00 / 00:00")

    def _on_status(self, status) -> None:
        if status in (
            QMediaPlayer.LoadedMedia, QMediaPlayer.InvalidMedia, QMediaPlayer.NoMedia
        ):
            if self._status_connected:
                try:
                    self._player.mediaStatusChanged.disconnect(self._on_status)
                except RuntimeError:
                    pass
                self._status_connected = False

    def toggle_playback(self) -> None:
        if self._player.playbackState() == QMediaPlayer.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def stop(self) -> None:
        self._player.stop()
        self._player.setPosition(0)
        self._play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self._slider.blockSignals(True)
        self._slider.setValue(0)
        self._slider.blockSignals(False)
        self._time_label.setText(
            f"{self.fmt(0)} / {self.fmt(self._player.duration())}"
        )

    def _on_position(self, pos: int) -> None:
        if not self._slider.isSliderDown():
            self._slider.blockSignals(True)
            self._slider.setValue(pos)
            self._slider.blockSignals(False)

            self._time_label.setText(
                f"{self.fmt(pos)} / {self.fmt(self._player.duration())}"
            )

    def _on_duration(self, dur: int) -> None:
        self._slider.setRange(0, dur)

    def _on_state(self, state) -> None:
        playing = state == QMediaPlayer.PlayingState
        self._play_btn.setIcon(
            self.style().standardIcon(
                QStyle.SP_MediaPause if playing else QStyle.SP_MediaPlay
            )
        )

    @staticmethod
    def fmt(ms: int) -> str:
        s = ms // 1000
        return f"{s // 60:02d}:{s % 60:02d}"
