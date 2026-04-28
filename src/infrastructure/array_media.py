import threading
import wave
from collections import OrderedDict
from pathlib import Path
from typing import Optional

import numpy as np
from pydub import AudioSegment
from PySide6.QtGui import QImage, QPixmap

from src.core.config import WAVEFORM_CACHE_MAX_ITEMS

_WAVEFORM_CACHE_LOCK = threading.Lock()
_WAVEFORM_CACHE: OrderedDict[tuple[str, int, int, int], np.ndarray] = OrderedDict()


# ---------------------------------------------
# NumPy and image methods
# ---------------------------------------------


def load_numpy_array(
    file_path: str | Path,
    source_key: str | None = None,
) -> tuple[np.ndarray, str | None, dict]:
    """
    Loads a NumPy array from a .npy or .npz file, getting metadata when present.

    Args:
        file_path (str | Path): Path to the file to load
        source_key (str | None, optional): Specific key used when working with .npz files.
        Defaults to None.

    Raises:
        ValueError: Not supported extensions
        ValueError: .npz file empty
        ValueError: Source key not found

    Returns:
        tuple[np.ndarray, str|None, dict]: Numpy loaded array, source key and metadata dictionary
    """

    path = Path(file_path)

    # Load a simple numpy array
    if path.suffix.lower() == ".npy":
        array = np.load(path, allow_pickle=False)
        return np.asarray(array), None, {}

    if path.suffix.lower() != ".npz":
        raise ValueError(f"Unsupported NumPy file: {path}")

    # Load a numpy array for a .npz file
    with np.load(path, allow_pickle=False) as archive:
        array_keys = [key for key in archive.files if np.asarray(archive[key]).ndim > 0]
        if not array_keys:
            raise ValueError(f"No array payloads found in {path.name}")

        chosen_key = source_key or _default_npz_array_key(array_keys)
        if chosen_key not in archive.files:
            raise ValueError(f"Array key '{chosen_key}' not found in {path.name}")

        metadata = {}
        for key in ("sample_rate", "sr", "fs"):
            if key in archive.files:
                scalar = np.asarray(archive[key])
                if scalar.ndim == 0:
                    metadata["sample_rate"] = int(scalar.item())
                    break

        return np.asarray(archive[chosen_key]), chosen_key, metadata


def is_numpy_media_path(file_path: str | Path) -> bool:
    """
    Check if the extension of a determined file is in NumPy format

    Returns:
        _type_: Bool, true for NumPy formats if not false
    """
    return Path(file_path).suffix.lower() in {".npy", ".npz"}


def is_image_array(array: np.ndarray) -> bool:
    """
    Determines if a specific numpy array has a compatible struct with an image

    Args:
        array (np.ndarray): Image to evaluate in numpy format

    Returns:
        bool: True for image detected, False if not
    """
    if array.ndim == 2:  # Gray Scale image
        return True
    if array.ndim != 3:
        return False
    # Check the image chanels (Gray, RGB, RGBA)
    return array.shape[2] in (1, 3, 4)


def normalize_image_array(array: np.ndarray) -> np.ndarray:
    """
    Normalize a numpy array to convert it to a valid 8-bit image

    If the values of the array are floats between 0 and 1, it rescales them to 255

    Args:
        array (np.ndarray): Image in numpy array format

    Raises:
        ValueError: Not valid image shape.
        ValueError: Image array empty.

    Returns:
        np.ndarray: A numpy array in np.uint8 format.
    """
    arr = np.asarray(array)

    # Array in Gray scale format (H, W, 1) it transforms the array to a 2D dimension (H, W)
    if arr.ndim == 3 and arr.shape[2] == 1:
        arr = arr[:, :, 0]

    if not is_image_array(arr):
        raise ValueError("Unsupported image array shape. Expected HxW, HxWx3, or HxWx4.")

    # If the array is already on uint8 format it doesnt require an extra transformation
    if arr.dtype == np.uint8:
        return arr

    arr = arr.astype(np.float32)
    if arr.size == 0:
        raise ValueError("Image array is empty")

    # Ignore NaN values
    min_val = float(np.nanmin(arr))
    max_val = float(np.nanmax(arr))

    # Return a black image if it is a plain image
    if max_val <= min_val:
        return np.zeros(arr.shape, dtype=np.uint8)

    # Case A: Data already normalized [0.0, 1.0]
    if min_val >= 0.0 and max_val <= 1.0:
        arr = arr * 255.0
    # Case B: Min-Max Rescaling, maping all values into [0.0, 255.0] range
    else:
        arr = (arr - min_val) * (255.0 / (max_val - min_val))

    return np.clip(arr, 0, 255).astype(np.uint8)


