from abc import abstractmethod

from PySide6.QtCore import QEvent, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from src.application.services.labeling_service import LabelingService
from src.application.services.navigation_service import NavigationService
from src.application.services.project_service import ProjectService
from src.core.config import DEFAULT_LABELS, ICON_SIZE
from src.core.resources import icon
from src.domain.models.media.media_item import MediaItem
from src.domain.models.project import Project
from src.ui.helpers.dividers import make_hline, make_vline
from src.ui.styles import (
    AppTheme,
    btn_danger,
    btn_ghost,
    btn_primary_sm,
    chip_labeled,
    chip_unlabeled,
    info_strip,
    text_breadcrumb,
    text_section_header,
    topbar_panel,
)

from ._label_panel import LabelPanel


class BaseViewer(QWidget):
    """
    Abstract base class for all media viewer widgets
    """

    # ------ Signals --------
    item_labeled = Signal(object)  # emits MediaItem
    prev_requested = Signal()
    next_requested = Signal()
    back_requested = Signal()
    auto_saved = Signal()

    def __init__(
        self,
        labeling_service: LabelingService,
        project_service: ProjectService,
        available_labels: list | None = None,
        parent=None,
    ) -> None:

        super().__init__(parent)

        self._labeling_service = labeling_service
        self._project_service = project_service
        self._navigation_service: NavigationService | None = None

        self._current_item: MediaItem | None = None
        self._current_project: Project | None = None

        self.available_labels = (available_labels or DEFAULT_LABELS).copy()

        self._auto_save_timer = QTimer()
        self._auto_save_timer.setSingleShot(True)
        self._auto_save_timer.timeout.connect(self._auto_save_project)
        self._auto_save_delay_ms = 3000
        self._has_unsaved_changes = False

        self._init_ui()
        self._connect_base_signals()
        self._setup_shortcuts()

    # --------------------------------------
    # Hooks - subclass must / may override
    # --------------------------------------

    @abstractmethod
    def build_media_area(self) -> QWidget:
        """Return the central content widget for this media type"""
        ...

    def build_info_rows(self, info_layout: QVBoxLayout) -> None:
        """
        Append type-specific metadata rows to the info strip

        Defatult: no-op (subclass overrides when it has extra fields)
        """
        ...

    @abstractmethod
    def on_item_loaded(self, item: MediaItem, project: Project) -> None:
        """
        Load item into media widget

        Called after the base has updated all shared UI
        """
        ...

    def on_reset(self) -> None:
        """
        Stop/Clear the media widget beforee the base clears shared state

        Default: no-op
        """
        ...

    @abstractmethod
    def item_type_label(self) -> str:
        """
        Short ui term for this media type, used in dialog messages.

        e.g "Imagen", "Audio", etc.
        """
        ...

    def _populate_topbar_extras(self, tb: QHBoxLayout) -> None:
        """
        Optional Hook: injects widgets between the breadcrumb search stretch and the position
        counter (e.g. zoom controls for ImageViewer)
        Default: no-op
        """
        ...

    def _setup_extra_shortcuts(self, action_factory) -> None:
        """
        Hook: register additional shortcuts using *action_factory(shortcut, slot)*.
        Default: no-op.
        """
        ...

    def _handle_extra_key(self, key: int) -> bool:
        """
        Hook: handle aditional keys inside the eventFilter
        Return True if the key was consumed, False to let base handling run
        Default: no-op returning False
        """
        return False

    def _on_before_back(self) -> None:
        """Hook called at the start of _on_back_clicked (e.g. stop video)"""
        ...

    # --------------------------------------
    # UI Construction - base
    # --------------------------------------

    def _init_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(5)

        # Construct each widget
        body_widget = self._build_body()
        topbar_widget = self._build_topbar()

        root.addWidget(topbar_widget)
        root.addWidget(make_hline())
        root.addWidget(body_widget, stretch=1)

    def _build_topbar(self) -> QWidget:
        topbar = QWidget()
        topbar.setStyleSheet(topbar_panel())

        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(12, 0, 16, 0)
        tb.setSpacing(10)

        self.back_btn = QPushButton("Volver")
        self.back_btn.setStyleSheet(btn_ghost())
        self.back_btn.setFixedHeight(28)
        tb.addWidget(self.back_btn)
        self.back_btn.setIcon(icon("navigation/left.png"))
        tb.addWidget(make_vline())

        self.breadcrumb_label = QLabel("")
        self.breadcrumb_label.setStyleSheet(text_breadcrumb())
        tb.addWidget(self.breadcrumb_label)
        tb.addStretch()

        # Optional extra topbar widgets injected by subclass
        self._populate_topbar_extras(tb)

        self.position_label = QLabel("")
        self.position_label.setStyleSheet(
            f"font-size: {AppTheme.FONT_SM}; color: {AppTheme.TEXT_SECONDARY}; "
            f"background-color: {AppTheme.BG_APP}; padding: 2px 10px; "
            f"border-radius: 10px;"
        )
        tb.addWidget(self.position_label)
        tb.addSpacing(4)

        self.prev_btn = QPushButton("")
        self.prev_btn.setStyleSheet(btn_ghost())
        self.prev_btn.setFixedSize(36, 26)
        self.prev_btn.setIcon(icon("navigation/left.png"))
        self.prev_btn.setIconSize(QSize(*ICON_SIZE))
        tb.addWidget(self.prev_btn)

        self.next_btn = QPushButton("")
        self.next_btn.setStyleSheet(btn_primary_sm())
        self.next_btn.setFixedSize(36, 26)
        self.next_btn.setIcon(icon("navigation/right.png"))
        self.next_btn.setIconSize(QSize(*ICON_SIZE))
        tb.addWidget(self.next_btn)

        return topbar

    def _build_body(self) -> QWidget:
        body = QWidget()
        layout = QHBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self.build_media_area(), stretch=1)
        layout.addWidget(make_vline())
        layout.addWidget(self._build_right_panel())

        return body

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        panel.setFixedWidth(230)
        panel.setStyleSheet(f"background-color: {AppTheme.BG_PANEL};")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_info_strip())
        layout.addWidget(make_hline())

        label_area = QWidget()
        label_area.setStyleSheet(f"background-color: {AppTheme.BG_PANEL};")

        la = QVBoxLayout(label_area)
        la.setContentsMargins(14, 10, 14, 0)
        la.setSpacing(0)

        self.label_panel = LabelPanel(self.available_labels)
        la.addWidget(self.label_panel, stretch=1)
        layout.addWidget(label_area, stretch=1)

        layout.addWidget(make_hline())
        layout.addWidget(self._build_action_strip())

        return panel

    def _build_info_strip(self) -> QWidget:
        strip = QWidget()
        strip.setStyleSheet(info_strip())

        info = QVBoxLayout(strip)
        info.setContentsMargins(14, 10, 14, 10)
        info.setSpacing(6)

        # Status row
        status_row = QHBoxLayout()
        lbl = QLabel("ESTADO")
        lbl.setStyleSheet(text_section_header())

        self.status_chip = QLabel("Sin etiquetar")
        self.status_chip.setStyleSheet(chip_unlabeled())
        self.status_chip.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        status_row.addWidget(lbl)
        status_row.addStretch()
        status_row.addWidget(self.status_chip)
        info.addLayout(status_row)

        # ID row - always present
        id_row = QHBoxLayout()
        id_key = QLabel("ID")
        id_key.setStyleSheet(text_section_header())
        self.id_label = QLabel("-")
        self.id_label.setStyleSheet(
            f"font-size: {AppTheme.FONT_SM}; font-weight: bold; color: {AppTheme.TEXT_PRIMARY};"
        )
        self.id_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        id_row.addWidget(id_key)
        id_row.addStretch()
        id_row.addWidget(self.id_label)
        info.addLayout(id_row)

        # Type specific rows injected by subclass
        self.build_info_rows(info)

        return strip

    def _build_action_strip(self) -> QWidget:
        strip = QWidget()
        strip.setStyleSheet(f"background-color: {AppTheme.BG_PANEL};")
        al = QVBoxLayout(strip)
        al.setContentsMargins(14, 8, 14, 10)

        self.delete_label_btn = QPushButton("Eliminar etiqueta")
        self.delete_label_btn.setStyleSheet(btn_danger())
        self.delete_label_btn.setIcon(icon("delete.png"))
        self.delete_label_btn.setIconSize(QSize(*ICON_SIZE))
        self.delete_label_btn.setEnabled(False)
        al.addWidget(self.delete_label_btn)

        return strip

    # --------------------------------------
    # Signal wiring (base)
    # --------------------------------------
    def _connect_base_signals(self) -> None:
        # Return to project browser view
        self.back_btn.clicked.connect(self._on_back_clicked)

        # Navigation buttons
        self.prev_btn.clicked.connect(self._on_prev_clicked)
        self.next_btn.clicked.connect(self._on_next_clicked)

        # Label management
        self.delete_label_btn.clicked.connect(self._on_delete_clicked)
        self.label_panel.label_assigned.connect(self._on_label_assigned)

    # --------------------------------------
    # Keyboard shortcuts
    # --------------------------------------

    def _setup_shortcuts(self) -> None:
        # Helpers
        def _action(shortcut: str, slot) -> None:
            """Create an action scoped for this widget subtree"""
            act = QAction(self)
            act.setShortcut(shortcut)

            act.setShortcutContext(Qt.WidgetWithChildrenShortcut)
            act.triggered.connect(slot)
            self.addAction(act)

        # Navigation
        _action("Left", self._on_prev_clicked)
        _action("Right", self._on_next_clicked)
        _action("Escape", self._on_back_clicked)

        # Subclass specific shortcuts (Space for video/audio)
        self._setup_extra_shortcuts(_action)

        self._register_label_shortcuts()
        self.label_panel.label_list.installEventFilter(self)
        self.label_panel.label_list.viewport().installEventFilter(self)

    def _register_label_shortcuts(self) -> None:
        for act in self.actions():
            if getattr(act, "_is_label_shortcut", False):
                self.removeAction(act)

        # Label assignation shortcuts
        for i in range(min(9, len(self.available_labels))):
            act = QAction(self)
            act.setShortcut(str(i + 1))
            act.setShortcutContext(Qt.WidgetWithChildrenShortcut)
            act.triggered.connect(lambda checked=False, idx=i: self._assign_label_by_index(idx))
            act._is_label_shortcut = True
            self.addAction(act)

    def eventFilter(self, watched, event: QEvent) -> bool:  # noqa: N802
        """
        Intercepts keys that QListWidget before QAction shortcuts fire
        """

        if event.type() == QEvent.KeyPress:
            key = event.key()

            if self._handle_extra_key(key):
                return True

            if key == Qt.Key_Delete:
                self._on_delete_clicked()
                return True

            if key == Qt.Key_Right:
                self._on_next_clicked()
                return True

            if key == Qt.Key_Escape:
                self._on_back_clicked()
                return True

            if Qt.Key_1 <= key <= Qt.Key_9:
                self._assign_label_by_index(key - Qt.Key_1)
                return True

        return super().eventFilter(watched, event)

    # --------------------------------------
    # Command Handlers
    # --------------------------------------

    def _on_label_assigned(self, label: str) -> None:
        if not self._current_item:
            return

        try:
            self._labeling_service.assign_label(self._current_item, self._current_project, label)
            self._has_unsaved_changes = True
            self._schedule_auto_save()
            self._update_item_status()
            self.item_labeled.emit(self._current_item)

        except ValueError as e:
            QMessageBox.warning(self, "No se pudo etiquetar", str(e))

        finally:
            self.focus_label_list()

    def _on_prev_clicked(self) -> None:
        if not self._current_item:
            return
        self._force_save()
        if not self._current_item.is_labeled() and self._ask_skip() == QMessageBox.No:
            return
        self.prev_requested.emit()

    def _on_next_clicked(self) -> None:
        if not self._current_item:
            return
        self._force_save()
        if not self._current_item.is_labeled() and self._ask_skip() == QMessageBox.No:
            return
        self.next_requested.emit()

    def _on_delete_clicked(self) -> None:
        if not self._current_item or not self._current_item.is_labeled():
            return
        try:
            self._labeling_service.clear_label(self._current_item, self._current_project)
            self._has_unsaved_changes = True
            self._schedule_auto_save()
            self._update_item_status()
            self.item_labeled.emit(self._current_item)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

        finally:
            self.focus_label_list()

    def _on_back_clicked(self) -> None:
        self._on_before_back()
        self._force_save()
        if self._current_item and not self._current_item.is_labeled():
            noun = self.item_type_label()
            reply = QMessageBox.question(
                self,
                f"{noun.capitalize()} sin etiquetar",
                f"Este {noun} no tiene etiqueta. ¿Seguro que deseas regresar?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return
        self.back_requested.emit()

    def _assign_label_by_index(self, index: int) -> None:
        if 0 <= index < len(self.available_labels):
            self._on_label_assigned(self.available_labels[index])

    def _ask_skip(self) -> int:
        noun = self.item_type_label()
        return QMessageBox.question(
            self,
            f"{noun.capitalize()} sin etiquetar",
            f"Este {noun} aún no tiene etiqueta. ¿Deseas saltarlo?",
            QMessageBox.Yes | QMessageBox.No,
        )

    # --------------------------------------
    # Auto-Save Project
    # --------------------------------------

    def _schedule_auto_save(self) -> None:
        if self._current_project and self._current_project.get_save_path():
            self._auto_save_timer.stop()
            self._auto_save_timer.start(self._auto_save_delay_ms)

    def _auto_save_project(self) -> None:
        if not self._current_project:
            return
        try:
            if self._project_service.auto_save_project(self._current_project):
                self._has_unsaved_changes = False
                self.auto_saved.emit()

        except Exception as e:
            print(f"Auto-save failed {e}")

    def _force_save(self) -> None:
        if self._has_unsaved_changes and self._current_project:
            self._auto_save_timer.stop()
            self._auto_save_project()

    # --------------------------------------
    # Public API
    # --------------------------------------

    def load_item(self, item: MediaItem, project: Project) -> None:
        """
        Load item into viewer
        Updates all shared UI, then delegates to on_item_loaded()
        """
        self._current_item = item
        self._current_project = project

        self._update_breadcrumb()
        self._update_item_status()
        self._update_position_display()
        self.label_panel.set_enabled(True)

        self.on_item_loaded(item, project)

    def set_navigation_service(self, nav: NavigationService) -> None:
        self._navigation_service = nav
        self._update_position_display()

    def get_current_item(self) -> MediaItem | None:
        return self._current_item

    def reset(self) -> None:
        """
        Clear all project related state
        """

        self._auto_save_timer.stop()
        self._force_save()
        self.on_reset()

        # Clean class attributes
        self._current_item = None
        self._current_project = None
        self._navigation_service = None
        self._has_unsaved_changes = False

        # Clean UI
        self.label_panel.set_enabled(False)
        self.label_panel.clear_selection()
        self._clear_display()

    def stop(self) -> None:
        """Stop any active media playback"""

    def focus_label_list(self) -> None:
        self.label_panel.label_list.setFocus()

    def update_labels(self, labels: list) -> None:
        if not labels:
            return
        self.available_labels = labels.copy()
        self.label_panel.set_labels(labels)
        self._register_label_shortcuts()

    # --------------------------------------
    # Private UI updaters
    # --------------------------------------

    def _update_breadcrumb(self) -> None:
        if not self._current_item:
            self._clear_display()
            return
        name = self._current_item.get_filename()
        project_name = self._current_project.name if self._current_project else ""
        if project_name:
            self.breadcrumb_label.setText(
                f'<span style="color:{AppTheme.TEXT_MUTED}">{project_name} /</span> '
                f'<span style="color:{AppTheme.TEXT_PRIMARY}; font-weight:600">{name}</span>'
            )
        else:
            self.breadcrumb_label.setText(name)
        self.id_label.setText(self._current_item.item_id)

    def _update_item_status(self) -> None:
        if not self._current_item:
            return
        labeled = self._current_item.is_labeled()
        if labeled:
            self.status_chip.setText(f"✓  {self._current_item.label}")
            self.status_chip.setStyleSheet(chip_labeled())
        else:
            self.status_chip.setText("Sin etiquetar")
            self.status_chip.setStyleSheet(chip_unlabeled())
        self.label_panel.set_current_label(self._current_item.label if labeled else None)
        self.delete_label_btn.setEnabled(labeled)

    def _update_position_display(self) -> None:
        if self._navigation_service:
            current, total = self._navigation_service.get_position()
            self.position_label.setText(f"{current} / {total}")
            self.position_label.setVisible(True)
        else:
            self.position_label.setVisible(False)

    def _clear_display(self) -> None:
        self.breadcrumb_label.setText("")
        self.id_label.setText("—")
        self.status_chip.setText("Sin etiquetar")
        self.status_chip.setStyleSheet(chip_unlabeled())
        self.position_label.setVisible(False)
        self.delete_label_btn.setEnabled(False)

    # --------------------------------------
    # Convenience
    # --------------------------------------

    @staticmethod
    def _info_row(key: str, value_attr: str, info_layout: QVBoxLayout) -> QLabel:
        """
        Build and add standard key/value row to info_layout
        Returns the value QLabel so the subclass can update it
        """

        row = QHBoxLayout()
        key_lbl = QLabel(key)
        key_lbl.setStyleSheet(text_section_header())

        val_lbl = QLabel(value_attr)
        val_lbl.setStyleSheet(f"font-size: {AppTheme.FONT_SM}; color: {AppTheme.TEXT_SECONDARY};")
        val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        row.addWidget(key_lbl)
        row.addStretch()
        row.addWidget(val_lbl)
        info_layout.addLayout(row)

        return val_lbl
