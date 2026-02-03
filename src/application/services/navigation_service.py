from typing import Optional

from src.domain.models.project import Project, Fragment


class NavigationService:
    """Service for navigating through fragments (SRP)."""
    
    def __init__(self, project: Project):
        self._project = project
        self._current_fragment_id: Optional[str] = None
    
    def set_current_fragment(self, fragment_id: str) -> None:
        """Set the current fragment."""
        if not self._project.get_fragment(fragment_id):
            raise ValueError(f"Fragment not found: {fragment_id}")
        self._current_fragment_id = fragment_id
    
    def get_current_fragment(self) -> Optional[Fragment]:
        """Get the current fragment."""
        if self._current_fragment_id:
            return self._project.get_fragment(self._current_fragment_id)
        return None
    
    def move_to_next(self) -> Optional[Fragment]:
        """Move to the next fragment."""
        if not self._current_fragment_id:
            # Start from first fragment
            if self._project.get_total_count() > 0:
                first_fragment = self._project.fragments[0]
                self._current_fragment_id = first_fragment.fragment_id
                return first_fragment
            return None
        
        next_fragment = self._project.get_next_fragment(self._current_fragment_id)
        if next_fragment:
            self._current_fragment_id = next_fragment.fragment_id
        return next_fragment
    
    def move_to_previous(self) -> Optional[Fragment]:
        """Move to the previous fragment."""
        if not self._current_fragment_id:
            return None
        
        prev_fragment = self._project.get_previous_fragment(self._current_fragment_id)
        if prev_fragment:
            self._current_fragment_id = prev_fragment.fragment_id
        return prev_fragment
    
    def move_to_first(self) -> Optional[Fragment]:
        """Move to the first fragment."""
        if self._project.get_total_count() > 0:
            first_fragment = self._project.fragments[0]
            self._current_fragment_id = first_fragment.fragment_id
            return first_fragment
        return None
    
    def move_to_last(self) -> Optional[Fragment]:
        """Move to the last fragment."""
        if self._project.get_total_count() > 0:
            last_fragment = self._project.fragments[-1]
            self._current_fragment_id = last_fragment.fragment_id
            return last_fragment
        return None
    
    def has_next(self) -> bool:
        """Check if there is a next fragment."""
        if not self._current_fragment_id:
            return self._project.get_total_count() > 0
        return self._project.get_next_fragment(self._current_fragment_id) is not None
    
    def has_previous(self) -> bool:
        """Check if there is a previous fragment."""
        if not self._current_fragment_id:
            return False
        return self._project.get_previous_fragment(self._current_fragment_id) is not None
    
    def get_position(self) -> tuple[int, int]:
        """Get current position as (current_index, total_count)."""
        if not self._current_fragment_id:
            return (0, self._project.get_total_count())
        
        for i, fragment in enumerate(self._project.fragments):
            if fragment.fragment_id == self._current_fragment_id:
                return (i + 1, self._project.get_total_count())
        
        return (0, self._project.get_total_count())