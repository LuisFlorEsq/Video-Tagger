from PySide6.QtCore import QEvent, QSize, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.core.config import ICON_SIZE, LABEL_MAX_LENGTH, LABELS_MAX_COUNT, LABELS_MIN_COUNT
from src.core.resources import icon
from src.ui.styles import (
    AppTheme,
    btn_danger,
    btn_ghost,
    btn_primary,
    label_list,
    text_secondary,
    text_section_header,
)


class LabelConfigDialog(QDialog):
    """
    Modal dialog for managing project's label set
    """

    labels_changed = Signal(list)

    def __init__(self, current_labels: list[str], parent=None):
        super().__init__(parent)

        self._original_labels = list(current_labels)

        self.setWindowTitle("Configuración de etiquetas")
        self.setModal(True)
        self.setMinimumSize(420, 480)
        self.resize(420, 520)

        self._init_ui()
        self._populate(current_labels)
        self._update_button_states()

    # ─────────────────────────────────────────────
    # UI construction
    # ─────────────────────────────────────────────

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        # ── Header ───────────────────────────────
        header = QLabel("ETIQUETAS DEL PROYECTO")
        header.setStyleSheet(text_section_header())
        root.addWidget(header)

        hint = QLabel(
            f"Define las categorías disponibles para etiquetar fragmentos. "
            f"Mínimo {LABELS_MIN_COUNT}, máximo {LABELS_MAX_COUNT}."
        )
        hint.setStyleSheet(text_secondary())
        hint.setWordWrap(True)
        root.addWidget(hint)

        # ── List + side buttons ───────────────────
        list_row = QHBoxLayout()
        list_row.setSpacing(8)

        self.label_list = QListWidget()
        self.label_list.setStyleSheet(label_list())
        self.label_list.setDragDropMode(QListWidget.InternalMove)
        self.label_list.currentRowChanged.connect(self._update_button_states)
        self.label_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        list_row.addWidget(self.label_list, stretch=1)

        # Ctrl+Up / Ctrl+Down reorder items via keyboard
        self.label_list.installEventFilter(self)
        list_row.addWidget(self.label_list, stretch=1)

        # Side action buttons (up / down / delete)
        side_btns = QVBoxLayout()
        side_btns.setSpacing(4)

        self.up_btn = QPushButton("")
        self.up_btn.setFixedSize(36, 36)
        self.up_btn.setStyleSheet(btn_ghost())
        self.up_btn.setToolTip("Subir etiqueta")
        self.up_btn.setIcon(icon("navigation/up.png"))
        self.up_btn.setIconSize(QSize(*ICON_SIZE))
        self.up_btn.clicked.connect(self._move_up)
        side_btns.addWidget(self.up_btn)

        self.down_btn = QPushButton("")
        self.down_btn.setFixedSize(36, 36)
        self.down_btn.setStyleSheet(btn_ghost())
        self.down_btn.setToolTip("Bajar etiqueta")
        self.down_btn.setIcon(icon("navigation/down.png"))
        self.down_btn.setIconSize(QSize(*ICON_SIZE))
        self.down_btn.clicked.connect(self._move_down)
        side_btns.addWidget(self.down_btn)

        side_btns.addSpacing(8)

        self.delete_btn = QPushButton("")
        self.delete_btn.setFixedSize(36, 36)
        self.delete_btn.setStyleSheet(btn_danger())
        self.delete_btn.setIcon(icon("delete.png"))
        self.delete_btn.setIconSize(QSize(*ICON_SIZE))

        self.delete_btn.setToolTip("Eliminar etiqueta seleccionada")
        self.delete_btn.clicked.connect(self._delete_selected)
        side_btns.addWidget(self.delete_btn)

        side_btns.addStretch()
        list_row.addLayout(side_btns)
        root.addLayout(list_row)

        # ── Add new label row ─────────────────────
        add_row = QHBoxLayout()
        add_row.setSpacing(8)

        self.new_label_input = QLineEdit()
        self.new_label_input.setPlaceholderText("Nueva etiqueta…")
        self.new_label_input.setMaxLength(LABEL_MAX_LENGTH)
        self.new_label_input.returnPressed.connect(self._add_label)
        self.new_label_input.textChanged.connect(self._update_button_states)
        add_row.addWidget(self.new_label_input, stretch=1)

        self.add_btn = QPushButton("Agregar")
        self.add_btn.setStyleSheet(btn_primary())
        self.add_btn.setFixedHeight(36)
        self.add_btn.clicked.connect(self._add_label)
        add_row.addWidget(self.add_btn)

        root.addLayout(add_row)

        # ── Counter ───────────────────────────────
        self.counter_label = QLabel("")
        self.counter_label.setStyleSheet(text_secondary())
        self.counter_label.setAlignment(Qt.AlignRight)
        root.addWidget(self.counter_label)

        # ── Divider ───────────────────────────────
        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {AppTheme.BORDER}")
        root.addWidget(divider)

        # ── Dialog buttons ───────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()

        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setStyleSheet(btn_ghost())
        self.cancel_btn.setFixedHeight(36)
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.cancel_btn)

        self.ok_btn = QPushButton("Guardar cambios")
        self.ok_btn.setStyleSheet(btn_primary())
        self.ok_btn.setFixedHeight(36)
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self._accept)
        btn_row.addWidget(self.ok_btn)

        root.addLayout(btn_row)

    # ─────────────────────────────────────────────
    # Event filter - keyboard ordering
    # ─────────────────────────────────────────────

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        """Ctrl+Up / Ctrl + Down reorder the selected label without the mouse."""

        if watched is self.label_list and event.type() == QEvent.KeyPress:
            modifiers = event.modifiers()
            key = event.key()
            if modifiers == Qt.ControlModifier:
                if key == Qt.Key_Up:
                    self._move_up()
                    return True
                if key == Qt.Key_Down:
                    self._move_down()
                    return True

        return super().eventFilter(watched, event)

    # ─────────────────────────────────────────────
    # Population
    # ─────────────────────────────────────────────

    def _populate(self, labels: list[str]):
        self.label_list.clear()
        for label in labels:
            self._append_item(label)
        self._refresh_counter()

    def _append_item(self, text: str):
        item = QListWidgetItem(text)
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        font = QFont()
        font.setPointSize(10)
        item.setFont(font)
        self.label_list.addItem(item)

    # ─────────────────────────────────────────────
    # Command handlers
    # ─────────────────────────────────────────────

    def _add_label(self):
        text = self.new_label_input.text().strip()

        if not text:
            return

        if self.label_list.count() >= LABELS_MAX_COUNT:
            QMessageBox.warning(
                self, "Limite alcanzado", f"No puedes tener más de {LABELS_MAX_COUNT} etiquetas."
            )

            return

        # Duplicate check  (case-sensitive)
        existing = [
            self.label_list.item(i).text().strip().lower() for i in range(self.label_list.count())
        ]

        if text.lower() in existing:
            QMessageBox.warning(
                self, "Etiqueta duplicada", f"Ya existe la etiqueta con el nombre {text}"
            )
            return

        self._append_item(text)
        self.new_label_input.clear()
        self.label_list.setCurrentRow(self.label_list.count() - 1)
        self._refresh_counter()
        self._update_button_states()

    def _delete_selected(self):
        row = self.label_list.currentRow()
        if row < 0:
            return

        if self.label_list.count() <= LABELS_MIN_COUNT:
            QMessageBox.warning(
                self,
                "Mínimo requerido",
                f"El proyecto debe tener al menos {LABELS_MIN_COUNT} etiquetas.",
            )
            return

        # label_name = self.label_list.item(row).text()
        self.label_list.takeItem(row)

        # Keep selection near the deleted row
        new_count = self.label_list.count()
        if new_count > 0:
            self.label_list.setCurrentRow(min(row, new_count - 1))

        self._refresh_counter()
        self._update_button_states()

    def _move_up(self):
        row = self.label_list.currentRow()
        if row <= 0:
            return
        item = self.label_list.takeItem(row)
        self.label_list.insertItem(row - 1, item)
        self.label_list.setCurrentRow(row - 1)

    def _move_down(self):
        row = self.label_list.currentRow()
        if row < 0 and row >= self.label_list.count() - 1:
            return
        item = self.label_list.takeItem(row)
        self.label_list.insertItem(row + 1, item)
        self.label_list.setCurrentRow(row + 1)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        """
        Start inline editing on double-click
        """
        self.label_list.editItem(item)

    def _accept(self):
        labels = self._collect_labels()

        if not labels:
            QMessageBox.warning(
                self, "Sin etiquetas", "Debes definir al menos una etiqueta antes de guardar."
            )
            return

        orphaned = self._find_orphaned_labels(labels)
        if orphaned:
            names = ", ".join(f'"{label}"' for label in sorted(orphaned))
            reply = QMessageBox.question(
                self,
                "Etiquetas en uso",
                f"Las siguientes etiquetas ya fueron asignadas a fragmentos "
                f"pero no están en la nueva lista:\n\n{names}\n\n"
                f"Los fragmentos conservarán su etiqueta actual, pero no "
                f"podrás reasignarla desde el panel lateral.\n\n"
                f"¿Deseas continuar?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return

        self.labels_changed.emit(labels)
        self.accept()

    # ─────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────

    def _collect_labels(self) -> list[str]:
        """Return the current list, stripping blanks."""
        result = []
        for i in range(self.label_list.count()):
            text = self.label_list.item(i).text().strip()
            if text:
                result.append(text)
        return result

    def _find_orphaned_labels(self, new_labels: list[str]) -> set[str]:
        """Labels currently assigned to fragments that won't be in the new set."""
        new_set = {label.lower() for label in new_labels}
        return {lbl for lbl in self._assigned_labels if lbl.lower() not in new_set}

    def _refresh_counter(self):
        count = self.label_list.count()
        self.counter_label.setText(f"{count} / {LABELS_MAX_COUNT} etiquetas")

    def _update_button_states(self):
        row = self.label_list.currentRow()
        count = self.label_list.count()
        has_sel = row >= 0
        input_ok = bool(self.new_label_input.text().strip())

        self.up_btn.setEnabled(has_sel and row > 0)
        self.down_btn.setEnabled(has_sel and row < count - 1)
        self.delete_btn.setEnabled(has_sel and count > LABELS_MIN_COUNT)
        self.add_btn.setEnabled(input_ok and count < LABELS_MAX_COUNT)

    # ─────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────

    def set_assigned_labels(self, assigned: set[str]):
        """Pass the set of labels currently used by fragments."""
        self._assigned_labels = set(assigned)

    # Initialise to empty so the dialog works even if the caller forgets to call it
    _assigned_labels: set = set()
