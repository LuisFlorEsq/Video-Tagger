# ─────────────────────────────────────────────────────────────────────────────
# PyInstaller spec file for Video-Tagger
# Build with:  pyinstaller app.spec
# ─────────────────────────────────────────────────────────────────────────────

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_all
import os
import sys
import glob

# Project root
ROOT = os.path.dirname(os.path.abspath(SPEC))

# ── Locate Python's DLL directory ─────────────────────────────────────────────
# Resolves the venv's base Python installation to find _ctypes.pyd / libffi-8.dll
_python_dir   = os.path.dirname(sys.executable)          # e.g. .venv\Scripts
_python_base  = os.path.abspath(
    os.path.join(_python_dir, '..', '..'))                # walk up past venv

# Fallback: if we're already in the base interpreter, _python_dir IS the base
if not os.path.exists(os.path.join(_python_base, 'DLLs')):
    _python_base = _python_dir

_dlls_dir = os.path.join(_python_base, 'DLLs')

def _find_dll(name):
    """Return (src_path, '.') tuple if the DLL exists, else empty list."""
    candidate = os.path.join(_dlls_dir, name)
    if os.path.exists(candidate):
        return [(candidate, '.')]
    # Also search alongside python.exe (some installs put DLLs there)
    candidate2 = os.path.join(_python_base, name)
    if os.path.exists(candidate2):
        return [(candidate2, '.')]
    return []

_ctypes_binaries = (
    _find_dll('_ctypes.pyd') +
    _find_dll('libffi-8.dll') +
    _find_dll('libffi-7.dll')   # older Python 3.11 builds used libffi-7
)

# ── Collect full ctypes package so sub-modules are found ─────────────────────
_ctypes_datas, _ctypes_bins, _ctypes_hidden = collect_all('ctypes')

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    # Entry point
    [os.path.join(ROOT, 'main.py')],

    pathex=[ROOT],

    binaries=_ctypes_binaries + _ctypes_bins,

    # ── Data files ────────────────────────────────────────────────────────────
    # Format: (source_path, dest_folder_inside_bundle)
    # The dest folder must match what resource_path() expects.
    datas=[
        # Application assets (icons, images, etc.)
        (os.path.join(ROOT, 'src/ui/resources/icons'), 'ui/resources/icons'),

        # PySide6 Qt multimedia plugins — required for video playback
        (os.path.join(ROOT, '.venv', 'Lib', 'site-packages',
                      'PySide6', 'plugins', 'multimedia'),
         'PySide6/plugins/multimedia'),
    ] + _ctypes_datas,

    # ── Hidden imports ────────────────────────────────────────────────────────
    # Modules that PyInstaller misses because they are imported dynamically.
    hiddenimports=[
        # ctypes — must be explicit so pandas/_ctypes chain resolves cleanly
        '_ctypes',
        'ctypes',
        'ctypes.util',
        'ctypes._endian',

        # PySide6 internals
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',

        # pandas (used by CsvExporter)
        'pandas',
        'pandas._libs.tslibs.base',

        # Application packages
        'src',
        'src.core',
        'src.application',
        'src.application.services',
        'src.domain',
        'src.domain.models',
        'src.infrastructure',
        'src.ui',
        'src.ui.widgets',
        'src.ui.helpers',
        'src.ui.resources',
    ] + _ctypes_hidden,

    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],

    # Modules to exclude — reduces bundle size significantly
    excludes=['cv2'],

    noarchive=False,
    optimize=0,
)

# ── PYZ (pure-Python archive) ─────────────────────────────────────────────────
pyz = PYZ(a.pure)

# ── EXE ───────────────────────────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,   # onedir mode — binaries go to COLLECT
    name='VideoTagger',
    icon=os.path.join(ROOT, 'src', 'ui', 'resources', 'icons', 'app_icon.ico'),
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                # compress binaries if UPX is installed
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# ── COLLECT (onedir output) ───────────────────────────────────────────────────
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VideoTagger',      # output folder: dist/VideoTagger/
)
