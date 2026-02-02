import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
 
# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.ui.main_window import MainWindow


def main():
    """Initialize and run the application."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("Herramienta de etiquetado")
    app.setOrganizationName("Centro de Investigación en Computación")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()