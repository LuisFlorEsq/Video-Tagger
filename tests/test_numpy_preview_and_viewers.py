from __future__ import annotations

import math
import tempfile
import time
import wave
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

pytest.importorskip("PySide6")
pytest.importorskip("pydub")

from PySide6.QtWidgets import QApplication

from src.application.services.labeling_service import LabelingService
from src.application.services.project_service import ProjectService
import src.infrastructure.array_media as array_media
from src.infrastructure.array_media import load_waveform_envelope
from src.infrastructure.preview_sources import ImagePreviewSource, SignalPreviewSource
from src.infrastructure.validators import SimpleLabelValidator
from src.domain.models.media import MediaType, ImageItem, SignalItem
from src.domain.models.project import Project
from src.ui.widgets.media_viewer._viewer_stack import ViewerStack
from src.ui.widgets.media_viewer.audio._audio_utils import AudioPlayerWidget
from src.ui.widgets.media_viewer.image._image_viewer import ImageViewer
from src.ui.widgets.media_viewer.signal._signal_viewer import SignalViewer


pytestmark = pytest.mark.qt


class NullRepository:
    def save(self, project, file_path: Path) -> None:
        return None

    def load(self, file_path: Path):
        raise NotImplementedError

    def exists(self, file_path: Path) -> bool:
        return False


def _services():
    project_service = ProjectService(repository=NullRepository(), media_factory=None)
    labeling_service = LabelingService(SimpleLabelValidator())
    return project_service, labeling_service


def _write_test_wav(path: Path) -> None:
    sample_rate = 8000
    duration_s = 0.25
    amplitude = 16000
    samples = []
    total = int(sample_rate * duration_s)
    for index in range(total):
        value = int(amplitude * math.sin(2 * math.pi * 440 * (index / sample_rate)))
        samples.append(value)

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(np.array(samples, dtype=np.int16).tobytes())


def _wait_for_waveform(app: QApplication, player: AudioPlayerWidget, timeout_s: float = 1.0) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        app.processEvents()
        if player._waveform._envelope.size > 0:
            return
        time.sleep(0.01)


def test_image_preview_source_reads_numpy_dimensions(qt_app):
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "img.npy"
        np.save(path, np.zeros((9, 11), dtype=np.float32))

        metadata = ImagePreviewSource().get_metadata(path)
        assert metadata["width"] == 11
        assert metadata["height"] == 9


def test_signal_preview_source_reads_numpy_metadata(qt_app):
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "signal.npz"
        np.savez(path, signal=np.ones((3, 30), dtype=np.float32), sample_rate=np.array(100))

        metadata = SignalPreviewSource().get_metadata(path)
        assert metadata["shape"] == [3, 30]
        assert metadata["channels"] == 3
        assert metadata["sample_rate"] == 100


def test_waveform_loader_generates_envelope_from_wav(qt_app):
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "tone.wav"
        _write_test_wav(path)

        envelope = load_waveform_envelope(path, target_bins=64)
        assert envelope.size > 0
        assert float(envelope.max()) > 0.0


def test_waveform_loader_generates_envelope_from_compressed_audio(qt_app):
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "tone.mp3"
        path.write_bytes(b"fake mp3 bytes")

        class FakeSegment:
            channels = 2

            def get_array_of_samples(self):
                return np.array([0, 1000, -1000, 500], dtype=np.int16)

        class FakeAudioSegment:
            @staticmethod
            def from_file(_path):
                return FakeSegment()

        with patch.object(array_media, "AudioSegment", FakeAudioSegment):
            envelope = load_waveform_envelope(path, target_bins=64)

    assert envelope.size > 0
    assert float(envelope.max()) > 0.0


def test_waveform_cache_reuses_envelope(qt_app):
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "tone.wav"
        _write_test_wav(path)
        array_media.clear_waveform_envelope_cache()

        calls = {"count": 0}

        def fake_loader(_path, target_bins=512):
            calls["count"] += 1
            return np.array([0.25, 0.5, 0.25], dtype=np.float32)

        with patch.object(array_media, "load_waveform_envelope", side_effect=fake_loader):
            first, first_hit = array_media.load_waveform_envelope_cached(path)
            second, second_hit = array_media.load_waveform_envelope_cached(path)

        assert first_hit is False
        assert second_hit is True
        assert calls["count"] == 1
        assert np.array_equal(first, second)


def test_image_viewer_loads_numpy_image_item(qt_app, project_service, labeling_service):
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "img.npy"
        np.save(path, np.ones((6, 10, 3), dtype=np.float32))

        viewer = ImageViewer(labeling_service, project_service)
        project = Project("images", str(path.parent), media_type=MediaType.IMAGE)
        item = ImageItem("image_001", str(path))

        viewer.load_item(item, project)
        assert viewer.dim_label.text() == "10 x 6 px"
        assert not viewer._image_label.pixmap().isNull()


def test_audio_player_loads_real_waveform(qt_app):
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "tone.wav"
        _write_test_wav(path)

        player = AudioPlayerWidget()
        player.load(str(path), path.name)
        _wait_for_waveform(qt_app, player)

        assert player._waveform._envelope.size > 0


def test_audio_player_stop_clears_waveform_state(qt_app):
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "tone.wav"
        _write_test_wav(path)

        player = AudioPlayerWidget()
        player.load(str(path), path.name)
        player.stop()

        assert player._waveform._envelope.size == 0
        assert player._waveform._message == "Waveform unavailable"


def test_viewer_stack_dispatches_signal_items(qt_app, project_service, labeling_service):
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "signal.npy"
        np.save(path, np.linspace(-1.0, 1.0, 50, dtype=np.float32))

        stack = ViewerStack(labeling_service, project_service)
        project = Project("signals", str(path.parent), media_type=MediaType.SIGNAL)
        item = SignalItem("signal_001", str(path))

        stack.load_item(item, project)
        assert isinstance(stack.currentWidget(), SignalViewer)
