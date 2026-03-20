from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from pathlib import Path

@dataclass
class Fragment:
    """Represents a video fragment - Pure domain entity."""
    
    fragment_id: str
    video_path: str
    start_time: float
    duration: float = 1.0
    label: Optional[str] = None
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate fragment data."""
        if not self.fragment_id or not self.fragment_id.strip():
            raise ValueError("fragment_id cannot be empty")
        if not self.video_path or not self.video_path.strip():
            raise ValueError("video_path cannot be empty")
        if self.start_time < 0:
            raise ValueError("Start time must be non-negative")
        if self.duration <= 0:
            raise ValueError("Duration must be positive")
    
    def assign_label(self, label: str) -> None:
        """Assign a label to this fragment."""
        if not label or not label.strip():
            raise ValueError("Label cannot be empty")
        self.label = label.strip()
        self.modified_at = datetime.now()
    
    def clear_label(self) -> None:
        """Remove the label from this fragment."""
        self.label = None
        self.modified_at = datetime.now()
    
    def update_notes(self, notes: str) -> None:
        """Update notes for this fragment."""
        self.notes = notes
        self.modified_at = datetime.now()
    
    def is_labeled(self) -> bool:
        """Check if fragment has a label."""
        return self.label is not None and self.label.strip() != ""
    
    def get_end_time(self) -> float:
        """Get the end time of the fragment."""
        return self.start_time + self.duration
    
    def get_video_name(self) -> str:
        """Get just the video filename."""
        return Path(self.video_path).name