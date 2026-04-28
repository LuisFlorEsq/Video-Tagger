from datetime import datetime
from os import PathLike
from pathlib import Path
from typing import Dict, Iterator, List, Optional

from src.core.config import DEFAULT_LABELS
from src.domain.models.media.media_item import MediaItem, MediaType


class Project:
    """Represents a labeling project for any media type"""

    def __init__(
        self,
        name: str,
        folder_path: str,
        save_path: Optional[str] = None,
        media_type: MediaType = None,
        created_at: Optional[datetime] = None,
        modified_at: Optional[datetime] = None,
        custom_labels: Optional[List[str]] = None,
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
        self._label_statistics: Dict[str, int] = {}
        self._labeled_count = 0
        self._unlabeled_count = 0
        self._next_item_sequence = 1

        self.created_at = created_at or datetime.now()
        self.modified_at = modified_at or datetime.now()

    @staticmethod
    def _normalize_path(path: Optional[str | PathLike[str]]) -> Optional[str]:
        if path is None:
            return None
        return str(path)

    # ---------------------------------------------
    # Label management
    # ---------------------------------------------

    def set_labels(self, labels: List[str]) -> None:
        """Replace the label set for this project"""
        cleaned = [lbl.strip() for lbl in labels if lbl.strip()]
        if not cleaned:
            raise ValueError("El proyecto debe tener al menos una etiqueta.")
        self.custom_labels = cleaned
        self.modified_at = datetime.now()

    def get_labels(self) -> List[str]:
        return list(self.custom_labels)

    # ---------------------------------------------
    # Item management - generic API
    # ---------------------------------------------

    @property
    def items(self) -> List[MediaItem]:
        """Get read-only access to all media items."""
        return list(self._items)

    def iter_items(self) -> Iterator[MediaItem]:
        """Iterate over project items without copying the internal list."""
        return iter(self._items)

    def add_item(self, item: MediaItem) -> None:
        """Add a media item to the project."""
        if item.item_id in self._item_index:
            raise ValueError(f"Item with ID '{item.item_id}' already exists")
        self._item_index[item.item_id] = len(self._items)
        self._items.append(item)
        self._register_item_state(item)
        self.modified_at = datetime.now()

    def remove_item(self, item_id: str) -> bool:
        """Remove a media item from the project"""
        if item_id not in self._item_index:
            return False

        idx = self._item_index[item_id]
        removed_item = self._items.pop(idx)
        self._item_index.pop(item_id, None)
        self._unregister_item_state(removed_item)
        self._rebuild_item_index(start_index=idx)
        self.modified_at = datetime.now()
        return True

    def get_item(self, item_id: str) -> Optional[MediaItem]:
        idx = self.get_item_index(item_id)
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

    def get_item_by_label(self, label: str) -> List[MediaItem]:
        return [it for it in self._items if it.label == label]

    # ---------------------------------------------
    # Statistics - general
    # ---------------------------------------------

    def get_labeled_items(self) -> List[MediaItem]:
        return [it for it in self._items if it.is_labeled()]

    def get_unlabeled_items(self) -> List[MediaItem]:
        return [it for it in self._items if not it.is_labeled()]

    def get_total_count(self) -> int:
        return len(self._items)

    def get_labeled_count(self) -> int:
        return self._labeled_count

    def get_unlabeled_count(self) -> int:
        return self._unlabeled_count

    def get_progress_percentage(self) -> float:
        total = self.get_total_count()
        if not total:
            return 0.0
        return (self.get_labeled_count() / total) * 100

    def get_label_statistics(self) -> dict:
        return dict(self._label_statistics)

    def clear_all_labels(self) -> None:
        for item in self._items:
            if item.is_labeled():
                item.clear_label()
        self._label_statistics.clear()
        self._labeled_count = 0
        self._unlabeled_count = len(self._items)
        self.modified_at = datetime.now()

    # ---------------------------------------------
    # Save path helpers
    # ---------------------------------------------

    def set_save_path(self, save_path: Path | PathLike[str] | str) -> None:
        self.save_path = self._normalize_path(save_path)
        self.modified_at = datetime.now()

    def get_save_path(self) -> Optional[str]:
        return Path(self.save_path) if self.save_path else None

    def get_next_item_sequence(self) -> int:
        return self._next_item_sequence

    def record_label_change(
        self, previous_label: Optional[str], new_label: Optional[str]
    ) -> None:
        if previous_label == new_label:
            return

        if previous_label:
            current_count = self._label_statistics.get(previous_label, 0) - 1
            if current_count > 0:
                self._label_statistics[previous_label] = current_count
            else:
                self._label_statistics.pop(previous_label, None)
            self._labeled_count = max(0, self._labeled_count - 1)
            self._unlabeled_count = min(len(self._items), self._unlabeled_count + 1)

        if new_label:
            self._label_statistics[new_label] = self._label_statistics.get(new_label, 0) + 1
            self._labeled_count += 1
            self._unlabeled_count = max(0, self._unlabeled_count - 1)

        self.modified_at = datetime.now()

    def get_summary(self) -> dict:
        return {
            "name": self.name,
            "media_type": self.media_type.value,
            "total_fragments": self.get_total_count(),
            "labeled": self.get_labeled_count(),
            "unlabeled": self.get_unlabeled_count(),
            "progress_percentage": self.get_progress_percentage(),
            "label_statistics": self.get_label_statistics(),
        }

    def _register_item_state(self, item: MediaItem) -> None:
        if item.is_labeled():
            self._labeled_count += 1
            self._label_statistics[item.label] = self._label_statistics.get(item.label, 0) + 1
        else:
            self._unlabeled_count += 1

        item_sequence = self._extract_item_sequence(item.item_id)
        if item_sequence is not None:
            self._next_item_sequence = max(self._next_item_sequence, item_sequence + 1)

    def _unregister_item_state(self, item: MediaItem) -> None:
        if item.is_labeled():
            self._labeled_count = max(0, self._labeled_count - 1)
            label = item.label
            current_count = self._label_statistics.get(label, 0) - 1
            if current_count > 0:
                self._label_statistics[label] = current_count
            else:
                self._label_statistics.pop(label, None)
        else:
            self._unlabeled_count = max(0, self._unlabeled_count - 1)

    def _rebuild_item_index(self, start_index: int = 0) -> None:
        for index in range(start_index, len(self._items)):
            self._item_index[self._items[index].item_id] = index

    @staticmethod
    def _extract_item_sequence(item_id: str) -> Optional[int]:
        try:
            return int(item_id.split("_")[-1])
        except (ValueError, AttributeError):
            return None
