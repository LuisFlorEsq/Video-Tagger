import wave
from pathlib import Path
from typing import Optional

import numpy as np
from PySide6.QtGui import QImage, QPixmap


def load_numpy_array(
    file_path: str | Path,
    source_key: str | None = None,
) -> tuple[np.ndarray, str | None, dict]:
    path = Path(file_path)

    # Single numpy array
    if path.suffix.lower() == ".npy":
        array = np.load(path, allow_pickle=False)
        return np.asarray(array), None, {}

    if path.suffix.lower() != ".npz":
        raise ValueError(f"Unsupported NumPy file: {path}")
    
    
    # Load a numpy array for a .npz file
    with np.load(path, allow_pickle=False) as archive:
        array_keys = [key for key in archive.files if np.asarray(
            archive[key]).ndim > 0]
        if not array_keys:
            raise ValueError(f"No array payloads found in {path.name}")

        chosen_key = source_key or _default_npz_array_key(array_keys)
        if chosen_key not in archive.files:
            raise ValueError(
                f"Array key '{chosen_key}' not found in {path.name}")

        metadata = {}
        for key in ("sample_rate", "sr", "fs"):
            if key in archive.files:
                scalar = np.asarray(archive[key])
                if scalar.ndim == 0:
                    metadata["sample_rate"] = int(scalar.item())
                    break

        return np.asarray(archive[chosen_key]), chosen_key, metadata


def is_numpy_media_path(file_path: str | Path) -> bool:
    return Path(file_path).suffix.lower() in {".npy", ".npz"}


def is_image_array(array: np.ndarray) -> bool:
    if array.ndim == 2:
        return True
    if array.ndim != 3:
        return False
    return array.shape[2] in (1, 3, 4)


def normalize_image_array(array: np.ndarray) -> np.ndarray:
    arr = np.asarray(array)
    if arr.ndim == 3 and arr.shape[2] == 1:
        arr = arr[:, :, 0]

    if not is_image_array(arr):
        raise ValueError(
            "Unsupported image array shape. Expected HxW, HxWx3, or HxWx4."
        )

    if arr.dtype == np.uint8:
        return arr

    arr = arr.astype(np.float32)
    if arr.size == 0:
        raise ValueError("Image array is empty")

    min_val = float(np.nanmin(arr))
    max_val = float(np.nanmax(arr))
    if max_val <= min_val:
        return np.zeros(arr.shape, dtype=np.uint8)

    if min_val >= 0.0 and max_val <= 1.0:
        arr = arr * 255.0
    else:
        arr = (arr - min_val) * (255.0 / (max_val - min_val))

    return np.clip(arr, 0, 255).astype(np.uint8)


def image_array_to_qpixmap(array: np.ndarray) -> QPixmap:
    arr = normalize_image_array(array)
    if arr.ndim == 2:
        contiguous = np.ascontiguousarray(arr)
        image = QImage(
            contiguous.data,
            contiguous.shape[1],
            contiguous.shape[0],
            contiguous.strides[0],
            QImage.Format_Grayscale8,
        ).copy()
        return QPixmap.fromImage(image)

    fmt = QImage.Format_RGB888 if arr.shape[2] == 3 else QImage.Format_RGBA8888
    contiguous = np.ascontiguousarray(arr)
    image = QImage(
        contiguous.data,
        contiguous.shape[1],
        contiguous.shape[0],
        contiguous.strides[0],
        fmt,
    ).copy()
    return QPixmap.fromImage(image)


def load_image_pixmap(
    file_path: str | Path,
    source_key: str | None = None,
) -> tuple[QPixmap, dict]:
    path = Path(file_path)
    if not is_numpy_media_path(path):
        pixmap = QPixmap(str(path))
        return pixmap, {}

    array, resolved_key, _ = load_numpy_array(path, source_key=source_key)
    pixmap = image_array_to_qpixmap(array)
    metadata = {
        "width": int(array.shape[1]),
        "height": int(array.shape[0]),
        "source_key": resolved_key,
    }
    return pixmap, metadata


