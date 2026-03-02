from pathlib import Path
from PySide6.QtCore import QThread, Signal
import cv2


class VideoLoaderThread(QThread):
    """
    Reads video metadata (fps, frame count) in a background thread.
    Does NOT touch QMediaPlayer — that stays on the main thread in VideoPlayer.
    """
    video_loaded = Signal(str, float, int)
    loading_failed = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._video_path = None

    def load_video(self, video_path: str):
        self._video_path = video_path

        # On Windows, restarting a finished QThread without waiting causes freezes.
        if self.isRunning():
            self.quit()
            self.wait()

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
    """
    Manages the metadata loader thread.
    Media player source setting is handled externally by VideoPlayer.
    """
    def __init__(self):
        self.loader_thread = VideoLoaderThread()
        self.loader_thread.video_loaded.connect(self._on_video_loaded)
        self.loader_thread.loading_failed.connect(self._on_video_failed)

        self.on_loaded_callback = None
        self.on_failed_callback = None

        self._pending_path = None

    def load_video_async(self, video_path: str):
        self._pending_path = video_path
        self.loader_thread.load_video(video_path)

    def _on_video_loaded(self, video_path: str, fps: float, total_frames: int):
        if video_path != self._pending_path:
            return  # Stale result from a previous request, discard it
        if self.on_loaded_callback:
            self.on_loaded_callback(video_path, fps, total_frames)

    def _on_video_failed(self, video_path: str, error: str):
        if video_path != self._pending_path:
            return
        if self.on_failed_callback:
            self.on_failed_callback(video_path, error)