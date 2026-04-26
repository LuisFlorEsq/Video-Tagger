import os
from pathlib import Path
from typing import List

from src.domain.interfaces import IMediaScanner
from src.domain.models.media import (
    MediaItem, MediaType
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

    EXTENSIONS: frozenset[str] = frozenset()

    def scan_folder(self, folder_path: Path) -> List[MediaItem]:
        paths = self.scan_paths(folder_path)
        items: List[MediaItem] = []
        for i, path in enumerate(paths, start=1):
            item_id = f"item_{i:03d}"
            items.append(self._make_item(item_id, path))
        return items

    def scan_paths(self, folder_path: Path) -> List[Path]:
        if not folder_path.exists() or not folder_path.is_dir():
            raise ValueError(f"Invalid folder path: {folder_path}")

        valid_exts = self.EXTENSIONS
        found: List[Path] = []

        with os.scandir(folder_path) as entries:
            for entry in entries:
                if not entry.is_file():
                    continue
                if Path(entry.name).suffix.lower() in valid_exts:
                    found.append(Path(entry.path))

        return sorted(found)

    def get_supported_extensions(self) -> List[str]:
        return list(self.EXTENSIONS)

    def _make_item(self, item_id: str, path: Path) -> MediaItem:
        return MediaItem(
            item_id=item_id,
            file_path=str(path),
            media_type=self.media_type
        )

# ---------------------------------------------
# Video Scanner
# ---------------------------------------------


class VideoScanner(_BaseFileScanner):
    """Scans a folder for video files and returns VideoItem instances"""

    EXTENSIONS = frozenset(VIDEO_EXTENSIONS)

    @property
    def media_type(self) -> MediaType:
        return MediaType.VIDEO

# ---------------------------------------------
# Image Scanner
# ---------------------------------------------


class ImageScanner(_BaseFileScanner):
    """Scans a folder for image files and returns ImageItem instances."""

    EXTENSIONS = frozenset(IMAGE_EXTENSIONS.union(IMAGE_ARRAY_EXTENSIONS)) # Important operation over sets (union)

    @property
    def media_type(self) -> MediaType:
        return MediaType.IMAGE

# ---------------------------------------------
# Audio Scanner
# ---------------------------------------------


class AudioScanner(_BaseFileScanner):
    """Scans a folder for audio files and returns AudioItem instances"""

    EXTENSIONS = frozenset(AUDIO_EXTENSIONS)

    @property
    def media_type(self) -> MediaType:
        return MediaType.AUDIO

# ---------------------------------------------
# Text Scanner
# ---------------------------------------------


class TextScanner(_BaseFileScanner):
    """Scans a folder for plain-text files and returns TextItem instances"""

    EXTENSIONS = frozenset(TEXT_EXTENSIONS)

    @property
    def media_type(self) -> MediaType:
        return MediaType.TEXT


# ---------------------------------------------
# Signal Scanner
# ---------------------------------------------


class SignalScanner(_BaseFileScanner):
    """Scans a folder for numeric signal files and returns SignalItem instances."""

    EXTENSIONS = frozenset(SIGNAL_EXTENSIONS)

    @property
    def media_type(self) -> MediaType:
        return MediaType.SIGNAL
