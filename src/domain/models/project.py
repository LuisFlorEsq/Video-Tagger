from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path

from src.domain.models.fragment import Fragment
from src.core.config import DEFAULT_LABELS

class Project:
    """Represents a video annotation project"""
    
    def __init__(
        self, 
        name: str, 
        folder_path: str,
        save_path: Optional[str] = None,
        created_at: Optional[datetime] = None,
        modified_at: Optional[datetime] = None,
        custom_labels: Optional[List[str]] = None
    ):
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")
        
        self.name = name.strip()
        self.folder_path = folder_path
        self.save_path = save_path
        
        self.custom_labels: List[str] = (
            list(custom_labels) if custom_labels else list(DEFAULT_LABELS)
        )
        
        self._fragments: List[Fragment] = []
        self._fragment_index: Dict[str, int] = {}
        self.created_at = created_at or datetime.now()
        self.modified_at = modified_at or datetime.now()
        
    # ─────────────────────────────────────────────
    # Label management
    # ─────────────────────────────────────────────
    
    def set_labels(self, labels: List[str]) -> None:
        """Replace the label set for this project"""
        cleaned = [lbl.strip() for lbl in labels if lbl.strip()]
        if not cleaned:
            raise ValueError("El proyecto debe tener al menos una etiqueta.")
        self.custom_labels = cleaned
        self.modified_at = datetime.now()
        
    def get_labels(self) -> List[str]:
        return list(self.custom_labels)
    
    # ─────────────────────────────────────────────
    # Fragment management
    # ─────────────────────────────────────────────
    
    @property
    def fragments(self) -> List[Fragment]:
        """Get read-only access to fragments."""
        return self._fragments
    
    def add_fragment(self, fragment: Fragment) -> None:
        """Add a fragment to the project."""
        if fragment.fragment_id in self._fragment_index:  # O(1) instead of O(n)
            raise ValueError(f"Fragment with ID '{fragment.fragment_id}' already exists")
        
        self._fragment_index[fragment.fragment_id] = len(self._fragments)
        self._fragments.append(fragment)
        self.modified_at = datetime.now()
    
    def remove_fragment(self, fragment_id: str) -> bool:
        """Remove a fragment from the project"""
        if fragment_id not in self._fragment_index:
            return False
        
        idx = self._fragment_index[fragment_id]
        self._fragments.pop(idx)
        
        # Rebuild index — indices after the removed position shifted by -1
        self._fragment_index = {
            f.fragment_id: i for i, f in enumerate(self._fragments)
        }
        self.modified_at = datetime.now()
        return True
    
    def get_fragment(self, fragment_id: str) -> Optional[Fragment]:
        """Get a fragment by ID."""
        idx = self._fragment_index.get(fragment_id)
        if idx is None:
            return None
        return self._fragments[idx]
    
    def get_fragment_index(self, fragment_id: str) -> Optional[int]:
        """Get the 0-based position of a fragment by ID."""
        return self._fragment_index.get(fragment_id)
    
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
        idx = self._fragment_index.get(current_fragment_id)
        if idx is None or idx >= len(self._fragments) - 1:
            return None
        return self._fragments[idx + 1]
    
    def get_previous_fragment(self, current_fragment_id: str) -> Optional[Fragment]:
        """Get the previous fragment before the given one."""
        idx = self._fragment_index.get(current_fragment_id)
        if idx is None or idx == 0:
            return None
        return self._fragments[idx - 1]
    
    def set_save_path(self, save_path: Path) -> None:
        """Set the save path for this project."""
        self.save_path = str(save_path)
        self.modified_at = datetime.now()
    
    def get_save_path(self) -> Optional[Path]:
        """Get the save path if set."""
        return Path(self.save_path) if self.save_path else None