from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar,
    QLineEdit, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from src.domain.models.project import Project
from src.domain.models.media.media_item import MediaItem

from src.core.config import FILTER_ALL, FILTER_LABELED, FILTER_UNLABELED
from src.ui.helpers.project_formatter import format_project_badge, format_project_stats
from src.ui.styles import (
    AppTheme,
    progress_bar, fragment_list,
    text_secondary, text_muted,
    chip_info, input_field
)


class FragmentListPanel(QWidget):
    """Displays the project's fragment list with search and filter controls."""

    fragment_activated = Signal(object)   # user double-clicks / enters a row

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project: Project = None
        self._active_filter = FILTER_ALL
        self._init_ui()

    # ─────────────────────────────────────────────
    # UI construction
    # ─────────────────────────────────────────────

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Filter bar ────────────────────────────
        filter_bar = QWidget()
        filter_bar.setFixedHeight(48)
        filter_bar.setStyleSheet(
            f"background-color: {AppTheme.BG_PANEL};"
            f"border-bottom: 1px solid {AppTheme.BORDER};"
        )
        filter_layout = QHBoxLayout(filter_bar)
        filter_layout.setContentsMargins(14, 0, 14, 0)
        filter_layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar elemento…")
        self.search_input.setFixedHeight(30)
        self.search_input.setFixedWidth(220)
        self.search_input.setStyleSheet(input_field())
        self.search_input.textChanged.connect(self._apply_filter)
        filter_layout.addWidget(self.search_input)
        filter_layout.addSpacing(4)

        self._filter_btns: dict[str, QPushButton] = {}
        for mode, label in [
            (FILTER_ALL,       "Todos"),
            (FILTER_LABELED,   "Etiquetados"),
            (FILTER_UNLABELED, "Sin etiquetar"),
        ]:
            btn = QPushButton(label)
            btn.setFixedHeight(28)
            btn.setCheckable(True)
            btn.setStyleSheet(self._pill_style(active=(mode == FILTER_ALL)))
            btn.clicked.connect(
                lambda checked, m=mode: self._on_filter_clicked(m))
            filter_layout.addWidget(btn)
            self._filter_btns[mode] = btn

        filter_layout.addStretch()

        self.count_label = QLabel("")
        self.count_label.setStyleSheet(text_muted())
        filter_layout.addWidget(self.count_label)

        layout.addWidget(filter_bar)

        # ── Stats toolbar ─────────────────────────
        toolbar = QWidget()
        toolbar.setFixedHeight(36)
        toolbar.setStyleSheet(
            f"background-color: {AppTheme.BG_SUBTLE};"
            f"border-bottom: 1px solid {AppTheme.BORDER};"
        )
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(14, 0, 14, 0)

        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet(text_secondary())
        toolbar_layout.addWidget(self.stats_label)
        toolbar_layout.addStretch()

        self.progress_badge = QLabel("")
        self.progress_badge.setStyleSheet(chip_info())
        self.progress_badge.setVisible(False)
        toolbar_layout.addWidget(self.progress_badge)

        layout.addWidget(toolbar)

        # ── Progress bar ──────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet(progress_bar())

        layout.addWidget(self.progress_bar)

        # ── Item tree ─────────────────────────
        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Archivo", "Etiqueta", "ID"])
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setItemsExpandable(False)
        self.tree.setStyleSheet(fragment_list())
        self.tree.setIndentation(0)
        self.tree.setColumnWidth(0, 500)
        self.tree.setColumnWidth(1, 150)
        self.tree.setColumnWidth(2, 200)
        self.tree.header().setStretchLastSection(False)
        self.tree.itemActivated.connect(self._on_item_activated)

        layout.addWidget(self.tree)

    # ─────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────

    def load(self, project: Project):
        """Replace the displayed project and repopulate the list."""
        self._project = project
        self._active_filter = FILTER_ALL

        self._update_pill_styles()
        self.search_input.clear()

        self._populate()
        self._update_stats()
        self._apply_filter()

        self.set_focus()

    def refresh(self, project: Project):
        """Repopulate preserving the current selection and filter."""
        self._project = project

        selected_id = None
        current = self.tree.currentItem()
        if current:
            selected_id = current.data(0, Qt.UserRole)

        self._populate()
        self._update_stats()
        self._apply_filter()

        # Restore selection by fragment_id
        if selected_id:
            for i in range(self.tree.topLevelItemCount()):
                item = self.tree.topLevelItem(i)
                if item.data(0, Qt.UserRole) == selected_id:
                    self.tree.setCurrentItem(item)
                    break
        elif self.tree.topLevelItemCount() > 0:
            self.tree.setCurrentItem(self.tree.topLevelItem(0))

        self.set_focus()

    def reset(self):
        """Clear all content back to the empty state."""
        self._project = None

        self.tree.clear()
        self.progress_bar.setValue(0)

        self.stats_label.setText("")
        self.count_label.setText("")
        self.progress_badge.setVisible(False)

        self.search_input.clear()
        self._active_filter = FILTER_ALL
        self._update_pill_styles()

    def focus_search(self):
        self.search_input.setFocus()
        self.search_input.selectAll()

    def set_focus(self):
        self.tree.setFocus()

    # ─────────────────────────────────────────────
    # Private — populate and filter
    # ─────────────────────────────────────────────

    def _populate(self):
        self.tree.clear()

        if not self._project:
            return

        for media_item in self._project.items:
            status = media_item.label if media_item.is_labeled() else "Sin etiquetar"
            tree_item = QTreeWidgetItem(
                [media_item.get_video_name(), status, media_item.item_id]
            )
            tree_item.setData(0, Qt.UserRole, media_item.item_id)
            tree_item.setToolTip(0, media_item.file_path)

            color = AppTheme.SUCCESS if media_item.is_labeled() else AppTheme.TEXT_MUTED
            tree_item.setForeground(1, QColor(color))
            self.tree.addTopLevelItem(tree_item)

    def _update_stats(self):
        if not self._project:
            return

        summary = {
            'total_fragments':    self._project.get_total_count(),
            'labeled':            self._project.get_labeled_count(),
            'unlabeled':          self._project.get_unlabeled_count(),
            'progress_percentage': self._project.get_progress_percentage(),
            'label_statistics':   self._project.get_label_statistics(),
        }

        self.stats_label.setText(format_project_stats(summary))
        self.progress_badge.setText(format_project_badge(summary))
        self.progress_badge.setVisible(True)
        self.progress_bar.setValue(int(summary['progress_percentage']))

    def _apply_filter(self):
        if not self._project:
            return

        search = self.search_input.text().strip().lower()
        visible = 0
        total = self.tree.topLevelItemCount()

        for i in range(total):
            tree_item = self.tree.topLevelItem(i)
            item_id = tree_item.data(0, Qt.UserRole)
            media_item = self._project.get_fragment(item_id)

            if media_item is None:
                tree_item.setHidden(True)
                continue

            if self._active_filter == FILTER_LABELED and not media_item.is_labeled():
                tree_item.setHidden(True)
                continue
            if self._active_filter == FILTER_UNLABELED and media_item.is_labeled():
                tree_item.setHidden(True)
                continue

            if search:
                haystack = (
                    media_item.get_video_name().lower()
                    + (media_item.label or "").lower()
                    + media_item.item_id.lower()
                )
                if search not in haystack:
                    tree_item.setHidden(True)
                    continue

            tree_item.setHidden(False)
            visible += 1

        grand_total = self._project.get_total_count()
        if visible == grand_total and not search and self._active_filter == FILTER_ALL:
            self.count_label.setText(f"{grand_total} elementos")
        else:
            self.count_label.setText(f"{visible} / {grand_total} elementos")

    def _on_filter_clicked(self, mode: str):
        self._active_filter = mode
        self._update_pill_styles()
        self._apply_filter()

    def _on_item_activated(self, item: QTreeWidgetItem):
        if not self._project:
            return

        media_item = self._project.get_item(item.data(0, Qt.UserRole))
        if media_item:
            self.fragment_activated.emit(media_item)

    def _update_pill_styles(self):
        for mode, btn in self._filter_btns.items():
            btn.setStyleSheet(self._pill_style(
                active=(mode == self._active_filter)))

    # TODO: Move this method to styles file
    @staticmethod
    def _pill_style(active: bool) -> str:
        t = AppTheme
        if active:
            return (
                f"QPushButton {{"
                f"background-color: {t.PRIMARY_LIGHT};"
                f"color: {t.PRIMARY};"
                f"border: 1px solid {t.PRIMARY};"
                f"border-radius: 10px;"
                f"padding: 0 12px;"
                f"font-size: {t.FONT_SM};"
                f"font-weight: bold;"
                f"}}"
            )
        return (
            f"QPushButton {{"
            f"background-color: transparent;"
            f"color: {t.TEXT_SECONDARY};"
            f"border: 1px solid {t.BORDER};"
            f"border-radius: 10px;"
            f"padding: 0 12px;"
            f"font-size: {t.FONT_SM};"
            f"}}"
            f"QPushButton:hover {{"
            f"background-color: {t.BG_APP};"
            f"color: {t.TEXT_PRIMARY};"
            f"}}"
        )
