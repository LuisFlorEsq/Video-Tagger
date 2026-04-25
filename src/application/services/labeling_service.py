from typing import List, Optional

from src.domain.models.project import Project
from src.domain.models.media import MediaItem
from src.domain.interfaces import (
    ILabelValidator
)


class LabelingService:
    """Service for labeling operations (SRP)."""

    def __init__(self, validator: Optional[ILabelValidator] = None):
        self._validator = validator

    def assign_label(self, item: MediaItem, project: Project, label: str) -> None:
        """Assign a label to a item with validation."""
        if self._validator and not self._validator.validate(label):
            error = self._validator.get_validation_error(label)
            raise ValueError(error or "Etiqueta no valida")

        previous_label = item.label
        item.assign_label(label)

        if project:
            project.record_label_change(previous_label, item.label)

    def clear_label(self, item: MediaItem, project: Project) -> None:
        """Remove a label from a item."""
        previous_label = item.label
        item.clear_label()

        if project:
            project.record_label_change(previous_label, item.label)

    def batch_assign_label(self, items: List[MediaItem], project: Project, label: str) -> int:
        """
        Assign label to every item in items.
        Returns the count of succesfully labeled items
        """
        count = 0
        for item in items:
            try:
                self.assign_label(item, project, label)
                count += 1
            except ValueError:
                continue
        return count

    def get_items_needing_labels(self, project: Project) -> List[MediaItem]:
        """Return all items that still need a label."""
        return project.get_unlabeled_items()
