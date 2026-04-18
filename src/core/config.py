from pathlib import Path

# --------------------------------------------------------------------
# View indices (QStackedWidget slots on MainWindow and Project browser)
# --------------------------------------------------------------------

VIEW_PROJECT = 0
VIEW_FRAGMENT = 1
VIEW_WELCOME = 0
VIEW_LIST = 1

# ---------------------------------------------
# Label configuration
# ---------------------------------------------

DEFAULT_LABELS: list[str] = [
    "Etiqueta 1",
    "Etiqueta 2",
    "Etiqueta 3",
    "Etiqueta 4",
    "Etiqueta 5",
    "Otro"
]

LABELS_MIN_COUNT = 1
LABELS_MAX_COUNT = 20
LABEL_MAX_LENGTH = 60

# ---------------------------------------------
# Items filter options
# ---------------------------------------------
FILTER_ALL = "all"
FILTER_LABELED = "labeled"
FILTER_UNLABELED = "unlabeled"

# ---------------------------------------------
# Icons and assets configuration
# ---------------------------------------------

ICONS_PATH = Path("ui/resources/icons")
ICON_SIZE = (16, 16)

# ---------------------------------------------
# Video metadata timeout
# ---------------------------------------------

METADATA_TIMEOUT_MS = 5_000

# ---------------------------------------------
# Scanner available extensions
# ---------------------------------------------

VIDEO_EXTENSIONS = [".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv"]
IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png",
                    ".bmp", ".gif", ".tiff", ".tif", ".webp"]
AUDIO_EXTENSIONS = [".mp3", ".wav", ".flac",
                    ".ogg", ".aac", ".m4a", ".wma", ".opus"]
TEXT_EXTENSIONS = [".txt", ".csv", ".json", ".xml", ".md", ".rst", ".log"]
