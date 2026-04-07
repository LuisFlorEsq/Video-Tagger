from pathlib import Path
from typing import List

from src.domain.interfaces import IFragmentScanner, IMediaScanner
from src.domain.models.media.media_item import MediaItem, MediaType
from src.domain.models.media.image_item import ImageItem
from src.domain.models.media.audio_item import AudioItem
from src.domain.models.media.text_item import TextItem


class FileSystemFragmentScanner(IFragmentScanner):
    """File system-based scanner for video fragments."""
    
    SUPPORTED_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
    
    def scan_folder(self, folder_path: Path) -> List[Path]:
        """Scan folder for video files."""
        if not folder_path.exists() or not folder_path.is_dir():
            raise ValueError(f"Invalid folder path: {folder_path}")
        
        video_files = []
        for ext in self.SUPPORTED_EXTENSIONS:
            video_files.extend(folder_path.glob(f'*{ext}'))
            video_files.extend(folder_path.glob(f'*{ext.upper()}'))
        
        return sorted(set(video_files))
    
    def get_supported_extensions(self) -> List[str]:
        """Get supported extensions."""
        return self.SUPPORTED_EXTENSIONS.copy()


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
# Image Scanner
# ---------------------------------------------

class ImageScanner(_BaseFileScanner):
    """Scans a folder for image files and returns ImageItem instances."""
    
    EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif", ".webp"]
    
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
    
    EXTENSIONS = [".mp3", ".wav", ".flac", ".ogg", ".aac", ".m4a", ".wma", ".opus"]
    
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
    
    EXTENSIONS = [".txt", ".csv", ".json", ".xml", ".md", ".rst", ".log"]
    
    @property
    def media_type(self) -> MediaType:
        return MediaType.TEXT
    
    def _make_item(self, item_id: str, path: Path) -> TextItem:
        return TextItem(
            item_id=item_id,
            file_path=str(path)
        )