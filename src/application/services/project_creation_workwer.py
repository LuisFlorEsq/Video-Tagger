from pathlib import Path
from typing import Iterable, Optional

from PySide6.QtCore import QObject, Signal

from src.application.services.project_factory import MediaTypeFactory
from src.domain.models.media import MediaType
from src.domain.models.project import Project


class ProjectCreationCancelled(Exception):  # noqa: N818
    """
    Raised internally when the user cancels mid-creation.
    """

    pass


class ProjectCreationWorker(QObject):
    """
    Performs a file-by-file work of building a Project off the GUI thread
    """

    # (current_index, total_count, filename)
    progress = Signal(int, int, str)
    finished = Signal(object)
    # (message, failed_file_path)
    failed = Signal(str, str)
    cancelled = Signal()

    def __init__(
        self,
        media_factory: MediaTypeFactory,
        folder_path: Path,
        media_type: MediaType,
        paths: Optional[Iterable[Path]] = None,
    ) -> None:
        super().__init__()
        self._media_factory = media_factory
        self._folder_path = folder_path
        self._media_type = media_type
        self._explicit_paths = list(paths) if paths is not None else None
        self._cancel_requested = False

    # ---------------------------------------------
    # Public control (safe to call from the GUI thread)
    # ---------------------------------------------

    def request_cancel(self) -> None:
        """Thread-safe-enough: a plain bool flip, checked between files."""
        self._cancel_requested = True

    # ---------------------------------------------
    # Entry point
    # ---------------------------------------------

    def run(self) -> None:
        try:
            project = self._build_project()
        except ProjectCreationCancelled:
            self.cancelled.emit()
            return
        except Exception as exc:
            failed_path = getattr(exc, "media_file_path", "")
            self.failed.emit(str(exc), failed_path)
            return

        self.finished.emit(project)

    # ---------------------------------------------
    # Internal
    # ---------------------------------------------

    def _build_project(self) -> Project:
        if self._explicit_paths is not None:
            scanned_paths = self._explicit_paths
        else:
            scanned_paths = self._media_factory.scan_paths(
                folder_path=self._folder_path,
                media_type=self._media_type,
            )

        path_list = sorted(Path(p) for p in scanned_paths)

        if not path_list:
            label = self._media_type.label()
            raise ValueError(f"No se encontraron archivos de {label.lower()} en la carpeta")

        project = Project(
            name=self._folder_path.name,
            folder_path=str(self._folder_path),
            media_type=self._media_type,
        )

        total = len(path_list)

        for index, file_path in enumerate(path_list, start=1):
            if self._cancel_requested:
                raise ProjectCreationCancelled()

            self.progress.emit(index, total, file_path.name)

            try:
                item = self._media_factory.create_item(
                    media_type=self._media_type,
                    index=index,
                    file_path=file_path,
                    strict_metadata=True,
                )
            except Exception as exc:
                exc.media_file_path = str(file_path)
                raise

            project.add_item(item)

        return project
