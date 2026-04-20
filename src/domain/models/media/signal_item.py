from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.domain.models.media.media_item import MediaItem, MediaType


@dataclass
class SignalItem(MediaItem):
    """
    Numeric sampled signal persisted on disk, typically in NumPy formats.
    """

    shape: Optional[list[int]] = None
    dtype: Optional[str] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    duration_s: Optional[float] = None
    source_key: Optional[str] = None

    def __init__(
        self,
        item_id: str,
        file_path: str,
        label: Optional[str] = None,
        notes: str = "",
        shape: Optional[list[int]] = None,
        dtype: Optional[str] = None,
        sample_rate: Optional[int] = None,
        channels: Optional[int] = None,
        duration_s: Optional[float] = None,
        source_key: Optional[str] = None,
        created_at: Optional[datetime] = None,
        modified_at: Optional[datetime] = None,
    ) -> None:
        super().__init__(
            item_id=item_id,
            file_path=file_path,
            media_type=MediaType.SIGNAL,
            label=label,
            notes=notes,
            created_at=created_at or datetime.now(),
            modified_at=modified_at or datetime.now(),
        )

        self.shape = list(shape) if shape else None
        self.dtype = dtype
        self.sample_rate = sample_rate
        self.channels = channels
        self.duration_s = duration_s
        self.source_key = source_key

    @property
    def duration_label(self) -> str:
        if self.duration_s is None:
            return "--:--"
        total_s = int(self.duration_s)
        return f"{total_s // 60:02d}:{total_s % 60:02d}"
