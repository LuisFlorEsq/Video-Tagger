from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.domain.models.media import MediaItem, MediaType


@dataclass
class VideoItem(MediaItem):
    """
    A single video clip to be loaded.

    Extra fields:
        start_time: float
        duration: float
    """

    def __init__(
        self,
        item_id: str,
        file_path: str,
        start_time: float = 0.0,
        duration: float = 1.0,
        label: Optional[str] = None,
        notes: str = "",
        created_at: Optional[datetime] = None,
        modified_at: Optional[datetime] = None
    ) -> None:
        super().__init__(
            item_id=item_id,
            file_path=file_path,
            media_type=MediaType.VIDEO,
            label=label,
            notes=notes,
            created_at=created_at or datetime.now(),
            modified_at=modified_at or datetime.now()
        )

        if start_time < 0:
            raise ValueError("start_time must be non-negative")
        if duration <= 0:
            raise ValueError("duration must be positive")

        self.start_time = start_time
        self.duration = duration

    def get_video_name(self) -> str:
        return self.get_filename()

    def get_end_time(self):
        return self.start_time + self.duration
