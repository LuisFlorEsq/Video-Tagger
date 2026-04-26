from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFileDialog,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.application.services.project_service import ProjectService
from src.application.services.export_service import ExportService

from src.domain.models.media.media_item import MediaItem
from src.domain.models.project import Project

from src.ui.helpers.dividers import make_vline
from src.ui.styles import (
    AppTheme,
    chip_info,
    chip_warning,
    text_breadcrumb,
    text_secondary,
    text_title,
    topbar_panel,
)

from src.ui.widgets.dialogs.label_config_dialog import LabelConfigDialog
from src.ui.widgets.dialogs.media_type_dialog import MediaTypeDialog
from src.core.config import VIEW_LIST, VIEW_WELCOME


from ._fragment_list import MediaListPanel
from ._sidebar import SidebarPanel


class ProjectBrowser(QWidget):
    """
    Project browser - UI coordination only.
    Business logic delegated to services (SRP + DIP).
    """

    project_loaded = Signal(Project)
    item_selected = Signal(MediaItem)
    project_closed = Signal()
    labels_changed = Signal(list)

    def __init__(
        self,
        project_service: ProjectService,
        export_service: ExportService,
        parent=None,
    ):
        super().__init__(parent)
        self._project_service = project_service
        self._export_service = export_service
        self._current_project: Project = None

        self._init_ui()
        self._connect_signals()
        self._setup_shortcuts()
        self._show_welcome()

    # ----- UI construction -----

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # --- Topbar ---
        topbar = QWidget()
        topbar.setFixedHeight(48)
        topbar.setStyleSheet(topbar_panel())
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(16, 0, 16, 0)
        tb.setSpacing(5)

        app_title = QLabel("Herramienta de etiquetado")
        app_title.setStyleSheet(
            f"font-size: {AppTheme.FONT_LG}; font-weight: bold; "
            f"color: {AppTheme.TEXT_PRIMARY};"
        )
        tb.addWidget(app_title)

        self._topbar_sep = make_vline()
        tb.addWidget(self._topbar_sep)

        self.topbar_project_label = QLabel("")
        self.topbar_project_label.setStyleSheet(text_breadcrumb())
        self.topbar_project_label.setVisible(False)
        tb.addWidget(self.topbar_project_label)

        tb.addStretch()

        # --- MediaType badge, shown when a project is loaded
        self._type_badge = QLabel("")
        self._type_badge.setStyleSheet(chip_info())
        self._type_badge.setVisible(False)
        tb.addWidget(self._type_badge)

        self.sync_badge = QLabel("")
        self.sync_badge.setStyleSheet(chip_warning())
        self.sync_badge.setVisible(False)
        tb.addWidget(self.sync_badge)

        root.addWidget(topbar)

        # --- Body contents ---
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self._sidebar = SidebarPanel()
        body_layout.addWidget(self._sidebar)

        self._stack = QStackedWidget()

        # Main area — welcome screen or fragment list
        welcome = QWidget()
        wl = QVBoxLayout(welcome)
        wl.setAlignment(Qt.AlignCenter)

        title = QLabel("Bienvenido")
        title.setStyleSheet(text_title())
        title.setAlignment(Qt.AlignCenter)

        sub = QLabel(
            "Crea un nuevo proyecto seleccionando una carpeta con videos,\n"
            "o abre un proyecto existente para continuar etiquetando."
        )
        sub.setStyleSheet(text_secondary())
        sub.setAlignment(Qt.AlignCenter)
        sub.setWordWrap(True)

        wl.addStretch()
        wl.addWidget(title)
        wl.addSpacing(8)
        wl.addWidget(sub)
        wl.addStretch()

        self._item_list = MediaListPanel()

        self._stack.addWidget(welcome)
        self._stack.addWidget(self._item_list)
        body_layout.addWidget(self._stack, stretch=1)
        root.addWidget(body, stretch=1)

    # ----- Signal wiring -----

    def _connect_signals(self):
        s = self._sidebar

        # Project selection
        s.new_project_btn.clicked.connect(self._on_new_project_clicked)
        s.load_project_btn.clicked.connect(self._on_load_project_clicked)

        # Project management
        s.save_project_btn.clicked.connect(self._on_save_clicked)
        s.export_csv_btn.clicked.connect(self._on_export_csv_clicked)
        s.config_labels_btn.clicked.connect(self._on_config_labels_clicked)

        # Sync new content and return to Main Window
        s.sync_btn.clicked.connect(self._on_sync_clicked)
        s.back_btn.clicked.connect(self._on_back_clicked)

        # Switch to media viewer (item selected)
        self._item_list.item_activated.connect(
            lambda item: self.item_selected.emit(item)
        )

    # ----- Keyboard shortcuts -----

    def _setup_shortcuts(self):
        for shortcut, slot in [
            ("Ctrl+R", self._on_sync_clicked),
            ("Escape", self._on_back_clicked),
            ("Ctrl+F", self._item_list.focus_search),
        ]:
            action = QAction(self)
            action.setShortcut(shortcut)
            action.setShortcutContext(Qt.WidgetWithChildrenShortcut)
            action.triggered.connect(slot)
            self.addAction(action)

    # ----- Command handlers -----

    def _on_new_project_clicked(self):

        # Ask for media type
        dlg = MediaTypeDialog(parent=self)
        if dlg.exec() != QDialog.Accepted:
            return
        media_type = dlg.chosen

        # Pick/select the folder
        folder_path = self._select_folder()
        if not folder_path:
            return
        try:
            project = self._project_service.create_project_from_folder(
                folder_path=folder_path,
                media_type=media_type,
            )
            self._load_project(project)
            self._prompt_initial_save(project)
            self.project_loaded.emit(project)
        except ValueError as exc:
            self._show_error("Error al crear proyecto", str(exc))
        except Exception as exc:
            self._show_error(
                "Error inesperado", f"No se pudo crear el proyecto:\n{str(exc)}"
            )

    def _on_load_project_clicked(self):
        file_path = self._select_project_file()
        if not file_path:
            return
        try:
            project = self._project_service.load_project(file_path)
            self._load_project(project)
            self.project_loaded.emit(project)
        except ValueError as exc:
            self._show_error("No se pudo cargar el proyecto", str(exc))
        except Exception as exc:
            self._show_error(
                "Error inesperado", f"No se pudo cargar el proyecto:\n{str(exc)}"
            )

    def _on_back_clicked(self):
        self._current_project = None
        self._show_welcome()
        self.project_closed.emit()

    def _on_save_clicked(self):
        if not self._current_project:
            return

        file_path = self._select_save_path(
            f"{self._current_project.name}.json", "JSON Files (*.json)"
        )
        if not file_path:
            return

        try:
            self._project_service.save_project(self._current_project, file_path)
            summary = self._project_service.get_project_summary(self._current_project)
            self._show_info(
                "Proyecto guardado",
                "Guardado correctamente.\n\n"
                f"Progreso: {summary['labeled']}/{summary['total_fragments']} "
                f"({summary['progress_percentage']:.1f}%)",
            )
        except Exception as exc:
            self._show_error("Error al guardar", str(exc))

    def _on_export_csv_clicked(self):
        if not self._current_project:
            self._show_error("Sin proyecto", "No hay proyecto cargado para exportar.")
            return

        if self._current_project.get_total_count() == 0:
            self._show_error("Sin datos", "No hay elementos para exportar.")
            return

        file_path = self._select_save_path(
            f"{self._current_project.name}_export.csv",
            "CSV Files (*.csv);;All Files (*)",
        )
        if not file_path:
            return

        try:
            self._export_service.export(self._current_project, file_path, "csv")
            summary = self._project_service.get_project_summary(self._current_project)
            self._show_info(
                "Exportacion exitosa",
                f"{summary['total_fragments']} elementos exportados.\n"
                f"Etiquetados: {summary['labeled']}/{summary['total_fragments']}\n"
                f"Archivo: {file_path.name}",
            )
        except Exception as exc:
            self._show_error(
                "Error al exportar", f"No se pudo exportar a CSV:\n{str(exc)}"
            )

    def _on_config_labels_clicked(self):
        if not self._current_project:
            return

        dlg = LabelConfigDialog(
            current_labels=self._current_project.get_labels(),
            parent=self,
        )
        dlg.set_assigned_labels(
            set(self._current_project.get_label_statistics().keys())
        )
        dlg.labels_changed.connect(self._on_labels_confirmed)
        dlg.exec()

    def _on_labels_confirmed(self, new_labels: list):
        if not self._current_project:
            return

        self._current_project.set_labels(new_labels)
        self._project_service.auto_save_project(self._current_project)
        self.labels_changed.emit(new_labels)

    def _on_sync_clicked(self):
        if not self._current_project:
            return

        new_items = self._project_service.get_new_items(self._current_project)
        if not new_items:
            self._show_info("Sin cambios", "No hay archivos nuevos para sincronizar.")
            return

        reply = QMessageBox.question(
            self,
            "Sincronizar archivos",
            f"Se encontraron {len(new_items)} archivos nuevos.\n\n"
            "Deseas agregarlos al proyecto?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            count = self._project_service.sync_new_items(
                self._current_project,
                new_items,
            )
            self.refresh()
            self._sidebar.set_sync_idle()
            self.sync_badge.setVisible(False)
            was_saved = self._persist_current_project(
                ask_first_save=True,
                success_title="Sincronizacion exitosa",
                success_message=(f"Se agregaron {count} archivos nuevos al proyecto."),
            )
            if not was_saved:
                self._show_info(
                    "Sincronizacion exitosa",
                    f"Se agregaron {count} archivos nuevos al proyecto.\n\n"
                    "El proyecto sigue en memoria, pero aun no se guardo.",
                )
        except Exception as exc:
            self._show_error("Error al sincronizar", str(exc))

    # ----- Public API -----

    def refresh(self):
        if self._current_project:
            self._item_list.refresh(self._current_project)

    def set_focus(self):
        self._item_list.set_focus()

    def get_current_project(self) -> Project:
        return self._current_project

    def trigger_new_project(self):
        self._on_new_project_clicked()

    def trigger_load_project(self):
        self._on_load_project_clicked()

    def trigger_save_project(self):
        self._on_save_clicked()

    def trigger_export_project(self):
        self._on_export_csv_clicked()

    # ----- Private helpers -----

    def _load_project(self, project: Project):
        self._current_project = project
        self._show_project(project)

    def _show_project(self, project: Project):
        self.topbar_project_label.setText(project.name)
        self.topbar_project_label.setVisible(True)
        self._topbar_sep.setVisible(True)

        self._type_badge.setText(f"  {project.media_type.label()}  ")
        self._type_badge.setVisible(True)

        self._sidebar.show_project_state(project.name)
        self._sidebar.sync_btn.setVisible(True)

        self._stack.setCurrentIndex(VIEW_LIST)
        self._item_list.load(project)
        self._check_for_new_items()

    def _show_welcome(self):
        self.topbar_project_label.setVisible(False)
        self._topbar_sep.setVisible(False)

        self._type_badge.setVisible(False)
        self.sync_badge.setVisible(False)

        self._sidebar.show_welcome_state()
        self._sidebar.set_sync_idle()
        self._item_list.reset()
        self._stack.setCurrentIndex(VIEW_WELCOME)

    def _check_for_new_items(self):
        if not self._current_project:
            return

        new_items = self._project_service.get_new_items(self._current_project)
        if new_items:
            self._sidebar.set_sync_pending(len(new_items))
            self.sync_badge.setText(f"{len(new_items)} archivos nuevos")
            self.sync_badge.setVisible(True)
        else:
            self._sidebar.set_sync_idle()
            self.sync_badge.setVisible(False)

    def _prompt_initial_save(self, project: Project):
        reply = QMessageBox.question(
            self,
            "Guardar proyecto",
            "El proyecto fue creado correctamente.\n\nDeseas guardarlo ahora?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        self._persist_project(
            project,
            ask_first_save=True,
            success_title="Proyecto guardado",
            success_message="Proyecto creado y guardado correctamente.",
        )

    def _persist_current_project(
        self,
        ask_first_save: bool,
        success_title: str | None = None,
        success_message: str | None = None,
    ) -> bool:
        if not self._current_project:
            return False

        return self._persist_project(
            self._current_project,
            ask_first_save=ask_first_save,
            success_title=success_title,
            success_message=success_message,
        )

    def _persist_project(
        self,
        project: Project,
        ask_first_save: bool,
        success_title: str | None = None,
        success_message: str | None = None,
    ) -> bool:
        if project.get_save_path():
            return self._auto_save_with_feedback(
                project,
                success_title=success_title,
                success_message=success_message,
            )

        if not ask_first_save:
            return False

        file_path = self._select_save_path(
            f"{project.name}.json",
            "JSON Files (*.json)",
        )
        if not file_path:
            return False

        self._project_service.save_project(project, file_path)
        if success_title and success_message:
            self._show_info(success_title, success_message)
        return True

    def _auto_save_with_feedback(
        self,
        project: Project,
        success_title: str | None = None,
        success_message: str | None = None,
    ) -> bool:
        saved = self._project_service.auto_save_project(project)
        if saved and success_title and success_message:
            self._show_info(success_title, success_message)
        return saved

    # ----- Dialogs -----

    def _select_folder(self) -> Path:
        folder = QFileDialog.getExistingDirectory(
            self,
            "Selecciona la carpeta raiz (proyecto)",
            "",
            QFileDialog.ShowDirsOnly,
        )
        return Path(folder) if folder else None

    def _select_project_file(self) -> Path:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Cargar proyecto",
            "",
            "JSON Files (*.json);;All Files (*)",
        )
        return Path(file_path) if file_path else None

    def _select_save_path(self, default_name: str, filter: str) -> Path:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar",
            default_name,
            filter,
        )
        return Path(file_path) if file_path else None

    def _show_error(self, title: str, message: str):
        QMessageBox.critical(self, title, message)

    def _show_info(self, title: str, message: str):
        QMessageBox.information(self, title, message)
