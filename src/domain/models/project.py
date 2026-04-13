from datetime import datetime
from os import PathLike
from pathlib import Path
from typing import Optional, List, Dict

from src.domain.models.media.media_item import MediaItem, MediaType
from src.domain.models.fragment import Fragment
from src.core.config import DEFAULT_LABELS

class Project:
    """Represents a labeling project for any media type"""
    
    def __init__(
        self, 
        name: str, 
        folder_path: str,
        save_path: Optional[str] = None,
        media_type: MediaType = MediaType.VIDEO, # Default for compatibility
        created_at: Optional[datetime] = None,
        modified_at: Optional[datetime] = None,
        custom_labels: Optional[List[str]] = None
    ):
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")
        
        self.name = name.strip()
        self.folder_path = self._normalize_path(folder_path)
        self.save_path = self._normalize_path(save_path)
        self.media_type = media_type
        
        self.custom_labels: List[str] = (
            list(custom_labels) if custom_labels else list(DEFAULT_LABELS)
        )
        
        self._items: List[MediaItem] = []
        self._item_index: Dict[str, int] = {}
        
        self.created_at = created_at or datetime.now()
        self.modified_at = modified_at or datetime.now()

    @staticmethod
    def _normalize_path(path: Optional[str | PathLike[str]]) -> Optional[str]:
        if path is None:
            return None
        return str(path)
        
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
    # Item management - generic API
    # ─────────────────────────────────────────────
    
    @property
    def items(self) -> List[MediaItem]:
        """Get read-only access to all media items."""
        return list(self._items)
    
    def add_item(self, item: MediaItem) -> None:
        """Add a media item to the project."""
        if item.item_id in self._item_index:
            raise ValueError(f"Item with ID '{item.item_id}' already exists")
        self._item_index[item.item_id] = len(self._items)
        self._items.append(item)
        self.modified_at = datetime.now()
        
    def remove_item(self, item_id: str) -> bool:
        """Remove a media item from the project"""
        if item_id not in self._item_index:
            return False
        
        idx = self._item_index[item_id]
        self.items.pop(idx)
        self._item_index = {
            it.item_id: i for i, it in enumerate(self._items)
        }
        self.modified_at = datetime.now()
        return True
    
    def get_item(self, item_id: str) -> Optional[MediaItem]:
        idx = self._item_index.get(item_id)
        return self._items[idx] if idx is not None else None
    
    def get_item_index(self, item_id: str) -> Optional[int]:
        return self._item_index.get(item_id)
    
    def get_next_item(self, current_item_id: str) -> Optional[MediaItem]:
        idx = self._item_index.get(current_item_id)
        if idx is None or idx >= len(self._items) - 1:
            return None
        return self._items[idx + 1]
    
    def get_previous_item(self, current_item_id: str) -> Optional[MediaItem]:
        idx = self._item_index.get(current_item_id)
        if idx is None or idx == 0:
            return None
        return self._items[idx - 1]

    # ─────────────────────────────────────────────
    # Video management - Fragment API
    # ─────────────────────────────────────────────

    @property
    def fragments(self) -> List[Fragment]:
        """
        Returns fragments for video projects.
        """
        return [it for it in self._items if isinstance(it, Fragment)]
 
    def add_fragment(self, fragment: Fragment) -> None:
        """Preserved entry point used throughout existing code."""
        self.add_item(fragment)
 
    def remove_fragment(self, fragment_id: str) -> bool:
        return self.remove_item(fragment_id)
 
    def get_fragment(self, fragment_id: str) -> Optional[Fragment]:
        item = self.get_item(fragment_id)
        return item if isinstance(item, Fragment) else None
 
    def get_fragment_index(self, fragment_id: str) -> Optional[int]:
        return self.get_item_index(fragment_id)
 
    def get_next_fragment(self, current_fragment_id: str) -> Optional[Fragment]:
        item = self.get_next_item(current_fragment_id)
        return item if isinstance(item, Fragment) else None
 
    def get_previous_fragment(self, current_fragment_id: str) -> Optional[Fragment]:
        item = self.get_previous_item(current_fragment_id)
        return item if isinstance(item, Fragment) else None
 
    def get_fragments_by_label(self, label: str) -> List[Fragment]:
        return [f for f in self.fragments if f.label == label]
    

    # ─────────────────────────────────────────────
    # Statistics - general
    # ─────────────────────────────────────────────
    
    def get_labeled_items(self) -> List[MediaItem]:
        return [it for it in self._items if it.is_labeled()]
 
    def get_unlabeled_items(self) -> List[MediaItem]:
        return [it for it in self._items if not it.is_labeled()]
 
    # Legacy names delegated — existing callers unchanged
    def get_labeled_fragments(self) -> List[Fragment]:
        return [f for f in self.fragments if f.is_labeled()]
 
    def get_unlabeled_fragments(self) -> List[Fragment]:
        return [f for f in self.fragments if not f.is_labeled()]
 
    def get_total_count(self) -> int:
        return len(self._items)
 
    def get_labeled_count(self) -> int:
        return len(self.get_labeled_items())
 
    def get_unlabeled_count(self) -> int:
        return len(self.get_unlabeled_items())
 
    def get_progress_percentage(self) -> float:
        if not self._items:
            return 0.0
        return (self.get_labeled_count() / self.get_total_count()) * 100
 
    def get_label_statistics(self) -> dict:
        stats: Dict[str, int] = {}
        for item in self._items:
            if item.is_labeled():
                stats[item.label] = stats.get(item.label, 0) + 1
        return stats
 
    def clear_all_labels(self) -> None:
        for item in self._items:
            item.clear_label()
        self.modified_at = datetime.now()
 
    # ─────────────────────────────────────────────
    # Save path helpers
    # ─────────────────────────────────────────────
    
    def set_save_path(self, save_path: Path | PathLike[str] | str) -> None:
        self.save_path = self._normalize_path(save_path)
        self.modified_at = datetime.now()
        
    
    def get_save_path(self) -> Optional[str]:
        return Path(self.save_path) if self.save_path else None
