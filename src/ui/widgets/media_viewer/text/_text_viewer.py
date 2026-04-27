from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QLineEdit,
    QPushButton,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPlainTextEdit,
    QLabel,
    QMessageBox,
)

from src.ui.styles import AppTheme, editor, text_wc, input_field, btn_ghost

from src.core.config import ICON_SIZE
from src.core.resources import icon
from src.domain.models.media.text_item import TextItem
from src.domain.models.project import Project

from src.ui.widgets.media_viewer._base_viewer import BaseViewer


class TextViewer(BaseViewer):
    """Plain-text viewer with read-only editor and persistent inline search."""

    def item_type_label(self) -> str:
        return "texto"

    def build_media_area(self) -> QWidget:
        area = QWidget()
        area.setStyleSheet(f"background-color: {AppTheme.BG_APP};")

        layout = QVBoxLayout(area)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        editor_row = QHBoxLayout()
        editor_row.setContentsMargins(24, 24, 24, 0)
        editor_row.setSpacing(0)
        editor_row.addStretch()

        editor_panel = QWidget()
        editor_panel.setMaximumWidth(920)
        editor_layout = QVBoxLayout(editor_panel)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)

        self._editor = QPlainTextEdit()
        self._editor.setReadOnly(True)
        self._editor.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self._editor.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._editor.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._editor.setStyleSheet(editor())
        editor_layout.addWidget(self._editor)

        editor_row.addWidget(editor_panel, stretch=1)
        editor_row.addStretch()
        layout.addLayout(editor_row, stretch=1)

        self._wc_label = QLabel("")
        self._wc_label.setStyleSheet(text_wc())
        layout.addWidget(self._wc_label)

        return area

    def _populate_topbar_extras(self, tb: QHBoxLayout) -> None:
        self._search_bar = QWidget()
        row = QHBoxLayout(self._search_bar)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(4)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Buscar en texto…")
        self._search_input.setFixedWidth(200)
        self._search_input.setFixedHeight(28)
        self._search_input.setStyleSheet(input_field())

        self._search_input.textChanged.connect(self._on_search_changed)
        self._search_input.returnPressed.connect(self._find_next)
        row.addWidget(self._search_input)

        self._find_btn = QPushButton("")
        self._find_btn.setFixedSize(28, 28)
        self._find_btn.setStyleSheet(btn_ghost())
        self._find_btn.setToolTip("Siguiente coincidencia")
        self._find_btn.setIcon(icon("navigation/right.png"))
        self._find_btn.setIconSize(QSize(*ICON_SIZE))
        self._find_btn.setEnabled(False)
        self._find_btn.clicked.connect(self._find_next)
        row.addWidget(self._find_btn)

        tb.addWidget(self._search_bar)

    def _setup_extra_shortcuts(self, action_factory) -> None:
        action_factory("Ctrl+F", self._focus_search)

    def _focus_search(self) -> None:
        self._search_input.setFocus()
        self._search_input.selectAll()

    def _on_search_changed(self, term: str) -> None:
        has_term = bool(term.strip())
        self._find_btn.setEnabled(has_term)

        if not has_term:
            self._editor.moveCursor(QTextCursor.Start)
            return

        self._editor.moveCursor(QTextCursor.Start)
        self._editor.find(term)

    def _find_next(self) -> None:
        term = self._search_input.text().strip()
        if not term:
            return
        if not self._editor.find(term):
            self._editor.moveCursor(QTextCursor.Start)
            self._editor.find(term)

    def on_item_loaded(self, item: TextItem, project: Project) -> None:
        try:
            content = item.load_content()
        except FileNotFoundError:
            QMessageBox.critical(
                self,
                "Archivo no encontrado",
                f"No se encontró el archivo de texto:\n{item.file_path}",
            )
            return
        except Exception as e:
            QMessageBox.critical(self, "Error al leer archivo", str(e))
            return

        self._editor.setPlainText(content)
        self._editor.moveCursor(QTextCursor.Start)

        words = item.word_count or 0
        chars = len(content)
        self._wc_label.setText(
            f"{words:,} palabras  ·  {chars:,} caracteres  ·  {item.encoding}"
        )
        self._search_input.clear()
        self._find_btn.setEnabled(False)
        self._editor.setFocus()

    def on_reset(self) -> None:
        # logger.debug("TextViewer.on_reset")
        self._editor.clear()
        self._wc_label.setText("")
        self._search_input.clear()
        self._find_btn.setEnabled(False)

    def stop(self) -> None:
        self.on_reset()
