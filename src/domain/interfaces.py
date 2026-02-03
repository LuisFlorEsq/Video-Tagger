from abc import ABC, abstractmethod
from typing import List, Optional
from pathlib import Path

from src.domain.models.project import Project


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


class IVideoSource(ABC):
    """Interface for video file operations."""
    
    @abstractmethod
    def get_duration(self, video_path: Path) -> float:
        """Get video duration in seconds."""
        pass
    
    @abstractmethod
    def get_fps(self, video_path: Path) -> float:
        """Get video frames per second."""
        pass
    
    @abstractmethod
    def exists(self, video_path: Path) -> bool:
        """Check if video file exists."""
        pass


class IFragmentScanner(ABC):
    """Interface for scanning folders for video fragments."""
    
    @abstractmethod
    def scan_folder(self, folder_path: Path) -> List[Path]:
        """Scan a folder and return list of video file paths."""
        pass
    
    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported video file extensions."""
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