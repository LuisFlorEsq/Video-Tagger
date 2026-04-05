# -----------------------------------------------------------------------------
# PyInstaller spec file for Video-Tagger
# Build with: pyinstaller app.spec
# Output: dist/VideoTagger/VideoTagger.exe
# -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_all, collect_submodules
from PyInstaller.compat import is_win
import os
import sys


# -----------------------------------------------------------------------------
# Paths / Constants
# -----------------------------------------------------------------------------

ROOT = os.path.dirname(os.path.abspath(SPEC))

APP_NAME = "VideoTagger"
ENTRYPOINT = os.path.join(ROOT, "main.py")

ICON_FILE = os.path.join(ROOT, "src", "ui", "resources", "icons", "app_icon.ico")

ASSETS_DIR = os.path.join(ROOT, "src", "ui", "resources", "icons")

# You can change this in one place if you reorganize your project.
ASSETS_DEST = "ui/resources/icons"


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def norm(path: str) -> str:
    """Normalize path for current OS."""
    return os.path.normpath(path)


def find_python_base() -> str:
    """
    Resolve the base Python directory even when running inside a venv.
    We want to locate DLLs consistently.
    """
    python_dir = os.path.dirname(sys.executable)

    # venv usually: .venv/Scripts/python.exe
    candidate = os.path.abspath(os.path.join(python_dir, "..", ".."))

    # If candidate does not contain DLLs, fallback
    if not os.path.exists(os.path.join(candidate, "DLLs")):
        candidate = python_dir

    return candidate


def find_dll(dlls_dir: str, python_base: str, name: str):
    """
    Return a PyInstaller binaries tuple list: [(src, ".")]
    """
    candidate1 = os.path.join(dlls_dir, name)
    if os.path.exists(candidate1):
        return [(candidate1, ".")]

    candidate2 = os.path.join(python_base, name)
    if os.path.exists(candidate2):
        return [(candidate2, ".")]

    return []


def collect_ctypes_dependencies():
    """
    ctypes is one of the most common causes of missing DLL problems on Windows.
    We collect both package content and critical DLLs.
    """
    python_base = find_python_base()
    dlls_dir = os.path.join(python_base, "DLLs")

    binaries = []
    if is_win:
        binaries += find_dll(dlls_dir, python_base, "_ctypes.pyd")
        binaries += find_dll(dlls_dir, python_base, "libffi-8.dll")
        binaries += find_dll(dlls_dir, python_base, "libffi-7.dll")

    datas, bins, hidden = collect_all("ctypes")

    return datas, bins + binaries, hidden


def collect_pyside_multimedia_plugins():
    """
    PySide6 multimedia plugins must be bundled for video playback.
    Using sysconfig/site-packages resolution is better than hardcoding .venv.
    """
    try:
        import PySide6
        pyside_root = os.path.dirname(PySide6.__file__)
        multimedia_path = os.path.join(pyside_root, "plugins", "multimedia")

        if os.path.exists(multimedia_path):
            return [(multimedia_path, "PySide6/plugins/multimedia")]

    except Exception:
        pass

    return []


# -----------------------------------------------------------------------------
# Dependency Collection
# -----------------------------------------------------------------------------

ctypes_datas, ctypes_bins, ctypes_hidden = collect_ctypes_dependencies()

pyside_multimedia_datas = collect_pyside_multimedia_plugins()

# Only list "problematic" hidden imports here.
# Avoid listing your entire project manually.
hiddenimports = (
    ctypes_hidden
    + [
        "_ctypes",
        "ctypes",
        "ctypes.util",
        "ctypes._endian",

        # PySide6 (Qt dynamic loading)
        "PySide6.QtMultimedia",
        "PySide6.QtMultimediaWidgets",

        # pandas sometimes triggers dynamic submodule loads
        "pandas._libs.tslibs.base",
    ]
)

# Optional: automatically include all submodules of your own project.
# This is safer than manually listing everything, but can increase size.
hiddenimports += collect_submodules("src")


datas = [
    # App icons/resources
    (ASSETS_DIR, ASSETS_DEST),
] + pyside_multimedia_datas + ctypes_datas

binaries = ctypes_bins


# -----------------------------------------------------------------------------
# Analysis
# -----------------------------------------------------------------------------

a = Analysis(
    [ENTRYPOINT],
    pathex=[ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "cv2",
    ],
    noarchive=False,
    optimize=0,
)


# -----------------------------------------------------------------------------
# PYZ
# -----------------------------------------------------------------------------

pyz = PYZ(a.pure)


# -----------------------------------------------------------------------------
# EXE
# -----------------------------------------------------------------------------

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # onedir mode
    name=APP_NAME,
    icon=ICON_FILE,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False
)


# -----------------------------------------------------------------------------
# COLLECT
# -----------------------------------------------------------------------------

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)