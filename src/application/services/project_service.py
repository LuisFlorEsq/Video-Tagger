from pathlib import Path
from typing import Iterable, Optional

from src.application.services.project_factory import MediaTypeFactory
from src.domain.interfaces import IProjectRepository
from src.domain.models.media import MediaType
from src.domain.models.project import Project

# ---------------------------------------------
# Project Service
# ---------------------------------------------


class ProjectService:
    """Service for project-related operations (SRP)."""

    def __init__(
        self,
        repository: IProjectRepository,
        media_factory: Optional["MediaTypeFactory"] = None,
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

    def create_project_from_paths(
        self,
        folder_path: Path,
        media_type: MediaType,
        paths: Iterable[Path],
    ) -> Project:
        """Create a project from pre-scanned paths."""
        if self._media_factory is None:
            raise RuntimeError(
                "MediaTypeFactory is required for non-video projects"
                "Register it in the service container"
            )

        return self._media_factory.create_project_from_paths(
            folder_path=folder_path,
            media_type=media_type,
            paths=paths,
        )

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
            folder_path=folder_path, media_type=project.media_type
        )
        existing_paths = {Path(it.file_path) for it in project.iter_items()}
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

        next_id = project.get_next_item_sequence()  # Get the current project next_id

        added = 0
        for file_path in sorted(new_items):
            try:
                item = self._media_factory.create_item(
                    media_type=project.media_type,
                    index=next_id,
                    file_path=file_path,
                )
                project.add_item(item)
                next_id += 1
                added += 1
            except Exception as e:
                print(f"Failed to add {file_path}: {e}")
        return added

    def sync_new_items_from_paths(self, project: Project, new_items: Iterable[Path]) -> int:
        """Sync new media from any iterable of file paths."""
        return self.sync_new_items(project, set(Path(path) for path in new_items))

    # ---- Statistics ----

    def get_project_summary(self, project: Project) -> dict:
        """Get a summary of project statistics."""
        return project.get_summary()
