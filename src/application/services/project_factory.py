from pathlib import Path
from typing import Iterable, Optional

from src.domain.interfaces import IMediaPreviewSource, IMediaScanner
from src.domain.models.media import MediaItem, MediaType
from src.domain.models.project import Project

# ---------------------------------------------
# MediaTypeFactory
# ---------------------------------------------


class MediaTypeFactory:
    """
    Creates a project for non-video media types.
    Register one IMediaScanner per MediaType at startup via register_scanner()
    """

    def __init__(self):
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
            raise ValueError(f"No scanner registered for media type: {media_type.value}")

        return scanner.scan_paths(folder_path)

    def create_item(
        self,
        media_type: MediaType,
        index: int,
        file_path: Path,
        strict_metadata: bool = False,
    ) -> MediaItem:

        file_path = Path(file_path)
        preview_source = self._preview_sources.get(media_type)
        item_id = self._make_item_id(media_type=media_type, numeric_id=index)

        if preview_source is None:
            raise ValueError(f"Unsupported media type: {media_type.value}")

        metadata = self._get_metadata(
            media_type=media_type, file_path=file_path, strict=strict_metadata
        )

        # TODO: Change current logic to receive the elements of item id and construct it here

        return preview_source.create_media_item(
            item_id=item_id, file_path=file_path, metadata=metadata
        )

    def _get_metadata(self, media_type: MediaType, file_path: Path, strict: bool = False) -> dict:
        preview_source = self._preview_sources.get(media_type)
        if preview_source is None:
            return {}

        try:
            metadata_reader = getattr(
                preview_source,
                "get_metadata_cached",
                preview_source.get_metadata,
            )
            return metadata_reader(file_path)
        except Exception:
            if strict:
                raise
            return {}

    @staticmethod
    def _make_item_id(media_type: MediaType, numeric_id: int) -> str:
        return f"{media_type.value}_{numeric_id:03d}"

    def create_project(
        self,
        folder_path: Path,
        media_type: MediaType,
        paths: Optional[Iterable[Path]] = None,
    ) -> Project:
        scanned_paths = (
            list(paths)
            if paths is not None
            else self.scan_paths(
                folder_path=folder_path,
                media_type=media_type,
            )
        )
        if not scanned_paths:
            label = media_type.label()
            raise ValueError(f"No se encontraron archivos de {label.lower()} en la carpeta")

        return self.create_project_from_paths(
            folder_path=folder_path,
            media_type=media_type,
            paths=scanned_paths,
        )

    def create_project_from_paths(
        self,
        folder_path: Path,
        media_type: MediaType,
        paths: Iterable[Path],
    ) -> Project:
        path_list = [Path(path) for path in paths]
        if not path_list:
            label = media_type.label()
            raise ValueError(f"No se encontraron archivos de {label.lower()} en la carpeta")

        project = Project(
            name=folder_path.name, folder_path=str(folder_path), media_type=media_type
        )

        for index, file_path in enumerate(sorted(path_list), start=1):
            item = self.create_item(
                media_type=media_type,
                index=index,
                file_path=file_path,
                strict_metadata=True,
            )
            project.add_item(item)

        return project