def signal_channels_first(array: np.ndarray) -> np.ndarray:
    arr = np.asarray(array)
    if arr.ndim == 1:
        return arr.reshape(1, -1)
    if arr.ndim != 2:
        raise ValueError("Signals must be 1D or 2D numeric arrays.")
    if arr.shape[0] <= arr.shape[1]:
        return arr
    return arr.T


def is_signal_array(array: np.ndarray) -> bool:
    return np.asarray(array).ndim in (1, 2)


def signal_metadata_from_array(
    array: np.ndarray,
    sample_rate: int | None = None,
    source_key: str | None = None,
) -> dict:
    if not is_signal_array(array):
        raise ValueError("Unsupported signal array shape.")
    channel_first = signal_channels_first(array)
    samples = int(channel_first.shape[1])
    duration_s = (samples / sample_rate) if sample_rate else None
    return {
        "shape": list(np.asarray(array).shape),
        "dtype": str(np.asarray(array).dtype),
        "channels": int(channel_first.shape[0]),
        "sample_rate": sample_rate,
        "duration_s": duration_s,
        "source_key": source_key,
    }


def load_signal_array(file_path: str | Path) -> tuple[np.ndarray, dict]:
    array, source_key, extra = load_numpy_array(file_path)
    sample_rate = extra.get("sample_rate")
    metadata = signal_metadata_from_array(
        array,
        sample_rate=sample_rate,
        source_key=source_key,
    )
    return signal_channels_first(array).astype(np.float32), metadata


def compute_waveform_envelope(
    samples: np.ndarray,
    target_bins: int = 512,
) -> np.ndarray:
    channel_first = signal_channels_first(
        np.asarray(samples, dtype=np.float32))
    mono = np.mean(np.abs(channel_first), axis=0)
    if mono.size == 0:
        return np.zeros(0, dtype=np.float32)

    bins = max(1, min(int(target_bins), mono.size))
    chunk = int(np.ceil(mono.size / bins))
    envelope = np.array(
        [mono[i:i + chunk].max(initial=0.0)
         for i in range(0, mono.size, chunk)],
        dtype=np.float32,
    )
    max_val = float(envelope.max(initial=0.0))
    if max_val > 0:
        envelope /= max_val
    return envelope


def load_waveform_envelope(file_path: str | Path, target_bins: int = 512) -> np.ndarray:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix in {".npy", ".npz"}:
        samples, _ = load_signal_array(path)
        return compute_waveform_envelope(samples, target_bins=target_bins)

    if suffix == ".wav":
        return _load_waveform_from_wav(path, target_bins=target_bins)

    return np.zeros(0, dtype=np.float32)


def _load_waveform_from_wav(path: Path, target_bins: int) -> np.ndarray:
    with wave.open(str(path), "rb") as wav_file:
        frames = wav_file.getnframes()
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        raw = wav_file.readframes(frames)

    dtype_map = {1: np.uint8, 2: np.int16, 4: np.int32}
    dtype = dtype_map.get(sample_width)
    if dtype is None:
        return np.zeros(0, dtype=np.float32)

    data = np.frombuffer(raw, dtype=dtype)
    if channels > 1:
        data = data.reshape(-1, channels).T
    else:
        data = data.reshape(1, -1)

    if dtype == np.uint8:
        normalized = (data.astype(np.float32) - 128.0) / 128.0
    else:
        scale = float(np.iinfo(dtype).max)
        normalized = data.astype(np.float32) / scale

    return compute_waveform_envelope(normalized, target_bins=target_bins)


def _default_npz_array_key(keys: list[str]) -> str:
    preferred = [key for key in keys if key.lower(
    ) in {"image", "signal", "data", "array", "arr_0"}]
    if preferred:
        return preferred[0]
    return sorted(keys)[0]