def image_array_to_qpixmap(array: np.ndarray) -> QPixmap:
    """
    Convert a numpy array to a QPixmap object for PySide6 rendering

    Args:
        array (np.ndarray): Input numpy array

    Returns:
        QPixmap: Object to render into a PySide widget (QLabel)
    """
    # Validate array is in correct format (uint8, 255)
    arr = normalize_image_array(array)

    # --- Gray Scale case ---
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

    # --- Color image case (RGB, RGBA) ---
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
    """
    Load an image from a standard file or from NumPy array

    Args:
        file_path (str | Path): File route/path
        source_key (str | None, optional): Array key used in .npz files. Defaults to None.

    Returns:
        tuple[QPixmap, dict]: Tuple with generated QPixmap and metadata dictionary.
    """
    path = Path(file_path)

    # Native image format (not NumPy) delegate to PySide6
    if not is_numpy_media_path(path):
        pixmap = QPixmap(str(path))
        return pixmap, {}

    # If it is on Numpy format delegate to the current logic
    array, resolved_key, _ = load_numpy_array(path, source_key=source_key)
    pixmap = image_array_to_qpixmap(array)
    metadata = {
        "width": int(array.shape[1]),
        "height": int(array.shape[0]),
        "source_key": resolved_key,
    }
    return pixmap, metadata


# ---------------------------------------------
# Signal on NumPy format methods
# ---------------------------------------------


def signal_channels_first(array: np.ndarray) -> np.ndarray:
    """
    Validate standard form for the given array (signal/audio)

    Args:
        array (np.ndarray): Signal input array

    Raises:
        ValueError: Array in not supported dimension

    Returns:
        np.ndarray: Array with channels in first axis
    """
    arr = np.asarray(array)
    if arr.ndim == 1:
        # Transform [samples] into [[samples]] (1 channel)
        return arr.reshape(1, -1)
    if arr.ndim != 2:
        raise ValueError("Signals must be 1D or 2D numeric arrays.")
    # If rows <= columns we have (Channels, Samples)
    if arr.shape[0] <= arr.shape[1]:
        return arr
    return arr.T  # Transpose from (Samples, Channels)


def is_signal_array(array: np.ndarray) -> bool:
    """
    Check if a given array can be interpreted as a signal/audio sample.

    Args:
        array (np.ndarray): Input array

    Returns:
        bool: True if have 1D or 2D, False if not
    """
    return np.asarray(array).ndim in (1, 2)


