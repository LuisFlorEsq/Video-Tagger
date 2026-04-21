from pathlib import Path
from typing import List

from src.domain.interfaces import IMediaScanner
from src.domain.models.media import (
    MediaItem, MediaType,
    ImageItem, AudioItem, SignalItem,
    VideoItem, TextItem
)

from src.core.config import (
    VIDEO_EXTENSIONS,
    IMAGE_EXTENSIONS,
    IMAGE_ARRAY_EXTENSIONS,
    AUDIO_EXTENSIONS,
    TEXT_EXTENSIONS,
    SIGNAL_EXTENSIONS,
)


class _BaseFileScanner(IMediaScanner):
    """Scan a folder for files matching a fixed extension list

    Subclasses implement:

        - EXTENSIONS class var
        - media_type property
        - _make_item() to convert a (id, Path) pair into a MediaItem
    """

    EXTENSIONS: List[str] = []

    def scan_folder(self, folder_path: Path) -> List[MediaItem]:
        if not folder_path.exists() or not folder_path.is_dir():
            raise ValueError(f"Invalid folder path: {folder_path}")

        found: List[Path] = []
        for ext in self.EXTENSIONS:
            found.extend(folder_path.glob(f"*{ext}"))
            found.extend(folder_path.glob(f"*{ext.upper()}"))

        sorted_paths = sorted(set(found))
        items: List[MediaItem] = []

        for i, path in enumerate(sorted_paths):
            item_id = f"item_{i + 1:03d}"
            items.append(self._make_item(item_id, path))

        return items

    def get_supported_extensions(self) -> List[str]:
        return self.EXTENSIONS.copy()

    def _make_item(self, item_id: str, path: Path) -> MediaItem:
        raise NotImplementedError

# ---------------------------------------------
# Video Scanner
# ---------------------------------------------


class VideoScanner(_BaseFileScanner):
    """Scans a folder for video files and returns VideoItem instances"""

    EXTENSIONS = VIDEO_EXTENSIONS

    @property
    def media_type(self) -> MediaType:
        return MediaType.VIDEO

    def _make_item(self, item_id: str, path: Path) -> VideoItem:
        return VideoItem(
            item_id=item_id,
            file_path=str(path)
        )

# ---------------------------------------------
# Image Scanner
# ---------------------------------------------


class ImageScanner(_BaseFileScanner):
    """Scans a folder for image files and returns ImageItem instances."""

    EXTENSIONS = IMAGE_EXTENSIONS + IMAGE_ARRAY_EXTENSIONS

    @property
    def media_type(self) -> MediaType:
        return MediaType.IMAGE

    def _make_item(self, item_id: str, path: Path) -> ImageItem:
        return ImageItem(
            item_id=item_id,
            file_path=str(path)
        )

# ---------------------------------------------
# Audio Scanner
# ---------------------------------------------


class AudioScanner(_BaseFileScanner):
    """Scans a folder for audio files and returns AudioItem instances"""

    EXTENSIONS = AUDIO_EXTENSIONS

    @property
    def media_type(self) -> MediaType:
        return MediaType.AUDIO

    def _make_item(self, item_id: str, path: Path) -> AudioItem:
        return AudioItem(
            item_id=item_id,
            file_path=str(path)
        )

# ---------------------------------------------
# Text Scanner
# ---------------------------------------------


class TextScanner(_BaseFileScanner):
    """Scans a folder for plain-text files and returns TextItem instances"""

    EXTENSIONS = TEXT_EXTENSIONS

    @property
    def media_type(self) -> MediaType:
        return MediaType.TEXT

    def _make_item(self, item_id: str, path: Path) -> TextItem:
        return TextItem(
            item_id=item_id,
            file_path=str(path)
        )

# ---------------------------------------------
# Signal Scanner
# ---------------------------------------------


class SignalScanner(_BaseFileScanner):
    """Scans a folder for numeric signal files and returns SignalItem instances."""

    EXTENSIONS = SIGNAL_EXTENSIONS

    @property
    def media_type(self) -> MediaType:
        return MediaType.SIGNAL

    def _make_item(self, item_id: str, path: Path) -> SignalItem:
        return SignalItem(
            item_id=item_id,
            file_path=str(path)
        )
