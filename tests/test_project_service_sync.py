from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest

from src.domain.models.media import MediaType


def test_video_sync_adds_only_new_files(project_service):
    with tempfile.TemporaryDirectory() as tmp_dir:
        folder = Path(tmp_dir)
        (folder / "clip_01.mp4").write_bytes(b"a")
        (folder / "clip_02.mp4").write_bytes(b"b")

        project = project_service.create_project_from_folder(folder, MediaType.VIDEO)

        (folder / "clip_03.mp4").write_bytes(b"c")
        (folder / "notes.txt").write_text("ignore me", encoding="utf-8")

        new_items = project_service.get_new_items(project)
        assert {path.name for path in new_items} == {"clip_03.mp4"}

        added = project_service.sync_new_items(project, new_items)
        assert added == 1
        assert project.items[-1].item_id == "video_003"


def test_image_project_supports_regular_and_numpy_images(project_service):
    with tempfile.TemporaryDirectory() as tmp_dir:
        folder = Path(tmp_dir)
        (folder / "frame.png").write_bytes(b"png-placeholder")
        np.save(folder / "array_image.npy", np.zeros((5, 7, 3), dtype=np.uint8))

        project = project_service.create_project_from_folder(folder, MediaType.IMAGE)

        assert project.get_total_count() == 2
        numpy_item = next(item for item in project.items if item.file_path.endswith(".npy"))
        assert (numpy_item.width, numpy_item.height) == (7, 5)


def test_signal_project_loads_numpy_metadata(project_service):
    with tempfile.TemporaryDirectory() as tmp_dir:
        folder = Path(tmp_dir)
        np.save(folder / "signal.npy", np.linspace(-1.0, 1.0, 128, dtype=np.float32))
        np.savez(
            folder / "multichannel.npz",
            signal=np.ones((2, 64), dtype=np.float32),
            sample_rate=np.array(200),
        )

        project = project_service.create_project_from_folder(folder, MediaType.SIGNAL)

        assert project.get_total_count() == 2
        npz_item = next(item for item in project.items if item.file_path.endswith(".npz"))
        assert npz_item.channels == 2
        assert npz_item.sample_rate == 200
        assert npz_item.shape == [2, 64]
        assert npz_item.duration_s == pytest.approx(64 / 200)


def test_image_project_rejects_signal_shaped_numpy_array(project_service):
    with tempfile.TemporaryDirectory() as tmp_dir:
        folder = Path(tmp_dir)
        np.save(folder / "bad.npy", np.arange(32, dtype=np.float32))

        with pytest.raises(ValueError):
            project_service.create_project_from_folder(folder, MediaType.IMAGE)
