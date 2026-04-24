from __future__ import annotations

import tempfile
from pathlib import Path

from src.domain.models.media import MediaType, SignalItem
from src.domain.models.project import Project
from src.infrastructure.exporters import _item_to_row
from src.infrastructure.repositories import JsonProjectRepository


def test_signal_item_round_trip_in_json_repository():
    project = Project(
        name="signals",
        folder_path="signals",
        media_type=MediaType.SIGNAL,
    )
    item = SignalItem(
        item_id="signal_001",
        file_path="signals/ecg.npy",
        label="normal",
        shape=[2, 256],
        dtype="float32",
        sample_rate=128,
        channels=2,
        duration_s=2.0,
        source_key="signal",
    )
    project.add_item(item)

    repository = JsonProjectRepository()
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "project.json"
        repository.save(project, path)
        loaded = repository.load(path)

    loaded_item = loaded.items[0]
    assert loaded_item.media_type == MediaType.SIGNAL
    assert loaded_item.shape == [2, 256]
    assert loaded_item.dtype == "float32"
    assert loaded_item.sample_rate == 128
    assert loaded_item.source_key == "signal"


def test_export_row_contains_signal_fields():
    item = SignalItem(
        item_id="signal_002",
        file_path="signals/eeg.npz",
        shape=[4, 512],
        dtype="float32",
        sample_rate=256,
        channels=4,
        duration_s=2.0,
        source_key="data",
    )

    row = _item_to_row(item)
    assert row["media_type"] == "signal"
    assert row["shape"] == [4, 512]
    assert row["dtype"] == "float32"
    assert row["channels"] == 4
    assert row["source_key"] == "data"
