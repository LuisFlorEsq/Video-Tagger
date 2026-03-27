from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QSlider, QLabel, QStyle
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import Qt, Signal, QUrl


class VideoPlayer(QWidget):
    """Custom video player widget with basic controls."""

    position_changed = Signal(int)
    duration_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.video_path = None

        self.on_ready_callback = None
        self._media_ready_connected = False

        self._init_player()
        self._init_ui()
        self._connect_signals()

    def _init_player(self):
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)

        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.video_widget.setMinimumSize(640, 480)
        self.video_widget.setStyleSheet("background-color: black;")
        layout.addWidget(self.video_widget, 1)

        timeline_layout = QHBoxLayout()
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setMinimumWidth(120)
        timeline_layout.addWidget(self.time_label)

        self.timeline_slider = QSlider(Qt.Horizontal)
        self.timeline_slider.setRange(0, 0)
        timeline_layout.addWidget(self.timeline_slider)
        layout.addLayout(timeline_layout)

        controls_layout = QHBoxLayout()
        self.play_button = QPushButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        controls_layout.addWidget(self.play_button)
        controls_layout.addSpacing(20)
        controls_layout.addStretch()
        layout.addLayout(controls_layout)

    def _connect_signals(self):
        # Media player metadata
        self.media_player.positionChanged.connect(self._on_position_changed)
        self.media_player.durationChanged.connect(self._on_duration_changed)
        self.media_player.playbackStateChanged.connect(self._on_playback_state_changed)

        # Play buttons and position tracker
        self.play_button.clicked.connect(self.toggle_playback)
        self.timeline_slider.sliderMoved.connect(self.seek_position)

    # ─────────────────────────────────────────────
    # Video loading
    # ─────────────────────────────────────────────

    def load_video(self, video_path: str) -> bool:
        path = Path(video_path)
        if not path.exists():
            return False

        self.video_path = video_path

        # Disconnect old media status listener if connected
        if self._media_ready_connected:
            try:
                self.media_player.mediaStatusChanged.disconnect(self._on_media_status_changed)
            except RuntimeError:
                pass
            self._media_ready_connected = False

        # Connect listener for new load
        self.media_player.mediaStatusChanged.connect(self._on_media_status_changed)
        self._media_ready_connected = True

        self.media_player.stop()
        self.media_player.setSource(QUrl.fromLocalFile(str(path.absolute())))

        return True

    def _on_media_status_changed(self, status):
        if status == QMediaPlayer.LoadedMedia:
            # disconnect (one-shot)
            if self._media_ready_connected:
                try:
                    self.media_player.mediaStatusChanged.disconnect(self._on_media_status_changed)
                except RuntimeError:
                    pass
                self._media_ready_connected = False

            # Render first frame
            self.media_player.play()
            self.media_player.pause()
            self.media_player.setPosition(0)

            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

            if self.on_ready_callback:
                self.on_ready_callback()

    # ─────────────────────────────────────────────
    # Playback controls
    # ─────────────────────────────────────────────

    def toggle_playback(self):
        if self.media_player.playbackState() != QMediaPlayer.PlayingState:
            self.media_player.play()
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.media_player.pause()
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def seek_position(self, position: int):
        self.media_player.setPosition(position)

    def _on_position_changed(self, position: int):
        self.timeline_slider.blockSignals(True)
        self.timeline_slider.setValue(position)
        self.timeline_slider.blockSignals(False)

        current_time = self._format_time(position)
        total_time = self._format_time(self.media_player.duration())
        self.time_label.setText(f"{current_time} / {total_time}")

        self.position_changed.emit(position)

    def _on_duration_changed(self, duration: int):
        self.timeline_slider.setRange(0, duration)
        self.duration_changed.emit(duration)

    def _on_playback_state_changed(self, state):
        if state == QMediaPlayer.StoppedState:
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.media_player.setPosition(0)

    @staticmethod
    def _format_time(ms: int) -> str:
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def force_stop(self):
        self.media_player.stop()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))