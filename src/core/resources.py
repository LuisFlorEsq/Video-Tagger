import sys
from pathlib import Path

def base_dir() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[2] # Up to src/

def resource_path(relative: str) -> str:
    """
    Return the absolute path to a bundled resource.

    Args:
        relative (str): Path relative to the project root

    Returns:
        str: Absolute path that works both in development and when running from a 
        PyInstaller onedir bundle.
    """
    return str(base_dir() / relative)