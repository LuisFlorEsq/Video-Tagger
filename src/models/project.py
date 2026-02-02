from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from pathlib import Path
import json

from src.models.fragment import VideoFragment

@dataclass
class Project:
    """Represents a video annotation project."""
    
    name: str
    folder_path: str
    fragments: List[VideoFragment] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    
    def add_fragment(self, fragment: VideoFragment) -> None:
        """Add a fragment to the project."""
        self.fragments.append(fragment)
        self.modified_at = datetime.now()
    
    def get_fragment(self, fragment_id: str) -> Optional[VideoFragment]:
        """Get a fragment by ID."""
        for fragment in self.fragments:
            if fragment.fragment_id == fragment_id:
                return fragment
        return None
    
    def get_labeled_count(self) -> int:
        """Get count of labeled fragments."""
        return sum(1 for f in self.fragments if f.is_labeled())
    
    def get_total_count(self) -> int:
        """Get total fragment count."""
        return len(self.fragments)
    
    def get_progress_percentage(self) -> float:
        """Get labeling progress as percentage."""
        if not self.fragments:
            return 0.0
        return (self.get_labeled_count() / self.get_total_count()) * 100
    
    def to_dict(self) -> dict:
        """Convert to dictionary for saving."""
        return {
            'name': self.name,
            'folder_path': self.folder_path,
            'fragments': [f.to_dict() for f in self.fragments],
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Project':
        """Create instance from dictionary."""
        project = cls(
            name=data['name'],
            folder_path=data['folder_path'],
            created_at=datetime.fromisoformat(data['created_at']),
            modified_at=datetime.fromisoformat(data['modified_at'])
        )
        project.fragments = [
            VideoFragment.from_dict(f) for f in data.get('fragments', [])
        ]
        return project
    
    def save_to_file(self, filepath: Path) -> None:
        """Save project to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: Path) -> 'Project':
        """Load project from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        return cls.from_dict(data)