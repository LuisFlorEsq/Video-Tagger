from enum import Enum
from os import PathLike
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

# ---------------------------------------------
# MediaType enum
# ---------------------------------------------

class MediaType(Enum):
    VIDEO = "video",
    IMAGE = "image",
    AUDIO = "audio",
    TEXT = "text"
    
    @classmethod
    def from_str(cls, value: str) -> "MediaType":
        """
        Case sensitive factory; falls back to video for unknown values
        """
        try:
            return cls(value.lower())
        except (ValueError, AttributeError):
            return cls.VIDEO

    def label(self) -> str:
        """
        Human-readable Spanish label for the UI
        """
        return {
            MediaType.VIDEO: "Video",
            MediaType.IMAGE: "Imagen",
            MediaType.AUDIO: "Audio",
            MediaType.TEXT: "Texto",
        }[self]
    

# ---------------------------------------------
# MediaType base
# ---------------------------------------------

@dataclass
class MediaItem:
    """
    Base class for every labelable media unit.
    
    All media types share: an ID, a file path, a media type tag,
    an optional label, notes, timestamps.
    
    Subclasses and type-specific fields (start_time/duration for video, width/height for images, etc.) without touching this base.
    
    """
    
    item_id: str
    file_path: str
    media_type: MediaType
    
    label: Optional[str] = None
    notes: str = ""
    
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    
    
    def __post_init__(self) -> None:
        if not self.item_id or not self.item_id.strip():
            raise ValueError("item_id cannot be empty")

        self.file_path = self._normalize_path(self.file_path)

        if not self.file_path or not self.file_path.strip():
            raise ValueError("file_path cannot be empty")

    @staticmethod
    def _normalize_path(path: str | PathLike[str]) -> str:
        return str(path)
        
    # ----- Label operations ------
    
    def assign_label(self, label_str: str) -> None:
        """
        Assign a label for this item.
        """
        
        if not label_str or not label_str.strip():
            raise ValueError("label_str cannot be empty")
        self.label = label_str.strip()
        self.modified_at = datetime.now()
    
    def clear_label(self) -> None:
        """
        Remove the label for this item.
        """
        self.label = None
        self.modified_at = datetime.now()
        
    def update_notes(self, notes: str) -> None:
        """
        Update the notes for this item.
        """
        self.notes = notes
        self.modified_at = datetime.now()
    
    def is_labeled(self) -> bool:
        return bool(self.label and self.label.strip())
    
    
    # ----- File helpers ------
    
    def get_filename(self) -> str:
        """
        Return just the filename portion of file_path
        """
        return Path(self.file_path).name
    
    def file_exist(self) -> bool:
        return Path(self.file_path).exists()
