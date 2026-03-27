from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QAction

from src.ui.widgets.video_player import VideoPlayer
from src.ui.widgets.label_panel import LabelPanel
from src.ui.widgets.label_panel import DEFAULT_LABELS

from src.application.services.labeling_service import LabelingService
from src.application.services.navigation_service import NavigationService
from src.application.services.project_service import ProjectService

from src.domain.models.project import Project
from src.domain.models.fragment import Fragment

from src.ui.helpers.dividers import make_hline, make_vline
from src.ui.styles import (
    AppTheme,
    topbar_panel,
    btn_primary_sm, btn_ghost, btn_danger,
    chip_labeled, chip_unlabeled,
    text_breadcrumb, text_section_header
)


class FragmentViewer(QWidget):
    """
    Fragment viewer — UI presentation only.
    Business logic delegated to services (SRP + DIP).
    """

    fragment_labeled = Signal(Fragment)
    prev_requested   = Signal()
    next_requested   = Signal()
    back_requested   = Signal()

    def __init__(
        self,
        labeling_service: LabelingService,
        project_service: ProjectService,
        available_labels: list = None,
        parent=None
    ):
        super().__init__(parent)

        self._labeling_service    = labeling_service
        self._project_service     = project_service
        self._navigation_service  = None

        self._current_fragment: Fragment = None
        self._current_project:  Project  = None

        self.available_labels = (available_labels or DEFAULT_LABELS).copy()

        # Auto-save
        self._auto_save_timer = QTimer()
        self._auto_save_timer.setSingleShot(True)
        self._auto_save_timer.timeout.connect(self._auto_save_project)
        self._auto_save_delay_ms  = 3000
        self._has_unsaved_changes = False

        self._init_ui()
        self._connect_signals()
        self._setup_shortcuts()

    # ─────────────────────────────────────────────
    # UI construction
    # ─────────────────────────────────────────────

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top bar ───────────────────────────────
        topbar = QWidget()
        topbar.setFixedHeight(48)
        topbar.setStyleSheet(topbar_panel())
        topbar_layout = QHBoxLayout(topbar)
        topbar_layout.setContentsMargins(12, 0, 16, 0)
        topbar_layout.setSpacing(10)

        self.back_btn = QPushButton("← Volver")
        self.back_btn.setStyleSheet(btn_ghost())
        self.back_btn.setFixedHeight(30)
        topbar_layout.addWidget(self.back_btn)

        topbar_layout.addWidget(make_vline())

        # Breadcrumb: "project / filename"
        self.breadcrumb_label = QLabel("")
        self.breadcrumb_label.setStyleSheet(text_breadcrumb())
        topbar_layout.addWidget(self.breadcrumb_label)

        topbar_layout.addStretch()

        self.position_label = QLabel("")
        self.position_label.setStyleSheet(
            f"font-size: {AppTheme.FONT_SM}; color: {AppTheme.TEXT_SECONDARY}; "
            f"background-color: {AppTheme.BG_APP}; padding: 2px 10px; "
            f"border-radius: 10px;"
        )
        topbar_layout.addWidget(self.position_label)

        topbar_layout.addSpacing(4)

        self.prev_btn = QPushButton("←")
        self.prev_btn.setStyleSheet(btn_ghost())
        self.prev_btn.setFixedSize(40, 30)
        topbar_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("→")
        self.next_btn.setStyleSheet(btn_primary_sm())
        self.next_btn.setFixedSize(40, 30)
        topbar_layout.addWidget(self.next_btn)

        root.addWidget(topbar)
        root.addWidget(make_hline())

        # ── Body ──────────────────────────────────
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # ── Video area ────────────────────────────
        video_area = QWidget()
        video_area.setStyleSheet(f"background-color: {AppTheme.BG_APP};")
        video_layout = QVBoxLayout(video_area)
        video_layout.setContentsMargins(12, 12, 12, 12)
        video_layout.setSpacing(8)

        self.video_player = VideoPlayer()
        video_layout.addWidget(self.video_player, stretch=1)

        body_layout.addWidget(video_area, stretch=1)
        body_layout.addWidget(make_vline())

        # ── Right panel ───────────────────────────
        right_panel = QWidget()
        right_panel.setFixedWidth(230)
        right_panel.setStyleSheet(f"background-color: {AppTheme.BG_PANEL};")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Info strip
        info_strip = QWidget()
        info_strip.setStyleSheet(
            f"background-color: {AppTheme.BG_PANEL}; "
            f"border-bottom: 1px solid {AppTheme.BG_APP};"
        )
        info_layout = QVBoxLayout(info_strip)
        info_layout.setContentsMargins(14, 10, 14, 10)
        info_layout.setSpacing(6)

        # Status row
        status_row = QHBoxLayout()
        status_lbl = QLabel("ESTADO")
        status_lbl.setStyleSheet(text_section_header())
        self.status_chip = QLabel("Sin etiquetar")
        self.status_chip.setStyleSheet(chip_unlabeled())
        self.status_chip.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        status_row.addWidget(status_lbl)
        status_row.addStretch()
        status_row.addWidget(self.status_chip)
        info_layout.addLayout(status_row)

        # ID row
        id_row = QHBoxLayout()
        id_key = QLabel("ID")
        id_key.setStyleSheet(text_section_header())
        self.id_label = QLabel("—")
        self.id_label.setStyleSheet(
            f"font-size: {AppTheme.FONT_SM}; font-weight: bold; "
            f"color: {AppTheme.TEXT_PRIMARY};"
        )
        self.id_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        id_row.addWidget(id_key)
        id_row.addStretch()
        id_row.addWidget(self.id_label)
        info_layout.addLayout(id_row)

        right_layout.addWidget(info_strip)
        right_layout.addWidget(make_hline())

        # Label picker — fills remaining space
        label_area = QWidget()
        label_area.setStyleSheet(f"background-color: {AppTheme.BG_PANEL};")
        label_layout = QVBoxLayout(label_area)
        label_layout.setContentsMargins(14, 10, 14, 0)
        label_layout.setSpacing(0)

        self.label_panel = LabelPanel(self.available_labels)
        label_layout.addWidget(self.label_panel, stretch=1)

        right_layout.addWidget(label_area, stretch=1)

        # Delete action strip — bottom, understated
        right_layout.addWidget(make_hline())
        action_strip = QWidget()
        action_strip.setStyleSheet(f"background-color: {AppTheme.BG_PANEL};")
        action_layout = QVBoxLayout(action_strip)
        action_layout.setContentsMargins(14, 8, 14, 10)

        self.delete_label_btn = QPushButton("Eliminar etiqueta actual")
        self.delete_label_btn.setStyleSheet(btn_danger())
        self.delete_label_btn.setEnabled(False)
        action_layout.addWidget(self.delete_label_btn)

        right_layout.addWidget(action_strip)

        body_layout.addWidget(right_panel)
        root.addWidget(body, stretch=1)

    # ─────────────────────────────────────────────
    # Signal wring
    # ─────────────────────────────────────────────

    def _connect_signals(self):
        # Return to project browser view
        self.back_btn.clicked.connect(self._on_back_clicked)
        
        # Navigation buttons
        self.prev_btn.clicked.connect(self._on_prev_clicked)
        self.next_btn.clicked.connect(self._on_next_clicked)
        
        # Label management
        self.delete_label_btn.clicked.connect(self._on_delete_clicked)
        self.label_panel.label_assigned.connect(self._on_label_assigned)
        
        # Video player
        self.video_player.ready.connect(self._on_video_ready_for_fragment)
        self.video_player.load_failed.connect(self._on_video_load_failed)
        
    # ─────────────────────────────────────────────
    # Keyboard shortcuts
    # ─────────────────────────────────────────────

    def _setup_shortcuts(self):
        # Navigation
        prev_action = QAction(self)
        prev_action.setShortcut("Left")
        prev_action.triggered.connect(self._on_prev_clicked)
        self.addAction(prev_action)
        
        next_action = QAction(self)
        next_action.setShortcut("Right")
        next_action.triggered.connect(self._on_next_clicked)
        self.addAction(next_action)
        
        # Back to Project browser
        back_action = QAction(self)
        back_action.setShortcut("Escape")
        back_action.triggered.connect(self._on_back_clicked)
        self.addAction(back_action)
        
        # Delete label
        delete_action = QAction(self)
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(self._on_delete_clicked)
        self.addAction(delete_action)
        
        # Play and pause action
        play_pause_action = QAction(self)
        play_pause_action.setShortcut("Space")
        play_pause_action.triggered.connect(self.video_player.toggle_playback)
        self.addAction(play_pause_action)
        
        # Label shortcuts
        for i in range(min(9, len(self.available_labels))):
            label_action = QAction(self)
            label_action.setShortcut(str(i + 1))
            label_action.triggered.connect(lambda checked=False, idx=i: self._assign_label_by_index(idx))
            self.addAction(label_action)

    # ─────────────────────────────────────────────
    # Command handlers
    # ─────────────────────────────────────────────

    def _on_label_assigned(self, label: str):
        if not self._current_fragment:
            return
        try:
            self._labeling_service.assign_label(self._current_fragment, self._current_project, label)
            self._has_unsaved_changes = True
            self._schedule_auto_save()
            self._update_fragment_status()
            self.fragment_labeled.emit(self._current_fragment)
        except ValueError as e:
            self._show_error("No se pudo etiquetar", str(e))

    def _on_prev_clicked(self):
        if not self._current_fragment:
            return
        self._force_save()
        if not self._current_fragment.is_labeled():
            reply = QMessageBox.question(
                self, "Fragmento sin etiquetar",
                "Este fragmento aún no tiene etiqueta. ¿Deseas saltarlo?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        self.prev_requested.emit()

    def _on_next_clicked(self):
        if not self._current_fragment:
            return
        self._force_save()
        if not self._current_fragment.is_labeled():
            reply = QMessageBox.question(
                self, "Fragmento sin etiquetar",
                "Este fragmento aún no tiene etiqueta. ¿Deseas saltarlo?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        self.next_requested.emit()

    def _on_delete_clicked(self):
        if not self._current_fragment or not self._current_fragment.is_labeled():
            return
        try:
            self._labeling_service.clear_label(self._current_fragment, self._current_project)
            self._has_unsaved_changes = True
            self._schedule_auto_save()
            self._update_fragment_status()
            self.fragment_labeled.emit(self._current_fragment)
        except Exception as e:
            self._show_error("Error", str(e))

    def _on_back_clicked(self):
        self.video_player.force_stop()
        self._force_save()
        if self._current_fragment and not self._current_fragment.is_labeled():
            reply = QMessageBox.question(
                self, "Fragmento sin etiquetar",
                "Este fragmento no tiene etiqueta. ¿Seguro que deseas regresar?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        self.back_requested.emit()
        
    def _assign_label_by_index(self, index: int):
        if not self._current_fragment or not self._current_project:
            return
        if index < 0 or index >= len(self.available_labels):
            return
        label = self.available_labels[index]
        self._on_label_assigned(label)

    # ─────────────────────────────────────────────
    # Auto-save
    # ─────────────────────────────────────────────

    def _schedule_auto_save(self):
        if self._current_project and self._current_project.get_save_path():
            self._auto_save_timer.stop()
            self._auto_save_timer.start(self._auto_save_delay_ms)

    def _auto_save_project(self):
        if not self._current_project:
            return
        try:
            success = self._project_service.auto_save_project(self._current_project)
            if success:
                self._has_unsaved_changes = False
        except Exception as e:
            print(f"Auto-save failed: {e}")

    def _force_save(self):
        if self._has_unsaved_changes and self._current_project:
            self._auto_save_timer.stop()
            self._auto_save_project()

    # ─────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────

    def load_fragment(self, fragment: Fragment, project: Project = None):
        self._current_fragment = fragment
        self._current_project  = project

        if not Path(fragment.video_path).exists():
            self._show_error(
                "Archivo no encontrado",
                f"No se encontró el archivo de video:\n{fragment.video_path}"
            )
            return

        self.video_player.load_video(fragment.video_path)

        self._update_breadcrumb()
        self._update_fragment_status()
        self._update_position_display()
        self.label_panel.set_enabled(True)

    def set_navigation_service(self, navigation_service: NavigationService):
        self._navigation_service = navigation_service
        self._update_position_display()

    def get_current_fragment(self) -> Fragment:
        return self._current_fragment

    # ─────────────────────────────────────────────
    # Private UI updaters
    # ─────────────────────────────────────────────

    def _on_video_ready_for_fragment(self):
        if self._current_fragment:
            pos = int(self._current_fragment.start_time * 1000)
            QTimer.singleShot(50, lambda: self.video_player.seek_position(pos))
            
    def _on_video_load_failed(self, msg: str):
        QMessageBox.critical(self, "Error al cargar video", msg)

    def _update_breadcrumb(self):
        """Show  project / filename  in the top bar — single source for both."""
        if not self._current_fragment:
            self.breadcrumb_label.setText("")
            self.id_label.setText("—")
            return

        video_name = self._current_fragment.get_video_name()
        project_name = self._current_project.name if self._current_project else ""

        if project_name:
            # Use HTML to style the separator and filename differently
            self.breadcrumb_label.setText(
                f'<span style="color:{AppTheme.TEXT_MUTED}">{project_name} /</span> '
                f'<span style="color:{AppTheme.TEXT_PRIMARY}; font-weight:600">{video_name}</span>'
            )
        else:
            self.breadcrumb_label.setText(video_name)

        self.id_label.setText(self._current_fragment.fragment_id)

    def _update_fragment_status(self):
        """Single source of truth for all status-dependent UI state."""
        if not self._current_fragment:
            return

        labeled = self._current_fragment.is_labeled()

        # Status chip
        if labeled:
            self.status_chip.setText(f"✓  {self._current_fragment.label}")
            self.status_chip.setStyleSheet(chip_labeled())
        else:
            self.status_chip.setText("Sin etiquetar")
            self.status_chip.setStyleSheet(chip_unlabeled())

        # Label panel reflection
        self.label_panel.set_current_label(
            self._current_fragment.label if labeled else None
        )

        # Delete link
        self.delete_label_btn.setEnabled(labeled)

    def _update_position_display(self):
        if self._navigation_service:
            current, total = self._navigation_service.get_position()
            self.position_label.setText(f"{current} / {total}")
            self.position_label.setVisible(True)
        else:
            self.position_label.setVisible(False)

    def _show_error(self, title: str, message: str):
        QMessageBox.critical(self, title, message)