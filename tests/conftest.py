from __future__ import annotations

import copy
import os
from pathlib import Path

import numpy as np
import pytest

from src.application.services.labeling_service import LabelingService
from src.application.services.project_service import MediaTypeFactory, ProjectService
from src.domain.interfaces import IMediaPreviewSource, IProjectRepository
from src.domain.models.media import (
    AudioItem,
    ImageItem,
    MediaItem,
    MediaType,
    SignalItem,
    TextItem,
    VideoItem,
)
from src.infrastructure.scanners import (
    AudioScanner,
    ImageScanner,
    SignalScanner,
    TextScanner,
    VideoScanner,
)
from src.infrastructure.validators import SimpleLabelValidator

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class MemoryProjectRepository(IProjectRepository):
    def __init__(self) -> None:
        self._storage: dict[str, object] = {}

    def save(self, project, file_path: Path) -> None:
        self._storage[str(Path(file_path))] = copy.deepcopy(project)

    def load(self, file_path: Path):
        return copy.deepcopy(self._storage[str(Path(file_path))])

    def exists(self, file_path: Path) -> bool:
        return str(Path(file_path)) in self._storage


class FakePreviewSource(IMediaPreviewSource):
    def __init__(self, media_type: MediaType, metadata_resolver, item_factory) -> None:
        self._media_type = media_type
        self._metadata_resolver = metadata_resolver
        self._item_factory = item_factory

    @property
    def media_type(self) -> MediaType:
        return self._media_type

    def get_metadata(self, file_path: str) -> dict:
        return dict(self._metadata_resolver(Path(file_path)))

    def create_media_item(self, item_id: str, file_path: Path, metadata: dict) -> MediaItem:
        return self._item_factory(item_id=item_id, file_path=Path(file_path), metadata=metadata)

    def file_exists(self, file_path: str) -> bool:
        return Path(file_path).exists()


@pytest.fixture
def memory_repository() -> MemoryProjectRepository:
    return MemoryProjectRepository()


@pytest.fixture
def media_factory() -> MediaTypeFactory:
    factory = MediaTypeFactory()
    for scanner in (
        VideoScanner(),
        ImageScanner(),
        AudioScanner(),
        SignalScanner(),
        TextScanner(),
    ):
        factory.register_scanner(scanner)

    factory.register_preview_source(
        FakePreviewSource(
            MediaType.VIDEO,
            lambda _path: {"duration_s": 3.5},
            lambda item_id, file_path, metadata: VideoItem(
                item_id=item_id,
                file_path=str(file_path),
                start_time=0.0,
                duration=metadata.get("duration_s", 1.0) or 1.0,
            ),
        )
    )
    factory.register_preview_source(
        FakePreviewSource(
            MediaType.IMAGE,
            lambda path: _image_metadata(path),
            lambda item_id, file_path, metadata: ImageItem(
                item_id=item_id,
                file_path=str(file_path),
                width=metadata.get("width"),
                height=metadata.get("height"),
                source_key=metadata.get("source_key"),
            ),
        )
    )
    factory.register_preview_source(
        FakePreviewSource(
            MediaType.AUDIO,
            lambda _path: {"duration_s": 12.5, "sample_rate": 44100},
            lambda item_id, file_path, metadata: AudioItem(
                item_id=item_id,
                file_path=str(file_path),
                duration_s=metadata.get("duration_s"),
                sample_rate=metadata.get("sample_rate"),
            ),
        )
    )
    factory.register_preview_source(
        FakePreviewSource(
            MediaType.TEXT,
            lambda _path: {"encoding": "utf-8"},
            lambda item_id, file_path, metadata: TextItem(
                item_id=item_id,
                file_path=str(file_path),
                encoding=metadata.get("encoding", "utf-8"),
            ),
        )
    )
    factory.register_preview_source(
        FakePreviewSource(
            MediaType.SIGNAL,
            lambda path: _signal_metadata(path),
            lambda item_id, file_path, metadata: SignalItem(
                item_id=item_id,
                file_path=str(file_path),
                shape=metadata.get("shape"),
                dtype=metadata.get("dtype"),
                sample_rate=metadata.get("sample_rate"),
                channels=metadata.get("channels"),
                duration_s=metadata.get("duration_s"),
                source_key=metadata.get("source_key"),
            ),
        )
    )
    return factory


@pytest.fixture
def project_service(memory_repository: MemoryProjectRepository, media_factory: MediaTypeFactory) -> ProjectService:
    return ProjectService(repository=memory_repository, media_factory=media_factory)


@pytest.fixture
def labeling_service() -> LabelingService:
    return LabelingService(SimpleLabelValidator())


@pytest.fixture(scope="session")
def qt_app():
    pytest.importorskip("PySide6")

    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _image_metadata(path: Path) -> dict:
    if path.suffix.lower() != ".npy":
        return {"width": 12, "height": 8}

    array = np.load(path, allow_pickle=False)
    if array.ndim not in (2, 3):
        raise ValueError("invalid image array")

    return {"width": int(array.shape[1]), "height": int(array.shape[0])}


def _signal_metadata(path: Path) -> dict:
    if path.suffix.lower() == ".npy":
        array = np.load(path, allow_pickle=False)
        return {
            "shape": list(array.shape),
            "dtype": str(array.dtype),
            "sample_rate": None,
            "channels": 1 if array.ndim == 1 else int(array.shape[0]),
            "duration_s": None,
            "source_key": None,
        }

    with np.load(path, allow_pickle=False) as archive:
        array = np.asarray(archive["signal"])
        sample_rate = int(np.asarray(archive["sample_rate"]).item())
        return {
            "shape": list(array.shape),
            "dtype": str(array.dtype),
            "sample_rate": sample_rate,
            "channels": int(array.shape[0]),
            "duration_s": array.shape[1] / sample_rate,
            "source_key": "signal",
        }
