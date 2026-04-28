from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.domain.models.media import MediaItem, MediaType


@dataclass
class AudioItem(MediaItem):
    """
    A single audio clip to be labeled.

    duration_s — total duration in seconds (float).
                 Set to None if unknown; populated by infrastructure on load.
    sample_rate — Hz, optional metadata.
    """

    duration_s: Optional[float] = None
    sample_rate: Optional[int] = None

    def __init__(
        self,
        item_id: str,
        file_path: str,
        label: Optional[str] = None,
        notes: str = "",
        duration_s: Optional[float] = None,
        sample_rate: Optional[int] = None,
        created_at: Optional[datetime] = None,
        modified_at: Optional[datetime] = None,
    ) -> None:

        super().__init__(
            item_id=item_id,
            file_path=file_path,
            media_type=MediaType.AUDIO,
            label=label,
            notes=notes,
            created_at=created_at or datetime.now(),
            modified_at=modified_at or datetime.now(),
        )

        if duration_s is not None and duration_s < 0:
            raise ValueError("duration_s must be non-negative")

        self.duration_s = duration_s
        self.sample_rate = sample_rate

    def get_audio_name(self) -> str:
        return self.get_filename()

    @property
    def duration_label(self) -> str:
        """Human-readable duration string (MM:SS)."""
        if self.duration_s is None:
            return "--:--"
        total_s = int(self.duration_s)
        return f"{total_s // 60:02d}:{total_s % 60:02d}"
