from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class FrameAnnotation:
    """Represents a single frame annotation."""
    
    frame_number: int
    timestamp_ms: float
    video_path: str
    label: Optional[str] = None
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate frame data after initialization."""
        if self.frame_number < 0:
            raise ValueError("Frame number must be non-negative")
        if self.timestamp_ms < 0:
            raise ValueError("Timestamp must be non-negative")
    
    def update_label(self, label: str) -> None:
        """Update the label and modification timestamp."""
        self.label = label
        self.modified_at = datetime.now()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for export."""
        return {
            'frame_number': self.frame_number,
            'timestamp_ms': self.timestamp_ms,
            'video_path': self.video_path,
            'label': self.label or '',
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FrameAnnotation':
        """Create instance from dictionary."""
        return cls(
            frame_number=data['frame_number'],
            timestamp_ms=data['timestamp_ms'],
            video_path=data['video_path'],
            label=data.get('label'),
            notes=data.get('notes', ''),
            created_at=datetime.fromisoformat(data['created_at']),
            modified_at=datetime.fromisoformat(data['modified_at'])
        )