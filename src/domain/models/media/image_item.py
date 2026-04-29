from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .media_item import MediaItem, MediaType


@dataclass
class ImageItem(MediaItem):
    """
    A single image file to be labeled.

    Extra fields compared to the base:
        width / height - populated lazily from the infrastucture layer
    """

    width: Optional[int] = None
    height: Optional[int] = None
    source_key: Optional[str] = None

    def __init__(
        self,
        item_id: str,
        file_path: str,
        label: Optional[str] = None,
        notes: str = "",
        width: Optional[int] = None,
        height: Optional[int] = None,
        source_key: Optional[str] = None,
        created_at: Optional[datetime] = None,
        modified_at: Optional[datetime] = None,
    ) -> None:

        super().__init__(
            item_id=item_id,
            file_path=file_path,
            media_type=MediaType.IMAGE,
            label=label,
            notes=notes,
            created_at=created_at or datetime.now(),
            modified_at=modified_at or datetime.now(),
        )
        self.width = width
        self.height = height
        self.source_key = source_key

    def get_image_name(self) -> str:
        return self.get_filename()

    @property
    def has_dimensions(self) -> bool:
        return self.width is not None and self.height is not None

    @property
    def aspect_ratio(self) -> Optional[float]:
        if self.has_dimensions and self.height > 0:
            return self.width / self.height
        return None
