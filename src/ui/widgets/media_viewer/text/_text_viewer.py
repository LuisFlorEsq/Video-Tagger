from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QLineEdit,
    QPushButton,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPlainTextEdit,
    QLabel,
    QMessageBox
)

from src.ui.styles import (
    AppTheme,
    editor,
    text_wc, input_field,
    btn_ghost
)

from src.core.logger import logger
from src.domain.models.media.text_item import TextItem
from src.domain.models.project import Project

from src.ui.widgets.media_viewer._base_viewer import BaseViewer


class TextViewer(BaseViewer):
    """Plain-text viewer with read-only editor and inline search (Ctrl + F)"""

    def item_type_label(self) -> str:
        return "texto"

    def build_media_area(self) -> QWidget:
        area = QWidget()
        area.setStyleSheet(f"background-color: {AppTheme.BG_APP};")

        layout = QVBoxLayout(area)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._editor = QPlainTextEdit()
        self._editor.setReadOnly(True)
        self._editor.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self._editor.setStyleSheet(editor())
        layout.addWidget(self._editor, stretch=1)

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

        self._search_input.textChanged.connect(self._find_next)
        self._search_input.returnPressed.connect(self._find_next)
        row.addWidget(self._search_input)

        self._find_btn = QPushButton("")
        self._find_btn.setFixedSize(28, 28)
        self._find_btn.setStyleSheet(btn_ghost())
        self._find_btn.clicked.connect(self._find_next)
        row.addWidget(self._find_btn)

        self._search_bar.setVisible(False)
        tb.addWidget(self._search_bar)

    def _setup_extra_shortcuts(self, action_factory) -> None:
        action_factory("Ctrl+F", self._toggle_search)

    def _toggle_search(self) -> None:
        visible = not self._search_bar.isVisible()
        self._search_bar.setVisible(visible)

        if visible:
            self._search_input.setFocus()
            self._search_input.selectAll()
        else:
            self._editor.setFocus()

    def _find_next(self) -> None:
        term = self._search_input.text()
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
                self, "Archivo no encontrado",
                f"No se encontró el archivo de texto:\n{item.file_path}"
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
        self._search_bar.setVisible(False)
        self._search_input.clear()

    def on_reset(self) -> None:
        # logger.debug("TextViewer.on_reset")
        self._editor.clear()
        self._wc_label.setText("")
        self._search_bar.setVisible(False)
