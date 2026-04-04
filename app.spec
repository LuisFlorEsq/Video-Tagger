# ─────────────────────────────────────────────────────────────────────────────
# PyInstaller spec file for Video-Tagger
# Build with:  pyinstaller app.spec
# ─────────────────────────────────────────────────────────────────────────────

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import os

# Project root
ROOT = os.path.dirname(os.path.abspath(SPEC))

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    # Entry point
    [os.path.join(ROOT, 'main.py')],

    pathex=[ROOT],

    binaries=[],

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
    ],

    # ── Hidden imports ────────────────────────────────────────────────────────
    # Modules that PyInstaller misses because they are imported dynamically.
    hiddenimports=[
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
        'src.ui.resources'
    ],

    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],

    # Modules to exclude — reduces bundle size significantly
    excludes=[
        'tkinter',
        'cv2',
        'unittest',
        'email',
        'html',
        'http',
        'urllib',
        'xmlrpc',
        'pydoc',
        'doctest',
        'difflib',
        'ftplib',
        'imaplib',
        'mailbox',
        'mimetypes',
        'sqlite3',
    ],

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
    console=True,           # no console window
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
