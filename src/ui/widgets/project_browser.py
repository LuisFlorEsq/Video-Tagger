from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTreeWidget, QTreeWidgetItem,
    QLabel, QFileDialog, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QAction

from src.application.services.project_service import ProjectService
from src.application.services.export_service import ExportService

from src.domain.models.project import Project
from src.domain.models.fragment import Fragment

from src.ui.helpers.dividers import make_hline, make_vline
from src.ui.helpers.project_formatter import (
    format_project_badge,
    format_project_stats
)
from src.ui.styles import (
    AppTheme,
    sidebar_panel, sidebar_btn, sidebar_btn_active, sidebar_btn_warning,
    sidebar_section_label, topbar_panel, progress_bar, btn_primary, btn_success,
    fragment_list, chip_labeled, chip_unlabeled, chip_warning, chip_info,
    text_title, text_secondary, text_muted, text_breadcrumb, divider,
    text_section_header,
)

class ProjectBrowser(QWidget):
    """
    Project browser widget — UI presentation only.
    Business logic delegated to ProjectService (SRP + DIP).
    """

    project_loaded = Signal(Project)
    fragment_selected = Signal(Fragment)
    project_closed = Signal()

    def __init__(
        self,
        project_service: ProjectService,
        export_service: ExportService,
        parent=None
    ):
        super().__init__(parent)
        self._project_service = project_service
        self._export_service = export_service
        self._current_project: Project = None

        self._init_ui()
        self._connect_signals()
        self._setup_shortcuts() 
        self._update_view()

    # ─────────────────────────────────────────────
    # UI construction
    # ─────────────────────────────────────────────

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top bar ──────────────────────────────
        self.topbar = QWidget()
        self.topbar.setFixedHeight(48)
        self.topbar.setStyleSheet(topbar_panel())
        topbar_layout = QHBoxLayout(self.topbar)
        topbar_layout.setContentsMargins(16, 0, 16, 0)
        topbar_layout.setSpacing(5)

        app_title = QLabel("Herramienta de etiquetado")
        app_title.setStyleSheet(
            f"font-size: {AppTheme.FONT_LG}; font-weight: bold; color: {AppTheme.TEXT_PRIMARY};"
        )
        topbar_layout.addWidget(app_title)

        self._topbar_sep = make_vline()
        topbar_layout.addWidget(self._topbar_sep)

        self.topbar_project_label = QLabel("")
        self.topbar_project_label.setStyleSheet(text_breadcrumb())
        self.topbar_project_label.setVisible(False)
        topbar_layout.addWidget(self.topbar_project_label)

        topbar_layout.addStretch()

        self.sync_badge = QLabel("")
        self.sync_badge.setStyleSheet(chip_warning())
        self.sync_badge.setVisible(False)
        topbar_layout.addWidget(self.sync_badge)

        self.progress_badge = QLabel("")
        self.progress_badge.setStyleSheet(chip_info())
        self.progress_badge.setVisible(False)
        topbar_layout.addWidget(self.progress_badge)

        root.addWidget(self.topbar)

        # ── Thin divider ─────────────────────────
        # root.addWidget(self._make_hline())

        # ── Body (sidebar + main) ─────────────────
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # ── Sidebar ───────────────────────────────
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(210)
        self.sidebar.setStyleSheet(sidebar_panel())
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(10, 12, 10, 12)
        sidebar_layout.setSpacing(2)

        # Welcome state — new/open buttons
        self.welcome_section = QWidget()
        ws_layout = QVBoxLayout(self.welcome_section)
        ws_layout.setContentsMargins(0, 0, 0, 0)
        ws_layout.setSpacing(2)

        ws_header = QLabel("Inicio")
        ws_header.setStyleSheet(sidebar_section_label())
        ws_layout.addWidget(ws_header)

        self.new_project_btn = QPushButton("Nuevo proyecto")
        self.new_project_btn.setStyleSheet(sidebar_btn())
        self.new_project_btn.setMinimumHeight(36)
        ws_layout.addWidget(self.new_project_btn)

        self.load_project_btn = QPushButton("Abrir proyecto")
        self.load_project_btn.setStyleSheet(sidebar_btn())
        self.load_project_btn.setMinimumHeight(36)
        ws_layout.addWidget(self.load_project_btn)

        sidebar_layout.addWidget(self.welcome_section)

        # Project state — actions when project is loaded
        self.project_section = QWidget()
        self.project_section.setVisible(False)
        ps_layout = QVBoxLayout(self.project_section)
        ps_layout.setContentsMargins(0, 0, 0, 0)
        ps_layout.setSpacing(2)

        ps_header = QLabel("Proyecto")
        ps_header.setStyleSheet(sidebar_section_label())
        ps_layout.addWidget(ps_header)

        self.save_project_btn = QPushButton("Guardar")
        self.save_project_btn.setStyleSheet(sidebar_btn())
        self.save_project_btn.setMinimumHeight(34)
        ps_layout.addWidget(self.save_project_btn)

        self.export_csv_btn = QPushButton("Exportar CSV")
        self.export_csv_btn.setStyleSheet(sidebar_btn())
        self.export_csv_btn.setMinimumHeight(34)
        ps_layout.addWidget(self.export_csv_btn)

        ps_layout.addWidget(make_hline())

        actions_header = QLabel("Sincronización")
        actions_header.setStyleSheet(sidebar_section_label())
        ps_layout.addWidget(actions_header)

        self.sync_btn = QPushButton("Sincronizar videos")
        self.sync_btn.setStyleSheet(sidebar_btn_warning())
        self.sync_btn.setMinimumHeight(34)
        self.sync_btn.setEnabled(False)
        ps_layout.addWidget(self.sync_btn)

        ps_layout.addSpacing(8)
        ps_layout.addWidget(make_hline())

        self.back_btn = QPushButton("Cerrar proyecto")
        self.back_btn.setStyleSheet(sidebar_btn())
        self.back_btn.setMinimumHeight(34)
        ps_layout.addWidget(self.back_btn)

        sidebar_layout.addWidget(self.project_section)
        sidebar_layout.addStretch()

        body_layout.addWidget(self.sidebar)
        # body_layout.addWidget(self._make_vline())

        # ── Main panel ────────────────────────────
        self.main_panel = QWidget()
        main_layout = QVBoxLayout(self.main_panel)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Welcome screen (no project)
        self.welcome_screen = QWidget()
        welcome_layout = QVBoxLayout(self.welcome_screen)
        welcome_layout.setAlignment(Qt.AlignCenter)

        welcome_title = QLabel("Bienvenido")
        welcome_title.setStyleSheet(text_title())
        welcome_title.setAlignment(Qt.AlignCenter)

        welcome_sub = QLabel(
            "Crea un nuevo proyecto seleccionando una carpeta con videos,\n"
            "o abre un proyecto existente para continuar etiquetando."
        )
        welcome_sub.setStyleSheet(text_secondary())
        welcome_sub.setAlignment(Qt.AlignCenter)
        welcome_sub.setWordWrap(True)

        welcome_layout.addStretch()
        welcome_layout.addWidget(welcome_title)
        welcome_layout.addSpacing(8)
        welcome_layout.addWidget(welcome_sub)
        welcome_layout.addStretch()

        main_layout.addWidget(self.welcome_screen)

        # Fragment list screen (project loaded)
        self.list_screen = QWidget()
        self.list_screen.setVisible(False)
        list_layout = QVBoxLayout(self.list_screen)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(0)

        # Toolbar row: filters + count
        toolbar = QWidget()
        toolbar.setFixedHeight(40)
        toolbar.setStyleSheet(
            f"background-color: {AppTheme.BG_PANEL}; "
            f"border-bottom: 1px solid {AppTheme.BORDER};"
        )
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(14, 0, 14, 0)
        toolbar_layout.setSpacing(8)

        self.fragment_count_label = QLabel("")
        self.fragment_count_label.setStyleSheet(text_muted())
        toolbar_layout.addWidget(self.fragment_count_label)
        toolbar_layout.addStretch()

        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet(text_secondary())
        toolbar_layout.addWidget(self.stats_label)

        list_layout.addWidget(toolbar)

        # Progress bar (real Qt widget)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)

        self.progress_bar.setStyleSheet(progress_bar())

        list_layout.addWidget(self.progress_bar)

        # Fragment list
        self.fragment_list = QTreeWidget()
        self.fragment_list.setColumnCount(3)
        self.fragment_list.setHeaderLabels(["Video", "Etiqueta", "ID"])

        self.fragment_list.setRootIsDecorated(False)
        self.fragment_list.setAlternatingRowColors(True)
        self.fragment_list.setItemsExpandable(False)

        self.fragment_list.setStyleSheet(fragment_list())
        self.fragment_list.setIndentation(0)

        # Column sizes
        self.fragment_list.setColumnWidth(0, 500)
        self.fragment_list.setColumnWidth(1, 120)
        self.fragment_list.setColumnWidth(2, 200)

        list_layout.addWidget(self.fragment_list)
        main_layout.addWidget(self.list_screen)
        body_layout.addWidget(self.main_panel)

        root.addWidget(body, stretch=1)

    # ─────────────────────────────────────────────
    # Signal wiring
    # ─────────────────────────────────────────────

    def _connect_signals(self):
        # Project selection
        self.new_project_btn.clicked.connect(self._on_new_project_clicked)
        self.load_project_btn.clicked.connect(self._on_load_project_clicked)
        
        # Project management
        self.save_project_btn.clicked.connect(self._on_save_clicked)
        self.export_csv_btn.clicked.connect(self._on_export_csv_clicked)
        
        # Sync new videos and return to main window
        self.sync_btn.clicked.connect(self._on_sync_clicked)
        self.back_btn.clicked.connect(self._on_back_clicked)
        
        # Switch to fragment viewer (with the fragment selected)
        self.fragment_list.itemActivated.connect(self._on_fragment_selected)
        
    # ─────────────────────────────────────────────
    # Keyboard shortcuts
    # ─────────────────────────────────────────────

    def _setup_shortcuts(self):
        # Sync videos
        sync_action = QAction(self)
        sync_action.setShortcut("Ctrl+R")
        sync_action.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        sync_action.triggered.connect(self._on_sync_clicked)
        self.addAction(sync_action)

        # Close project
        close_action = QAction(self)
        close_action.setShortcut("Escape")
        close_action.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        close_action.triggered.connect(self._on_back_clicked)
        self.addAction(close_action)

    # ─────────────────────────────────────────────
    # Command handlers
    # ─────────────────────────────────────────────

    def _on_new_project_clicked(self):
        folder_path = self._select_folder()
        if not folder_path:
            return
        try:
            project = self._project_service.create_project_from_folder(folder_path)
            self._load_project(project)
            self.project_loaded.emit(project)
        except ValueError as e:
            self._show_error("Error al crear proyecto", str(e))
        except Exception as e:
            self._show_error("Error inesperado", f"No se pudo crear el proyecto:\n{str(e)}")

    def _on_load_project_clicked(self):
        file_path = self._select_project_file()
        if not file_path:
            return
        try:
            project = self._project_service.load_project(file_path)
            self._load_project(project)
            self.project_loaded.emit(project)
        except ValueError as e:
            self._show_error("No se pudo cargar el proyecto", str(e))
        except Exception as e:
            self._show_error("Error inesperado", f"No se pudo cargar el proyecto:\n{str(e)}")

    def _on_back_clicked(self):
        self._current_project = None
        self._reset_list_ui()
        self._update_view()
        self.project_closed.emit()

    def _on_save_clicked(self):
        if not self._current_project:
            return
        file_path = self._select_save_path(
            f"{self._current_project.name}.json",
            "JSON Files (*.json)"
        )
        if not file_path:
            return
        try:
            self._project_service.save_project(self._current_project, file_path)
            summary = self._project_service.get_project_summary(self._current_project)
            self._show_info(
                "Proyecto guardado",
                f"Guardado correctamente.\n\n"
                f"Progreso: {summary['labeled']}/{summary['total_fragments']} "
                f"({summary['progress_percentage']:.1f}%)"
            )
        except Exception as e:
            self._show_error("Error al guardar", str(e))

    def _on_export_csv_clicked(self):
        if not self._current_project:
            self._show_error("Sin proyecto", "No hay proyecto cargado para exportar.")
            return
        if self._current_project.get_total_count() == 0:
            self._show_error("Sin datos", "No hay fragmentos para exportar.")
            return
        file_path = self._select_save_path(
            f"{self._current_project.name}_export.csv",
            "CSV Files (*.csv);;All Files (*)"
        )
        if not file_path:
            return
        try:
            self._export_service.export(self._current_project, file_path, 'csv')
            summary = self._project_service.get_project_summary(self._current_project)
            self._show_info(
                "Exportación exitosa",
                f"{summary['total_fragments']} fragmentos exportados.\n"
                f"Etiquetados: {summary['labeled']}/{summary['total_fragments']}\n"
                f"Archivo: {file_path.name}"
            )
        except Exception as e:
            self._show_error("Error al exportar", f"No se pudo exportar a CSV:\n{str(e)}")

    def _on_sync_clicked(self):
        if not self._current_project:
            return
        new_videos = self._project_service.get_new_videos(self._current_project)
        if not new_videos:
            self._show_info("Sin cambios", "No hay videos nuevos para sincronizar.")
            return
        reply = QMessageBox.question(
            self,
            "Sincronizar videos",
            f"Se encontraron {len(new_videos)} videos nuevos.\n\n"
            f"¿Deseas agregarlos al proyecto?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                count = self._project_service.sync_new_videos(self._current_project, new_videos)
                self.refresh()
                self._show_info(
                    "Sincronización exitosa",
                    f"Se agregaron {count} videos nuevos al proyecto."
                )
            except Exception as e:
                self._show_error("Error al sincronizar", str(e))

    def _on_fragment_selected(self, item: QTreeWidgetItem):
        if not self._current_project:
            return
        
        fragment_id = item.data(0, Qt.UserRole)
        fragment = self._current_project.get_fragment(fragment_id)
        if fragment:
            self.fragment_selected.emit(fragment)

    # ─────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────

    def set_project(self, project: Project):
        self._load_project(project)

    def refresh(self):
        if self._current_project:
            
            selected_id = None
            current_item = self.fragment_list.currentItem()
            
            if current_item:
                selected_id = current_item.data(0, Qt.UserRole)
                
            self._populate_fragment_list()
            self._update_project_stats()
            self._check_for_new_videos()
            
            if selected_id:
                for i in range(self.fragment_list.topLevelItemCount()):
                    item = self.fragment_list.topLevelItem(i)
                    if item.data(0, Qt.UserRole) == selected_id:
                        self.fragment_list.setCurrentItem(item)
                        break
            elif self.fragment_list.topLevelItemCount() > 0:
                self.fragment_list.setCurrentItem(
                    self.fragment_list.topLevelItem(0)
                )
            
            self.fragment_list.setFocus()
        
    def get_current_project(self) -> Project:
        return self._current_project
    
    # ─────────────────────────────────────────────
    # Public API (Triggers from main_window)
    # ─────────────────────────────────────────────
    def trigger_new_project(self):
        """
        Public entry point, used each time a new project is requested 
        """
        self._on_new_project_clicked()
        
    def trigger_load_project(self):
        """
        Public entry point, used each time a project is loaded
        """
        self._on_load_project_clicked()
        
    def trigger_save_project(self):
        """
        Public entry point, used each time a project is prompted to save
        """
        self._on_save_clicked()
    
    def trigger_export_project(self):
        """
        Public entry point, used each time a project is prompted to export
        """
        self._on_export_csv_clicked()

    # ─────────────────────────────────────────────
    # Private helpers
    # ─────────────────────────────────────────────

    def _load_project(self, project: Project):
        self._current_project = project
        self._update_view()

    def _update_view(self):
        has_project = self._current_project is not None

        # Top bar
        self.topbar_project_label.setVisible(has_project)
        self._topbar_sep.setVisible(has_project)
        self.sync_badge.setVisible(False)
        self.progress_badge.setVisible(has_project)

        # Sidebar
        self.welcome_section.setVisible(not has_project)
        self.project_section.setVisible(has_project)

        # Main panel
        self.welcome_screen.setVisible(not has_project)
        self.list_screen.setVisible(has_project)

        if has_project:
            self.topbar_project_label.setText(self._current_project.name)
            self.refresh()
            
    def _reset_list_ui(self):
        self.fragment_list.clear()
        self.progress_bar.setValue(0)
        
        self.stats_label.setText("")
        self.fragment_count_label.setText("")
        
        self.sync_badge.setVisible(False)
        self.sync_btn.setEnabled(False)
        self.sync_btn.setText("Sincronizar videos")
        
        self.progress_badge.setVisible(False)
        

    def _check_for_new_videos(self):
        if not self._current_project:
            return
        new_videos = self._project_service.get_new_videos(self._current_project)
        if new_videos:
            self.sync_btn.setEnabled(True)
            self.sync_btn.setText(f"  Sincronizar ({len(new_videos)} nuevos)")
            self.sync_badge.setText(f"{len(new_videos)} videos nuevos")
            self.sync_badge.setVisible(True)
        else:
            self.sync_btn.setEnabled(False)
            self.sync_btn.setText("  Sincronizar videos")
            self.sync_badge.setVisible(False)

    def _populate_fragment_list(self):
        self.fragment_list.clear()
        
        if not self._current_project:
            return
        
        for fragment in self._current_project.fragments:
            video_name = fragment.get_video_name()
            status = fragment.label if fragment.is_labeled() else "Sin etiquetar"
            id = fragment.fragment_id
            
            item = QTreeWidgetItem([video_name, status, id])
            item.setData(0, Qt.UserRole, fragment.fragment_id)
            
            if fragment.is_labeled():
                item.setForeground(1, QColor(AppTheme.SUCCESS))
            else:
                item.setForeground(1, QColor(AppTheme.TEXT_PRIMARY))
                
            self.fragment_list.addTopLevelItem(item)

        count = self._current_project.get_total_count()
        self.fragment_count_label.setText(f"{count} fragmentos")

    def _update_project_stats(self):
        if not self._current_project:
            return
        summary = self._project_service.get_project_summary(self._current_project)
        pct = summary['progress_percentage']

        self.stats_label.setText(format_project_stats(summary))
        self.progress_badge.setText(format_project_badge(summary))
        self.progress_bar.setValue(int(pct))
        
    # ─────────────────────────────────────────────
    # Dialogs
    # ─────────────────────────────────────────────

    def _select_folder(self) -> Path:
        folder = QFileDialog.getExistingDirectory(
            self, "Selecciona la carpeta con los fragmentos",
            "", QFileDialog.ShowDirsOnly
        )
        return Path(folder) if folder else None

    def _select_project_file(self) -> Path:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Cargar proyecto", "",
            "JSON Files (*.json);;All Files (*)"
        )
        return Path(file_path) if file_path else None

    def _select_save_path(self, default_name: str, filter: str) -> Path:
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar", default_name, filter
        )
        return Path(file_path) if file_path else None

    def _show_error(self, title: str, message: str):
        QMessageBox.critical(self, title, message)

    def _show_info(self, title: str, message: str):
        QMessageBox.information(self, title, message)