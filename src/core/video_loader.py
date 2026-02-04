from pathlib import Path
from PySide6.QtCore import QThread, Signal, QUrl, QMutex, QMutexLocker
from PySide6.QtMultimedia import QMediaPlayer
import cv2


class VideoLoaderThread(QThread):
    video_loaded = Signal(str, float, int)
    loading_failed = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._video_path = None

    def load_video(self, video_path: str):
        self._video_path = video_path
        if not self.isRunning():
            self.start()

    def run(self):
        try:
            path = Path(self._video_path)
            if not path.exists():
                self.loading_failed.emit(self._video_path, "Archivo no encontrado")
                return

            cap = cv2.VideoCapture(str(path))
            if not cap.isOpened():
                self.loading_failed.emit(self._video_path, "No se puede abrir el video")
                return

            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()

            self.video_loaded.emit(self._video_path, fps, total_frames)

        except Exception as e:
            self.loading_failed.emit(self._video_path, str(e))

class VideoLoadManager:
    def __init__(self, media_player: QMediaPlayer):
        self.media_player = media_player
        self.loader_thread = VideoLoaderThread()

        self.loader_thread.video_loaded.connect(self._on_video_loaded)
        self.loader_thread.loading_failed.connect(self._on_video_failed)

        self.on_loaded_callback = None
        self.on_failed_callback = None

    def load_video_async(self, video_path: str):
        # MAIN THREAD cleanup
        self.media_player.stop()
        self.media_player.setSource(QUrl())

        # Start metadata loading
        self.loader_thread.load_video(video_path)

    def _on_video_loaded(self, video_path: str, fps: float, total_frames: int):
        # MAIN THREAD media loading
        self.media_player.setSource(
            QUrl.fromLocalFile(str(Path(video_path).absolute()))
        )

        if self.on_loaded_callback:
            self.on_loaded_callback(video_path, fps, total_frames)

    def _on_video_failed(self, video_path: str, error: str):
        if self.on_failed_callback:
            self.on_failed_callback(video_path, error)