def signal_metadata_from_array(
    array: np.ndarray,
    sample_rate: int | None = None,
    source_key: str | None = None,
) -> dict:
    """
    Creates a metadata dictionary for an audio signal.

    Args:
        array (np.ndarray): Signal array
        sample_rate (int | None, optional): Sample rate. Defaults to None.
        source_key (str | None, optional): Array key for .npz files. Defaults to None.

    Raises:
        ValueError: Not supported dimension

    Returns:
        dict: Metadata dict.
    """
    if not is_signal_array(array):
        raise ValueError("Unsupported signal array shape.")
    channel_first = signal_channels_first(array)
    samples = int(channel_first.shape[1])

    # Get duration only if sample rate is present
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
    """
    Load a signal from a NumPy file and standarize its format into float32

    Args:
        file_path (str | Path): .npy or .npz file path

    Returns:
        tuple[np.ndarray, dict]: Tuple with array as (Channels, Samples)
        in float32 and their metadata dict
    """
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
    """
    Generates a visual downsampling from an audio signal.

    Args:
        samples (np.ndarray): Input audio arrangement
        target_bins (int, optional): Desired number of horizontal points for the resulting graph.
        Defaults to 512.

    Returns:
        np.ndarray: Floating array of 1D normalized between 0.0 and 1.0 with length
        equal to target bins.
    """
    channel_first = signal_channels_first(np.asarray(samples, dtype=np.float32))

    # Convert to Mono by averaging the absolute values of all channels
    mono = np.mean(np.abs(channel_first), axis=0)
    if mono.size == 0:
        return np.zeros(0, dtype=np.float32)

    # Ensure that the number of containers does not exceed the actual data available
    bins = max(1, min(int(target_bins), mono.size))
    chunk = int(np.ceil(mono.size / bins))

    # List comprehension that extracts the maximum amplitude peak in each fragment
    envelope = np.array(
        [mono[i : i + chunk].max(initial=0.0) for i in range(0, mono.size, chunk)],
        dtype=np.float32,
    )

    # Normalize vector resultant, peak max value to 1.0
    max_val = float(envelope.max(initial=0.0))
    if max_val > 0:
        envelope /= max_val
    return envelope


