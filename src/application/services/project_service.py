from pathlib import Path
from typing import Optional

from src.domain.models.media.media_item import MediaItem, MediaType
from src.domain.models.media.audio_item import AudioItem
from src.domain.models.media.image_item import ImageItem
from src.domain.models.media.text_item import TextItem
from src.domain.models.media.video_item import VideoItem
from src.domain.models.project import Project
from src.domain.interfaces import (
    IMediaPreviewSource,
    IProjectRepository,
    IMediaScanner
)

# ---------------------------------------------
# Project Service
# ---------------------------------------------


class ProjectService:
    """Service for project-related operations (SRP)."""

    def __init__(
        self,
        repository: IProjectRepository,
        media_factory: Optional["MediaTypeFactory"] = None
    ):
        self._repository = repository
        self._media_factory = media_factory

    # ---- Project creation ----

    def create_project_from_folder(self, folder_path: Path, media_type: MediaType) -> Project:
        """Create a new project by scanning *folder_path*."""
        if not folder_path.exists():
            raise ValueError(f"La carpeta no existe: {folder_path}")

        if self._media_factory is None:
            raise RuntimeError(
                "MediaTypeFactory is required for non-video projects"
                "Register it in the service container"
            )

        return self._media_factory.create_project(folder_path, media_type)

    # ---- Persistence ----

    def save_project(self, project: Project, file_path: Path) -> None:
        """Save a project to file."""
        self._repository.save(project, file_path)

    def auto_save_project(self, project: Project) -> bool:
        """
        Auto-save project to its saved location.

        Args:
            project: Project to save

        Returns:
            True if saved successfully, False otherwise
        """
        save_path = project.get_save_path()

        if not save_path:
            return False

        try:
            self._repository.save(project, save_path)
            return True
        except Exception as e:
            print(f"Auto-save failed: {e}")
            return False

    def load_project(self, file_path: Path) -> Project:
        """Load a project from file."""
        if not self._repository.exists(file_path):
            raise ValueError(f"El proyecto no existe: {file_path}")

        return self._repository.load(file_path)

    # ---- Sync new MediaItems ----

    def get_new_items(self, project: Project) -> set[Path]:
        """
        Get the count of new MediaItems in a project folder

        Args:
            project (Project): Project to check

        Returns:
            set[Path]: Set of new MediaItems detected
        """
        folder_path = Path(project.folder_path)

        if not folder_path.exists():
            return set()

        if self._media_factory is None:
            raise RuntimeError("MediaTypeFactory is required for project sync")

        all_paths = self._media_factory.scan_paths(
            folder_path=folder_path,
            media_type=project.media_type
        )
        existing_paths = {Path(it.file_path) for it in project.items}
        new_items = set(all_paths) - existing_paths

        return new_items

    def sync_new_items(self, project: Project, new_items: set[Path]) -> int:
        """
        Add new MediaItems detected for the current project

        Args:
            project (Project): Project to sync
            new_items (set[Path]): New MediaItems detected by scanning the project's folder

        Returns:
            int: Number of new items added
        """
        if not new_items:
            return 0

        if self._media_factory is None:
            raise RuntimeError("MediaTypeFactory is required for project sync")

        # Derive the next numeric id for the existing item_ids
        max_id = 0
        for it in project.items:
            try:
                max_id = max(max_id, int(it.item_id.split("_")[-1]))
            except ValueError:
                pass
        next_id = max_id + 1

        added = 0
        for file_path in sorted(new_items):
            try:
                item = self._media_factory.create_item(
                    media_type=project.media_type,
                    item_id=self._make_item_id(project.media_type, next_id),
                    file_path=file_path,
                )
                project.add_item(item)
                next_id += 1
                added += 1
            except Exception as e:
                print(f"Failed to add {file_path}: {e}")
        return added

    @staticmethod
    def _make_item_id(media_type: MediaType, numeric_id: int) -> str:
        return f"{media_type.value}_{numeric_id:03d}"

    # ---- Statistics ----

    def get_project_summary(self, project: Project) -> dict:
        """Get a summary of project statistics."""
        return {
            'name': project.name,
            'media_type': project.media_type.value,
            'total_fragments': project.get_total_count(),
            'labeled': project.get_labeled_count(),
            'unlabeled': project.get_unlabeled_count(),
            'progress_percentage': project.get_progress_percentage(),
            'label_statistics': project.get_label_statistics()
        }


# ---------------------------------------------
# MediaTypeFactory
# ---------------------------------------------

class MediaTypeFactory:
    """
    Creates a project for non-video media types.

    ProjectService delegates here when MediaType != VIDEO

    Register one IMediaScanner per MediaType at startup via register_scanner()
    """

    def __init__(
        self
    ):
        self._scanners: dict[MediaType, IMediaScanner] = {}
        self._preview_sources: dict[MediaType, IMediaPreviewSource] = {}

    def register_scanner(self, scanner: IMediaScanner) -> None:
        self._scanners[scanner.media_type] = scanner

    def register_preview_source(self, preview_source: IMediaPreviewSource) -> None:
        self._preview_sources[preview_source.media_type] = preview_source

    def get_scanner(self, media_type: MediaType) -> Optional[IMediaScanner]:
        return self._scanners.get(media_type)

    def scan_paths(self, folder_path: Path, media_type: MediaType) -> list[Path]:

        scanner = self.get_scanner(media_type)
        if scanner is None:
            raise ValueError(
                f"No scanner registered for media type: {media_type.value}"
            )

        return [Path(item.file_path) for item in scanner.scan_folder(folder_path)]

    def create_item(
        self,
        media_type: MediaType,
        item_id: str,
        file_path: Path,
    ) -> MediaItem:
        file_path = Path(file_path)

        metadata = self._get_metadata(media_type, file_path)

        if media_type == MediaType.VIDEO:
            return VideoItem(
                item_id=item_id,
                file_path=file_path,
                start_time=0,
                duration=metadata.get("duration_s")
            )

        if media_type == MediaType.IMAGE:
            return ImageItem(
                item_id=item_id,
                file_path=str(file_path),
                width=metadata.get("width"),
                height=metadata.get("height"),
            )

        if media_type == MediaType.AUDIO:
            return AudioItem(
                item_id=item_id,
                file_path=str(file_path),
                duration_s=metadata.get("duration_s"),
                sample_rate=metadata.get("sample_rate"),
            )

        if media_type == MediaType.TEXT:
            return TextItem(
                item_id=item_id,
                file_path=str(file_path),
                encoding=metadata.get("encoding", "utf-8"),
            )

        raise ValueError(f"Unsupported media type: {media_type.value}")

    def _get_metadata(self, media_type: MediaType, file_path: Path) -> dict:
        preview_source = self._preview_sources.get(media_type)
        if preview_source is None:
            return {}

        try:
            return preview_source.get_metadata(file_path)
        except Exception:
            return {}

    def create_project(self, folder_path: Path, media_type: MediaType) -> Project:
        paths = self.scan_paths(folder_path=folder_path, media_type=media_type)
        if not paths:
            label = media_type.label()
            raise ValueError(
                f"No se encontraron archivos de {label.lower()} en la carpeta"
            )

        project = Project(
            name=folder_path.name,
            folder_path=str(folder_path),
            media_type=media_type
        )

        for index, file_path in enumerate(paths, start=1):
            item = self.create_item(
                media_type=media_type,
                item_id=ProjectService._make_item_id(media_type, index),
                file_path=file_path,
            )
            project.add_item(item)

        return project
