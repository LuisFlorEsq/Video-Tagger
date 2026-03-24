from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QSlider, QLabel, QStyle
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import Qt, Signal, QUrl, QTimer

from src.core.video_loader import VideoLoadManager


class VideoPlayer(QWidget):
    """Custom video player widget with frame-by-frame controls."""

    position_changed = Signal(int)
    duration_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.video_path = None
        self.fps = 30.0
        self.total_frames = 0

        self._pending_video_path = None
        self._stop_listener_connected = False
        self._media_ready_connected = False   # tracks if _on_media_status_changed is connected

        self._init_player()
        self._init_ui()
        self._connect_signals()

        self.video_loader = VideoLoadManager()
        self.video_loader.on_loaded_callback = self._on_metadata_loaded
        self.video_loader.on_failed_callback = self._on_video_load_failed

        # Called after media is ready and first frame is visible — safe to seek
        self.on_ready_callback = None

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
        self.media_player.positionChanged.connect(self._on_position_changed)
        self.media_player.durationChanged.connect(self._on_duration_changed)
        self.media_player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.play_button.clicked.connect(self.toggle_playback)
        self.timeline_slider.sliderMoved.connect(self.seek_position)

    # ------------------------------------------------------------------
    # Video loading
    # ------------------------------------------------------------------

    def load_video(self, video_path: str) -> bool:
        path = Path(video_path)
        if not path.exists():
            return False

        self.video_path = video_path
        self._pending_video_path = video_path

        # Disconnect any leftover stop listener
        self._disconnect_stop_listener()

        # Disconnect any leftover media-ready listener
        self._disconnect_media_ready()

        state = self.media_player.playbackState()
        has_source = self.media_player.source().isValid()

        if state == QMediaPlayer.PlayingState:
            # Must wait for full stop before touching the source on Windows
            self._connect_stop_listener()
            self.media_player.stop()
        elif state == QMediaPlayer.PausedState or (state == QMediaPlayer.StoppedState and has_source):
            # Has a previous source loaded — clear it then load new one after settling
            QTimer.singleShot(150, lambda: self._load_new_video(self._pending_video_path))
        else:
            # Truly empty player (first load) — go straight to loading, no clear needed
            self._load_new_video(video_path)

        return True

    def _on_stopped_for_load(self, state):
        """One-shot: fires when player reaches StoppedState after stop() was called."""
        if state == QMediaPlayer.StoppedState:
            self._disconnect_stop_listener()
            QTimer.singleShot(150, lambda: self._load_new_video(self._pending_video_path))

    def _load_new_video(self, video_path: str):
        """Clear old source (if any) then read metadata in background thread."""
        if video_path != self._pending_video_path:
            return  # A newer request superseded this one

        # Only clear the source if there actually is one — avoids confusing
        # the Windows backend by calling setSource(QUrl()) on an empty player
        if self.media_player.source().isValid():
            self.media_player.setSource(QUrl())

        self.video_loader.load_video_async(video_path)

    def _on_metadata_loaded(self, video_path: str, fps: float, total_frames: int):
        """Metadata thread finished — set source then wait for LoadedMedia."""
        if video_path != self._pending_video_path:
            return  # Stale result

        self.fps = fps
        self.total_frames = total_frames

        self._connect_media_ready()
        self.media_player.setSource(QUrl.fromLocalFile(str(Path(video_path).absolute())))

    def _on_media_status_changed(self, status):
        """
        Wait for LoadedMedia, then briefly play()->pause() to:
          - force the Windows pipeline to fully initialize
          - trigger durationChanged reliably (pause() alone is not enough on Windows)
          - render the first frame (no black screen)
        """
        if status == QMediaPlayer.LoadedMedia:
            self._disconnect_media_ready()

            # play() then immediately pause() forces the demuxer to run on Windows,
            # which is what reliably triggers durationChanged and renders the first frame.
            self.media_player.play()
            self.media_player.pause()
            self.media_player.setPosition(0)
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

            if self.on_ready_callback:
                self.on_ready_callback()

    # ------------------------------------------------------------------
    # Signal connection helpers — use flags to avoid double-connect/
    # disconnect-when-not-connected RuntimeWarnings
    # ------------------------------------------------------------------

    def _connect_stop_listener(self):
        if not self._stop_listener_connected:
            self.media_player.playbackStateChanged.connect(self._on_stopped_for_load)
            self._stop_listener_connected = True

    def _disconnect_stop_listener(self):
        if self._stop_listener_connected:
            try:
                self.media_player.playbackStateChanged.disconnect(self._on_stopped_for_load)
            except RuntimeError:
                pass
            self._stop_listener_connected = False

    def _connect_media_ready(self):
        if not self._media_ready_connected:
            self.media_player.mediaStatusChanged.connect(self._on_media_status_changed)
            self._media_ready_connected = True

    def _disconnect_media_ready(self):
        if self._media_ready_connected:
            try:
                self.media_player.mediaStatusChanged.disconnect(self._on_media_status_changed)
            except RuntimeError:
                pass
            self._media_ready_connected = False

    # ------------------------------------------------------------------
    # Loader failure
    # ------------------------------------------------------------------

    def _on_video_load_failed(self, video_path: str, error_message: str):
        print(f"Failed to load video {video_path}: {error_message}")
        self.fps = 30.0
        self.total_frames = 0

    # ------------------------------------------------------------------
    # Playback controls
    # ------------------------------------------------------------------

    def _on_playback_state_changed(self, state):
        """Reset play button and seek to start when video finishes playing naturally."""
        if state == QMediaPlayer.StoppedState:
            if not self._stop_listener_connected:
                self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
                self.media_player.setPosition(0)

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

    @staticmethod
    def _format_time(ms: int) -> str:
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def get_current_position_ms(self) -> int:
        return self.media_player.position()

    def is_playing(self) -> bool:
        return self.media_player.playbackState() == QMediaPlayer.PlayingState

    def force_stop(self):
        """
        Called when navigating away. Uses pause() not stop() to avoid
        the Windows multimedia pipeline teardown that causes freezes.
        """
        self._disconnect_stop_listener()
        self._disconnect_media_ready()
        self._pending_video_path = None

        if self.media_player.playbackState() != QMediaPlayer.StoppedState:
            self.media_player.pause()

        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))