def load_waveform_envelope(file_path: str | Path, target_bins: int = 512) -> np.ndarray:
    """
    Load and process a visual envelope from multiple types of files (.npy, .npz, or .wav).

    Args:
        file_path (str | Path): Path of the audio file or data
        target_bins (int, optional): Resolution points desired for the envelope. Defaults to 512.

    Returns:
        np.ndarray: Unidimensional array with the calculated envelope
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix in {".npy", ".npz"}:
        samples, _ = load_signal_array(path)
        return compute_waveform_envelope(samples, target_bins=target_bins)

    if suffix == ".wav":
        return _load_waveform_from_wav(path, target_bins=target_bins)

    if suffix in {".mp3", ".aac", ".m4a", ".ogg", ".flac", ".wma", ".opus"}:
        return _load_waveform_from_audio_segment(path, target_bins=target_bins)

    return np.zeros(0, dtype=np.float32)


def _load_waveform_from_wav(path: Path, target_bins: int) -> np.ndarray:
    """
    Internal logic to decode WAV files using native library 'wave'

    Args:
        path (Path): File path of the WAV file
        target_bins (int): Targeted bins desired

    Returns:
        np.ndarray: Floating array of 1D normalized between 0.0 and 1.0 with length
        equal to target bins.
    """
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


def _load_waveform_from_audio_segment(path: Path, target_bins: int) -> np.ndarray:
    """
    Decode compressed audio formats using pydub/ffmpeg and build a waveform envelope.

    Args:
        path (Path): The filesystem path to the compressed audio file
        target_bins (int): The desired horizontal resolution for the resulting waveform envelope

    Returns:
        np.ndarray: A float32 NumPy array representing the downsampled waveform envelope.
    """
    if AudioSegment is None:
        return np.zeros(0, dtype=np.float32)

    try:
        segment = AudioSegment.from_file(path)
    except Exception:
        return np.zeros(0, dtype=np.float32)

    raw = np.array(segment.get_array_of_samples())

    if raw.size == 0:
        return np.zeros(0, dtype=np.float32)

    channels = max(1, int(segment.channels))
    if channels > 1:
        raw = raw.reshape(-1, channels).T
    else:
        raw = raw.reshape(1, -1)

    return compute_waveform_envelope(raw, target_bins=target_bins)


def _default_npz_array_key(keys: list[str]) -> str:
    """
    Internal heuristic for determining the principal array in a .npz file for name priority

    Args:
        keys (list[str]): Key words to use

    Returns:
        str: Key to use
    """
    preferred = [
        key for key in keys if key.lower() in {"image", "signal", "data", "array", "arr_0"}
    ]
    if preferred:
        return preferred[0]
    return sorted(keys)[0]


# ---------------------------------------------
# Waveform audio cache management
# ---------------------------------------------


def make_waveform_cache_key(
    file_path: str | Path,
    target_bins: int = 512,
) -> tuple[str, int, int, int]:
    """
    Generate a unique and deterministic cache key based on file metadata

    Args:
        file_path (str | Path): The filesystem path to the compressed audio file.
        target_bins (int, optional): The desired horizontal resolution for the resulting waveform
        envelope. Defaults to 512.

    Returns:
        tuple[str, int, int, int]: A unique four-element identifier tuple
        (resolved_path, modification_time_ns, file_size_bts, target_bins)
    """
    path = Path(file_path).resolve()
    stat = path.stat()
    return (str(path), int(stat.st_mtime_ns), int(stat.st_size), int(target_bins))


def get_cached_waveform_envelope(
    file_path: str | Path,
    target_bins: int = 512,
) -> Optional[np.ndarray]:
    """
    Retrieve a waveform envelope from the cache if it exists.

    If found the item is moved to the end of OrderedDict to sustain its
    lifespan under the Least Recently Used (LRU) eviction policy.

    Args:
        file_path (str | Path): The filesystem path to the audio or signal file
        target_bins (int, optional): The horizontal resolution of the waveform. Defaults to 512.

    Returns:
        Optional[np.ndarray]: A float32 NumPy array copy of the envelope if cached,
            otherwise None.
    """
    try:
        key = make_waveform_cache_key(file_path, target_bins=target_bins)
    except FileNotFoundError:
        return None
    with _WAVEFORM_CACHE_LOCK:
        envelope = _WAVEFORM_CACHE.get(key)
        if envelope is None:
            return None
        _WAVEFORM_CACHE.move_to_end(key)
        return envelope.copy()


def store_waveform_envelope_cache(
    file_path: str | Path,
    envelope: np.ndarray,
    target_bins: int = 512,
) -> np.ndarray:
    """
    Stores a calculated waveform envelope into the global memory cache

    Inserts the item and updates its position for the LRU policy. If the cache
    exceeds `WAVEFORM_CACHE_MAX_ITEMS`, the oldest entries are discarded.

    Args:
        file_path (str | Path): The filesystem path to the audio or signal file.
        envelope (np.ndarray): The calculated float32 waveform array to cache.
        target_bins (int, optional): The horizontal resolution of the waveform. Defaults to 512.

    Returns:
        np.ndarray: A contiguous float32 copy of the stored envelope.
    """
    key = make_waveform_cache_key(file_path, target_bins=target_bins)
    cached = np.asarray(envelope, dtype=np.float32).copy()
    with _WAVEFORM_CACHE_LOCK:
        _WAVEFORM_CACHE[key] = cached
        _WAVEFORM_CACHE.move_to_end(key)
        while len(_WAVEFORM_CACHE) > WAVEFORM_CACHE_MAX_ITEMS:
            _WAVEFORM_CACHE.popitem(last=False)
    return cached


def load_waveform_envelope_cached(
    file_path: str | Path,
    target_bins: int = 512,
) -> tuple[np.ndarray, bool]:
    """
    Attempts to fetch the waveform from cache, or calculates and stores it on miss.

    This acts as a high-level access point for clients requiring optimized waveform data retrieval

    Args:
        file_path (str | Path): The filesystem path to the audio or signal file
        target_bins (int, optional): The horizontal resolution of the waveform. Defaults to 512.

    Returns:
        tuple[np.ndarray, bool]: A tuple containing the floa32 waveform envelope and a flag
        indicating whether is was a cache hit (True) or a cache miss (False)
    """
    cached = get_cached_waveform_envelope(file_path, target_bins=target_bins)
    if cached is not None:
        return cached, True

    try:
        envelope = load_waveform_envelope(file_path, target_bins=target_bins)
    except FileNotFoundError:
        return np.zeros(0, dtype=np.float32), False
    if envelope.size > 0:
        envelope = store_waveform_envelope_cache(
            file_path,
            envelope,
            target_bins=target_bins,
        )
    return envelope, False


def clear_waveform_envelope_cache() -> None:
    """
    Thread-safely clears all entries from the global waveform cache.
    """
    with _WAVEFORM_CACHE_LOCK:
        _WAVEFORM_CACHE.clear()
