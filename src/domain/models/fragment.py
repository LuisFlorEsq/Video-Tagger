from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

from src.domain.models.media.media_item import MediaItem, MediaType


@dataclass
class Fragment(MediaItem):
    """Represents a video fragment - Pure domain entity."""

    start_time: float = 0.0
    duration: float = 1.0

    def __init__(
        self,
        fragment_id: str,
        video_path: str,
        start_time: float,
        duration: float = 1.0,
        label: Optional[str] = None,
        notes: str = "",
        created_at: Optional[datetime] = None,
        modified_at: Optional[datetime] = None
    ) -> None:

        super().__init__(
            item_id=fragment_id,
            file_path=video_path,
            media_type=MediaType.VIDEO,
            label=label,
            notes=notes,
            created_at=created_at or datetime.now(),
            modified_at=modified_at or datetime.now(),
        )
        self._validate_video(start_time, duration)
        self.start_time = start_time
        self.duration = duration

    @staticmethod
    def _validate_video(start_time: float, duration: float) -> None:
        if start_time < 0:
            raise ValueError("Start time must be non-negative")
        if duration <= 0:
            raise ValueError("Duration must be positive")

    # ----- Backward compatibility ------

    @property
    def fragment_id(self) -> str:
        return self.item_id

    @fragment_id.setter
    def fragment_id(self, value: str) -> None:
        self.item_id = value

    @property
    def video_path(self) -> str:
        return self.file_path

    @video_path.setter
    def video_path(self, value: str) -> None:
        self.file_path = value

    # ----- Video specific helpers ------

    def get_end_time(self) -> float:
        return self.start_time + self.duration

    def get_video_name(self) -> str:
        return self.get_filename()
