import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))
from src.core.qt_config import setup_quiet_mode, setup_verbose_mode
from src.core.resources import resource_path

from src.core.container import get_container
from src.application.services.project_service import ProjectService
from src.application.services.export_service import ExportService
from src.application.services.labeling_service import LabelingService

from src.ui.main_window import create_main_window
from src.ui.styles import app_stylesheet


def main():
    """Initialize application with dependency injection."""
    
    setup_verbose_mode()
    
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    
    # app_icon = QIcon(resource_path("src/ui/resources/icons/icon_cic.png"))
    # app.setWindowIcon(app_icon)
    
    app.setApplicationName("Herramienta de etiquetado")
    app.setOrganizationName("Centro de Investigación en Computación")
    app.setStyleSheet(app_stylesheet())
    
    # Get dependency container
    container = get_container()
    
    # Resolve services from container
    project_service = container.resolve(ProjectService)
    labeling_service = container.resolve(LabelingService)
    export_service = container.resolve(ExportService)
    
    # Create main window with injected dependencies
    window = create_main_window(
        project_service=project_service,
        labeling_service=labeling_service,
        export_service=export_service
    )
    
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()