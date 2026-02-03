from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QSlider, QLabel, QStyle
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import Qt, Signal, QUrl

from src.core.video_loader import VideoLoadManager

class VideoPlayer(QWidget):
    """Custom video player widget with frame-by-frame controls."""
    
    # Signals
    position_changed = Signal(int)  # Emits current position in ms
    duration_changed = Signal(int)  # Emits total duration in ms
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.video_path = None
        self.fps = 30.0  # Default FPS, will be updated when video loads
        self.total_frames = 0
        self._has_hard_stopped = False

        
        self._init_player()
        self._init_ui()
        self._connect_signals()
        
        # Initialize threaded video loader
        self.video_loader = VideoLoadManager(self.media_player)
        self.video_loader.on_loaded_callback = self._on_video_loaded_async
        self.video_loader.on_failed_callback = self._on_video_load_failed
    
    def _init_player(self):
        """Initialize media player components."""
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)
    
    def _init_ui(self):
        """Create the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Video display area
        self.video_widget.setMinimumSize(640, 480)
        self.video_widget.setStyleSheet("background-color: black;")
        layout.addWidget(self.video_widget, 1)  # Stretch factor 1
        
        # Timeline slider
        timeline_layout = QHBoxLayout()
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setMinimumWidth(120)
        timeline_layout.addWidget(self.time_label)
        
        self.timeline_slider = QSlider(Qt.Horizontal)
        self.timeline_slider.setRange(0, 0)
        timeline_layout.addWidget(self.timeline_slider)
        
        layout.addLayout(timeline_layout)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        
        # Playback controls
        self.play_button = QPushButton()
        self.play_button.setIcon(
            self.style().standardIcon(QStyle.SP_MediaPlay)
        )
        controls_layout.addWidget(self.play_button)
        
        self.stop_button = QPushButton()
        self.stop_button.setIcon(
            self.style().standardIcon(QStyle.SP_MediaStop)
        )
        controls_layout.addWidget(self.stop_button)
        
        controls_layout.addSpacing(20)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
    
    def _connect_signals(self):
        """Connect signals and slots."""
        # Media player signals
        self.media_player.positionChanged.connect(self._on_position_changed)
        self.media_player.durationChanged.connect(self._on_duration_changed)
        
        # Control button signals
        self.play_button.clicked.connect(self.toggle_playback)
        self.stop_button.clicked.connect(self.stop)
        
        # Timeline slider
        self.timeline_slider.sliderMoved.connect(self.seek_position)
        
        
    def load_video(self, video_path: str) -> bool:
        """Load a video file asynchronously using thread."""
        path = Path(video_path)
        if not path.exists():
            return False
        
        self.video_path = video_path
        
        # Load video asynchronously
        self.video_loader.load_video_async(video_path)
        
        return True
    
    def _on_video_loaded_async(self, video_path: str, fps: float, total_frames: int):
        """Callback when video is loaded in thread (runs in main thread)."""
        self.fps = fps
        self.total_frames = total_frames
        print(f"Video loaded: {video_path}, FPS: {fps}, Frames: {total_frames}")
    
    def _on_video_load_failed(self, video_path: str, error_message: str):
        """Callback when video loading fails."""
        print(f"Failed to load video {video_path}: {error_message}")
        self.fps = 30.0
        self.total_frames = 0  
    
    def toggle_playback(self):
        """Toggle between play and pause."""
        if self.media_player.playbackState() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.play_button.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPlay)
            )
        else:
            self.media_player.play()
            self.play_button.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPause)
            )
    
    def stop(self):
        """Stop playback."""
        self.media_player.stop()
        self.play_button.setIcon(
            self.style().standardIcon(QStyle.SP_MediaPlay)
        )
    
    def seek_position(self, position: int):
        """Seek to a specific position in ms."""
        self.media_player.setPosition(position)
    
    def _on_position_changed(self, position: int):
        """Handle position changes."""
        self.timeline_slider.blockSignals(True)
        self.timeline_slider.setValue(position)
        self.timeline_slider.blockSignals(False)
        
        # Update time label
        current_time = self._format_time(position)
        total_time = self._format_time(self.media_player.duration())
        self.time_label.setText(f"{current_time} / {total_time}")
        
        # Emit signals
        self.position_changed.emit(position)
    
    def _on_duration_changed(self, duration: int):
        """Handle duration changes."""
        self.timeline_slider.setRange(0, duration)
        self.duration_changed.emit(duration)
        
    def _on_media_error(self, error, error_string):
        print(f"Media error: {error} - {error_string}")
    
    @staticmethod
    def _format_time(ms: int) -> str:
        """Format milliseconds to MM:SS."""
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def get_current_position_ms(self) -> int:
        """Get current position in milliseconds."""
        return self.media_player.position()
    
    def is_playing(self) -> bool:
        """Check if video is currently playing."""
        return self.media_player.playbackState() == QMediaPlayer.PlayingState


    def force_stop(self):
        self.media_player.stop()
        self.media_player.setSource(QUrl())
        self.play_button.setIcon(
            self.style().standardIcon(QStyle.SP_MediaPlay)
        )
