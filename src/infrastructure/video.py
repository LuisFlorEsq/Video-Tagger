from pathlib import Path

from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
 
from src.domain.interfaces import IVideoSource
from src.core.config import METADATA_TIMEOUT_MS


def _read_metadata(video_path: Path) -> tuple[float, float]:
    """Return (duration_seconds, fps) for *video_path*."""
    duration_s = 1.0
    fps        = 0.0
 
    player       = QMediaPlayer()
    audio_output = QAudioOutput()          # required even if we mute it
    player.setAudioOutput(audio_output)
    audio_output.setVolume(0)
 
    loop    = QEventLoop()
    timer   = QTimer()
    timer.setSingleShot(True)
 
    # Capture result into a mutable container so the lambda can write to it
    result: list = [duration_s, fps]
 
    def on_status_changed(status):
        if status == QMediaPlayer.LoadedMedia:
            dur_ms = player.duration()          # milliseconds
            if dur_ms > 0:
                result[0] = dur_ms / 1000.0
                
            timer.stop()
            loop.quit()
        elif status in (
            QMediaPlayer.InvalidMedia,
            QMediaPlayer.NoMedia,
        ):
            timer.stop()
            loop.quit()
 
    def on_error(error, error_string):
        timer.stop()
        loop.quit()
 
    player.mediaStatusChanged.connect(on_status_changed)
    player.errorOccurred.connect(on_error)
    timer.timeout.connect(loop.quit)
 
    player.setSource(QUrl.fromLocalFile(str(video_path.absolute())))
    timer.start(METADATA_TIMEOUT_MS)
    loop.exec()
 
    # Clean up — disconnect signals before the objects go out of scope
    player.mediaStatusChanged.disconnect(on_status_changed)
    player.errorOccurred.disconnect(on_error)
    player.stop()
 
    return result[0], result[1]
 
 
class QtVideoSource(IVideoSource):
    """PySide6-native video source."""
 
    def get_duration(self, video_path: Path) -> float:
        """Return video duration in seconds, or 1.0 on failure."""
        duration, _ = _read_metadata(video_path)
        return duration
 
    def get_fps(self, video_path: Path) -> float:
        """Return video FPS."""
        _, fps = _read_metadata(video_path)
        return fps
 
    def exists(self, video_path: Path) -> bool:
        """Return True if the file exists on disk."""
        return video_path.exists() and video_path.is_file()