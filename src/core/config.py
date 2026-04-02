from pathlib import Path

# ─────────────────────────────────────────────
# View indices (QStackedWidget slots on MainWindow)
# ─────────────────────────────────────────────

VIEW_PROJECT = 0
VIEW_FRAGMENT = 1

# ─────────────────────────────────────────────
# Label configuration
# ─────────────────────────────────────────────

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

# ─────────────────────────────────────────────
# Fragment filter options
# ─────────────────────────────────────────────
FILTER_ALL = "all"
FILTER_LABELED = "labeled"
FILTER_UNLABELED = "unlabeled"

# ─────────────────────────────────────────────
# Icons and assets configuration
# ─────────────────────────────────────────────

ICONS_PATH = Path("ui/resources/icons")
ICON_SIZE = (16, 16)