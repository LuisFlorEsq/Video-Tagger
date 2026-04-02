from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from src.ui.styles import (
    AppTheme, label_list, text_section_header,
    chip_labeled, chip_unlabeled,
)

class LabelPanel(QWidget):
    """
    Label picker panel.
    Emits label_assigned(str) when the user clicks a label.
    """

    label_assigned = Signal(str)

    def __init__(self, labels: list = None, parent=None):
        super().__init__(parent)

        self.labels = labels
        self._current_label: str = None
        self._enabled = False

        self._init_ui()
        self._populate_labels()

    # ─────────────────────────────────────────────
    # UI construction
    # ─────────────────────────────────────────────

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Section header
        header = QLabel("ASIGNAR ETIQUETA")
        header.setStyleSheet(text_section_header())
        layout.addWidget(header)

        # Label list
        self.label_list = QListWidget()
        self.label_list.setEnabled(False)
        self.label_list.setStyleSheet(label_list())
        self.label_list.setMouseTracking(True)
        self.label_list.viewport().setCursor(Qt.PointingHandCursor)
        self.label_list.itemActivated.connect(self._on_label_selected)
        
        layout.addWidget(self.label_list)

        # Current label chip
        self.current_label_chip = QLabel("Sin etiqueta")
        self.current_label_chip.setAlignment(Qt.AlignCenter)
        self.current_label_chip.setMinimumHeight(30)
        self.current_label_chip.setStyleSheet(chip_unlabeled())
        layout.addWidget(self.current_label_chip)

    # ─────────────────────────────────────────────
    # Slots
    # ─────────────────────────────────────────────

    def _on_label_selected(self, item: QListWidgetItem):
        if not self._enabled:
            return
        
        label_text = item.data(Qt.UserRole)
        if not label_text:
            return
        
        self._current_label = label_text
        self.label_assigned.emit(label_text)

    # ─────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        self.label_list.setEnabled(enabled)
        
        if enabled:
            self.label_list.setFocus()

    def set_current_label(self, label: str):
        """Reflect the fragment's current label in the chip and list selection."""
        self._current_label = label
        
        if label:
            self.current_label_chip.setText(f"✓  {label}")
            self.current_label_chip.setStyleSheet(chip_labeled())
            
            # Highlight matching row in the list
            for i in range(self.label_list.count()):
                item = self.label_list.item(i)
                if item.data(Qt.UserRole) == label:
                    self.label_list.setCurrentRow(i)
                    return
        else:
            self.current_label_chip.setText("Sin etiqueta asignada")
            self.current_label_chip.setStyleSheet(chip_unlabeled())
            self.label_list.clearSelection()

    def clear_selection(self):
        self.label_list.clearSelection()
        self._current_label = None

    def get_labels(self) -> list:
        return self.labels.copy()

    def set_labels(self, labels: list):
        if labels:
            self.labels = labels.copy()
            self._populate_labels()

    # ─────────────────────────────────────────────
    # Private helpers
    # ─────────────────────────────────────────────

    def _populate_labels(self):
        self.label_list.clear()
        font = QFont()
        font.setPointSize(10)
        
        for idx, label in enumerate(self.labels):
            prefix = f"[{idx+1}] " if idx < 9 else ""
            display_text = f" {prefix}{label}"
            
            item = QListWidgetItem(display_text)
            item.setFont(font)
            
            item.setData(Qt.UserRole, label)
            self.label_list.addItem(item)