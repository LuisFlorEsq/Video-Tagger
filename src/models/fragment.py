from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

@dataclass
class VideoFragment:
    """Represents a 1-seecond video fragment."""
    
    fragment_id: str
    video_path: str
    start_time: float
    duration: float
    label: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validdatee fragment data after initialization."""
        if self.start_time < 0:
            raise ValueError("Start time must be non-negative.")
        if self.duration <= 0:
            raise ValueError("Duration must be positive.")
    
    def update_label(self, label: str) -> None:
        """Update the label and modification timestamp.

        Args:
            label (str): Current label assigned
        """
        self.label = label
        self.modified_at = datetime.now()
    
    def to_dict(self) -> dict:
        """Convert dictionary for export.

        Returns:
            dict: Metadata from the video_fragment in dictionary form
        """
        return {
            'fragment_id': self.fragment_id,
            'video_path': self.video_path,
            'start_time': self.start_time,
            'duration': self.duration,
            'label': self.label or '',
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'VideoFragment':
        """Create an instance from dictionary (load existing project)

        Args:
            data (dict): Data contained in the JSON project file

        Returns:
            VideoFragment: A new instance of VideoFragment class
        """
        return cls(
            fragment_id = data['fragment_id'],
            video_path = data['video_path'],
            start_time = data['start_time'],
            duration = data.get('duration', 1.0),
            label = data.get('label'),
            created_at = datetime.fromisoformat(data['created_at']),
            modified_at = datetime.fromisoformat(data['modified_at'])
        )
    
    def get_end_time(self) -> float:
        """Get the end time of the fragment."""
        return self.start_time + self.duration
    
    def is_labeled(self) -> bool:
        """Check if the fragment has a label."""
        return self.label is not None and self.label != ""