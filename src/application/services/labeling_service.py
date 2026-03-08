from typing import List, Optional

from src.domain.models.label import Label
from src.domain.models.project import Project
from src.domain.models.fragment import Fragment
from src.domain.interfaces import (
    ILabelValidator
)


class LabelingService:
    """Service for labeling operations (SRP)."""
    
    def __init__(self, validator: Optional[ILabelValidator] = None):
        self._validator = validator
    
    def assign_label(self, fragment: Fragment, label: str) -> None:
        """Assign a label to a fragment with validation."""
        if self._validator and not self._validator.validate(label):
            error = self._validator.get_validation_error(label)
            raise ValueError(error or "Etiqueta no valida")
        
        fragment.assign_label(label)
    
    def clear_label(self, fragment: Fragment) -> None:
        """Remove a label from a fragment."""
        fragment.clear_label()
    
    def batch_assign_label(self, fragments: List[Fragment], label: str) -> int:
        """Assign the same label to multiple fragments. Returns count of updated fragments."""
        count = 0
        for fragment in fragments:
            try:
                self.assign_label(fragment, label)
                count += 1
            except ValueError:
                continue
        return count
    
    def get_fragments_needing_labels(self, project: Project) -> List[Fragment]:
        """Get all fragments that still need labels."""
        return project.get_unlabeled_fragments()