from abc import ABC, abstractmethod
from typing import List, Optional
from pathlib import Path

from src.domain.models.project import Project
from src.domain.models.media.media_item import MediaItem, MediaType

# ---------------------------------------------
# Persistence and validators
# ---------------------------------------------


class IProjectRepository(ABC):
    """Interface for project persistence operations."""

    @abstractmethod
    def save(self, project: Project, file_path: Path) -> None:
        """Save a project to storage."""
        pass

    @abstractmethod
    def load(self, file_path: Path) -> Project:
        """Load a project from storage."""
        pass

    @abstractmethod
    def exists(self, file_path: Path) -> bool:
        """Check if a project file exists."""
        pass


class IExporter(ABC):
    """Interface for exporting project data."""

    @abstractmethod
    def export(self, project: Project, output_path: Path) -> None:
        """Export project data to a file."""
        pass

    @abstractmethod
    def get_file_extension(self) -> str:
        """Get the file extension for this export format."""
        pass

    @abstractmethod
    def get_format_name(self) -> str:
        """Get the human-readable format name."""
        pass


class ILabelValidator(ABC):
    """Interface for validating labels."""

    @abstractmethod
    def validate(self, label: str) -> bool:
        """Check if a label is valid."""
        pass

    @abstractmethod
    def get_validation_error(self, label: str) -> Optional[str]:
        """Get validation error message if label is invalid."""
        pass


# ---------------------------------------------
# Multimodal Interfaces
# ---------------------------------------------

class IMediaScanner(ABC):
    """
    Generic folder scanner that produces MediaItem instances.
    """

    @property
    def media_type(self) -> MediaType:
        """
        The MediaType this scanner handles
        """
        pass

    @abstractmethod
    def scan_folder(self, folder_path: Path) -> List[MediaItem]:
        """
        Scan folder_path and return a list of MediaItem subclass instances.
        """
        pass

    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """
        Return lowercase dot-prefixed extensions: ['.jpg', '.png', '.mp4', ...]
        """
        pass


class IMediaPreviewSource(ABC):
    """
    Provides ligthweight metadata and preview data for a media file.

    For images: pixel dimensions
    For audio: duration and sample rate
    For text: encoding detection 
    """

    @property
    @abstractmethod
    def media_type(self) -> MediaType:
        pass

    @abstractmethod
    def get_metadata(self, file_path: str) -> dict:
        """
        Return a dict of type-specific metadata.

        Images  -> {"width": int, "height": int}
        Audio   -> {"duration_s": float, "sample_rate": int | None}
        Text    -> {"encoding": str, "size_bytes": int}
        """
        pass

    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        pass
