import sys
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget


VIDEO_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov", ".wmv"}


class FolderVideoPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Folder Video Player")
        self.resize(900, 600)

        # --- Media Player ---
        self.media_player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.media_player.setAudioOutput(self.audio_output)

        self.video_widget = QVideoWidget(self)
        self.media_player.setVideoOutput(self.video_widget)

        # --- State ---
        self.video_files = []
        self.current_index = -1
        self._stop_listener_connected = False 

        # --- UI ---
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        main_layout.addWidget(self.video_widget)

        self.video_label = QLabel("No video loaded")
        self.video_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.video_label)

        controls_layout = QHBoxLayout()

        self.open_button = QPushButton("Open Video")
        self.prev_button = QPushButton("⏮ Previous")
        self.play_button = QPushButton("▶ Play")
        self.next_button = QPushButton("Next ⏭")

        controls_layout.addWidget(self.open_button)
        controls_layout.addWidget(self.prev_button)
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.next_button)

        main_layout.addLayout(controls_layout)

        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.play_button.setEnabled(False)

    def _connect_signals(self):
        self.open_button.clicked.connect(self.open_video)
        self.prev_button.clicked.connect(self.play_previous)
        self.next_button.clicked.connect(self.play_next)
        self.play_button.clicked.connect(self.toggle_play)

        self.media_player.playbackStateChanged.connect(self._update_play_button)

    # -------------------------------------------------------
    # Core Logic
    # -------------------------------------------------------

    def open_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video",
            "",
            "Videos (*.mp4 *.avi *.mkv *.mov *.wmv)"
        )

        if not file_path:
            return

        path = Path(file_path)
        self._load_folder_videos(path)
        self._play_video_by_index(self.current_index)

    def _load_folder_videos(self, selected_path: Path):
        folder = selected_path.parent

        self.video_files = sorted(
            [f for f in folder.iterdir()
             if f.suffix.lower() in VIDEO_EXTENSIONS]
        )

        if not self.video_files:
            QMessageBox.warning(self, "Error", "No videos found in folder.")
            return

        self.current_index = self.video_files.index(selected_path)

        self.prev_button.setEnabled(True)
        self.next_button.setEnabled(True)
        self.play_button.setEnabled(True)
        
    def _play_video_by_index(self, index: int):
        if 0 <= index < len(self.video_files):
            self.current_index = index
            self._pending_video_path = self.video_files[index]

            if self._stop_listener_connected:
                self.media_player.playbackStateChanged.disconnect(self._on_stopped_for_load)
                self._stop_listener_connected = False

            if self.media_player.playbackState() == QMediaPlayer.PlayingState:
                self.media_player.playbackStateChanged.connect(self._on_stopped_for_load)
                self._stop_listener_connected = True
                self.media_player.stop()
            else:
                self.media_player.stop()
                QTimer.singleShot(150, lambda: self._load_new_video(self._pending_video_path))

    def _on_stopped_for_load(self, state):
        if state == QMediaPlayer.StoppedState:
            if self._stop_listener_connected:
                self.media_player.playbackStateChanged.disconnect(self._on_stopped_for_load)
                self._stop_listener_connected = False
            QTimer.singleShot(150, lambda: self._load_new_video(self._pending_video_path))

    def _load_new_video(self, video_path):
        self.media_player.setSource(QUrl())          # clear first
        self.media_player.setSource(QUrl.fromLocalFile(str(video_path)))
        self.media_player.pause()
        self.video_label.setText(video_path.name)

    def play_next(self):
        if self.current_index < len(self.video_files) - 1:
            self._play_video_by_index(self.current_index + 1)

    def play_previous(self):
        if self.current_index > 0:
            self._play_video_by_index(self.current_index - 1)

    def toggle_play(self):
        if self.media_player.playbackState() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def _update_play_button(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_button.setText("⏸ Pause")
        else:
            self.play_button.setText("▶ Play")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FolderVideoPlayer()
    window.show()
    sys.exit(app.exec())