from typing import Optional

from src.domain.models.project import Project
from src.domain.models.media import MediaItem


class NavigationService:
    """Service for navigating through media items (SRP)."""

    def __init__(self, project: Project):
        self._project = project
        self._current_item_id: Optional[str] = None

    # ----------------------------
    # Position management
    # ----------------------------

    def set_current_item(self, item_id: str) -> None:
        """Set the current items."""
        if not self._project.get_item(item_id):
            raise ValueError(f"Elemento no encontrado: {item_id}")
        self._current_item_id = item_id

    def get_current_item(self) -> Optional[MediaItem]:
        """Get the current item."""
        if self._current_item_id:
            return self._project.get_item(self._current_item_id)
        return None

    # ----------------------------
    # Navigation
    # ----------------------------

    def move_to_next(self) -> Optional[MediaItem]:
        """Move to the next item."""
        if not self._current_item_id:
            # Start from first item
            first_item = next(self._project.iter_items(), None)
            if first_item:
                self._current_item_id = first_item.item_id
                return first_item
            return None

        next_item = self._project.get_next_item(self._current_item_id)
        if next_item:
            self._current_item_id = next_item.item_id
        return next_item

    def move_to_previous(self) -> Optional[MediaItem]:
        """Move to the previous fragment."""
        if not self._current_item_id:
            return None

        prev_item = self._project.get_previous_item(self._current_item_id)
        if prev_item:
            self._current_item_id = prev_item.item_id
        return prev_item

    def move_to_first(self) -> Optional[MediaItem]:
        """Move to the first fragment."""
        first_item = next(self._project.iter_items(), None)
        if first_item:
            self._current_item_id = first_item.item_id
            return first_item
        return None

    def move_to_last(self) -> Optional[MediaItem]:
        """Move to the last fragment."""
        items = list(self._project.iter_items())
        if items:
            self._current_item_id = items[-1].item_id
            return items[-1]
        return None

    # ----------------------------
    # State queries
    # ----------------------------

    def has_next(self) -> bool:
        """Check if there is a next item."""
        if not self._current_item_id:
            return self._project.get_total_count() > 0
        return self._project.get_next_item(self._current_item_id) is not None

    def has_previous(self) -> bool:
        """Check if there is a previous item."""
        if not self._current_item_id:
            return False
        return self._project.get_previous_item(self._current_item_id) is not None

    def get_position(self) -> tuple[int, int]:
        """Get current position as (current_index, total_count)."""
        total = self._project.get_total_count()
        if not self._current_item_id:
            return (0, total)
        idx = self._project.get_item_index(self._current_item_id)
        if idx is None:
            return (0, total)
        return (idx + 1, total)
