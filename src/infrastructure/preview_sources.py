from pathlib import Path
from typing import Optional

from PySide6.QtGui import QImageReader
from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

from src.domain.interfaces import IMediaPreviewSource
from src.domain.models.media.media_item import MediaType

from src.core.config import METADATA_TIMEOUT_MS
from src.infrastructure.array_media import (
    is_image_array,
    is_numpy_media_path,
    load_numpy_array,
    load_signal_array
)


# ---------------------------------------------
# Auxiliar methods
# ---------------------------------------------

def read_qt_media_duration(file_path: Path) -> Optional[float]:
    """Standalone utility function to extract exact duration using QMediaPlayer"""
    try:
        player = QMediaPlayer()
        audio_output = QAudioOutput()
        player.setAudioOutput(audio_output)
        audio_output.setVolume(0)

        loop = QEventLoop()
        timer = QTimer()
        timer.setSingleShot(True)
        result: list = [None]

        def on_status(status):
            if status == QMediaPlayer.LoadedMedia:
                dur_ms = player.duration()
                if dur_ms > 0:
                    result[0] = dur_ms / 1000.0
                timer.stop()
                loop.quit()
            elif status in (QMediaPlayer.InvalidMedia, QMediaPlayer.NoMedia):
                timer.stop()
                loop.quit()

        def on_error(*_):
            timer.stop()
            loop.quit()

        player.mediaStatusChanged.connect(on_status)
        player.errorOccurred.connect(on_error)
        timer.timeout.connect(loop.quit)

        player.setSource(QUrl.fromLocalFile(str(file_path.absolute())))
        timer.start(METADATA_TIMEOUT_MS)
        loop.exec()

        player.mediaStatusChanged.disconnect(on_status)
        player.errorOccurred.disconnect(on_error)
        player.stop()

        return result[0]

    except Exception:
        return None


# ---------------------------------------------
# VideoPreviewSource
# ---------------------------------------------

class VideoPreviewSource(IMediaPreviewSource):
    """Reads video duration using Qts MediaPlayer with an event loop"""

    @property
    def media_type(self):
        return MediaType.VIDEO

    def get_metadata(self, file_path: Path) -> dict:
        duration_s = read_qt_media_duration(file_path)
        return {"duration_s": duration_s}

    def file_exists(self, file_path: Path) -> bool:
        return file_path.exists() and file_path.is_file()

# ---------------------------------------------
# ImagePreviewSource
# ---------------------------------------------


class ImagePreviewSource(IMediaPreviewSource):
    """Reads image dimensions by using Qt QImageReader"""

    @property
    def media_type(self) -> MediaType:
        return MediaType.IMAGE

    def get_metadata(self, file_path: Path) -> dict:
        if is_numpy_media_path(file_path):
            array, source_key, _ = load_numpy_array(file_path)
            if not is_image_array(array):
                raise ValueError(
                    f"{file_path.name} does not contain an image-shaped NumPy array"
                )
            return {
                "width": int(array.shape[1]),
                "height": int(array.shape[0]),
                "source_key": source_key,
            }
        try:
            reader = QImageReader(str(file_path))
            size = reader.size()
            if size.isValid():
                return {"width": size.width(), "height": size.height()}
        except Exception:
            pass

        return {"width": 0, "height": 0}

    def file_exists(self, file_path: Path) -> bool:
        return file_path.exists() and file_path.is_file()


# ---------------------------------------------
# AudioPreviewSource
# ---------------------------------------------

class AudioPreviewSource(IMediaPreviewSource):
    """Reads audio duration using Qts QMediaPlayer with an event loop"""

    @property
    def media_type(self) -> MediaType:
        return MediaType.AUDIO

    def get_metadata(self, file_path: Path) -> dict:
        duration_s = read_qt_media_duration(file_path)
        return {"duration_s": duration_s, "sample_rate": None}

    def file_exists(self, file_path: Path) -> bool:
        return file_path.exists() and file_path.is_file()

# ---------------------------------------------
# TextPreviewSource
# ---------------------------------------------


class TextPreviewSource(IMediaPreviewSource):
    """Sniffs the encoding of a text file and reports its byte size"""

    BOM_MAP = {
        b"\xef\xbb\xbf":     "utf-8-sig",
        b"\xff\xfe\x00\x00": "utf-32-le",
        b"\x00\x00\xfe\xff": "utf-32-be",
        b"\xff\xfe":         "utf-16-le",
        b"\xfe\xff":         "utf-16-be",
    }

    @property
    def media_type(self) -> MediaType:
        return MediaType.TEXT

    def get_metadata(self, file_path: Path) -> dict:
        encoding = self._detect_encoding(file_path)
        size_bytes = file_path.stat().st_size if file_path.exists() else 0
        return {"encoding": encoding, "size_bytes": size_bytes}

    def file_exists(self, file_path: Path) -> bool:
        return file_path.exists() and file_path.is_file()

    def _detect_encoding(self, file_path: Path) -> str:
        try:
            raw = file_path.read_bytes()
            for bom, enc in self._BOM_MAP.items():
                if raw.startswith(bom):
                    return enc
            # Heuristic: try UTF-8 strict; fall back to latin-1
            try:
                raw.decode("utf-8")
                return "utf-8"
            except UnicodeDecodeError:
                return "latin-1"
        except Exception:
            return "utf-8"

# ---------------------------------------------
# SignalPreviewSource
# ---------------------------------------------


class SignalPreviewSource(IMediaPreviewSource):
    """Reads metadata for NumPy-backed numeric signals."""

    @property
    def media_type(self) -> MediaType:
        return MediaType.SIGNAL

    def get_metadata(self, file_path: Path) -> dict:
        _, metadata = load_signal_array(file_path)
        return metadata

    def file_exists(self, file_path: Path) -> bool:
        return file_path.exists() and file_path.is_file()
