from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from pathlib import Path

from src.domain.models.fragment import Fragment

class Project:
    """Represents a video annotation project"""
    
    def __init__(
        self, 
        name: str, 
        folder_path: str,
        save_path: Optional[str] = None,
        created_at: Optional[datetime] = None,
        modified_at: Optional[datetime] = None
    ):
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")
        
        self.name = name.strip()
        self.folder_path = folder_path
        self.save_path = save_path
        self._fragments: List[Fragment] = []
        self.created_at = created_at or datetime.now()
        self.modified_at = modified_at or datetime.now()
    
    @property
    def fragments(self) -> List[Fragment]:
        """Get read-only access to fragments."""
        return self._fragments.copy()
    
    def add_fragment(self, fragment: Fragment) -> None:
        """Add a fragment to the project."""
        if self.get_fragment(fragment.fragment_id):
            raise ValueError(f"Fragment with ID '{fragment.fragment_id}' already exists")
        
        self._fragments.append(fragment)
        self.modified_at = datetime.now()
    
    def remove_fragment(self, fragment_id: str) -> bool:
        """Remove a fragment from the project."""
        fragment = self.get_fragment(fragment_id)
        if fragment:
            self._fragments.remove(fragment)
            self.modified_at = datetime.now()
            return True
        return False
    
    def get_fragment(self, fragment_id: str) -> Optional[Fragment]:
        """Get a fragment by ID."""
        for fragment in self._fragments:
            if fragment.fragment_id == fragment_id:
                return fragment
        return None
    
    def get_fragments_by_label(self, label: str) -> List[Fragment]:
        """Get all fragments with a specific label."""
        return [f for f in self._fragments if f.label == label]
    
    def get_labeled_fragments(self) -> List[Fragment]:
        """Get all labeled fragments."""
        return [f for f in self._fragments if f.is_labeled()]
    
    def get_unlabeled_fragments(self) -> List[Fragment]:
        """Get all unlabeled fragments."""
        return [f for f in self._fragments if not f.is_labeled()]
    
    def get_total_count(self) -> int:
        """Get total fragment count."""
        return len(self._fragments)
    
    def get_labeled_count(self) -> int:
        """Get count of labeled fragments."""
        return len(self.get_labeled_fragments())
    
    def get_unlabeled_count(self) -> int:
        """Get count of unlabeled fragments."""
        return len(self.get_unlabeled_fragments())
    
    def get_progress_percentage(self) -> float:
        """Get labeling progress as percentage."""
        if not self._fragments:
            return 0.0
        return (self.get_labeled_count() / self.get_total_count()) * 100
    
    def get_label_statistics(self) -> dict:
        """Get count of each label."""
        stats = {}
        for fragment in self._fragments:
            if fragment.is_labeled():
                label = fragment.label
                stats[label] = stats.get(label, 0) + 1
        return stats
    
    def clear_all_labels(self) -> None:
        """Remove all labels from all fragments."""
        for fragment in self._fragments:
            fragment.clear_label()
        self.modified_at = datetime.now()
    
    def get_next_fragment(self, current_fragment_id: str) -> Optional[Fragment]:
        """Get the next fragment after the given one."""
        try:
            current_index = next(
                i for i, f in enumerate(self._fragments) 
                if f.fragment_id == current_fragment_id
            )
            if current_index < len(self._fragments) - 1:
                return self._fragments[current_index + 1]
        except StopIteration:
            pass
        return None
    
    def get_previous_fragment(self, current_fragment_id: str) -> Optional[Fragment]:
        """Get the previous fragment before the given one."""
        try:
            current_index = next(
                i for i, f in enumerate(self._fragments) 
                if f.fragment_id == current_fragment_id
            )
            if current_index > 0:
                return self._fragments[current_index - 1]
        except StopIteration:
            pass
        return None
    
    def set_save_path(self, save_path: Path) -> None:
        """Set the save path for this project."""
        self.save_path = str(save_path)
        self.modified_at = datetime.now()
    
    def get_save_path(self) -> Optional[Path]:
        """Get the save path if set."""
        return Path(self.save_path) if self.save_path else None