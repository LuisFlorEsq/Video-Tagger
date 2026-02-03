from typing import List
from pathlib import Path

from src.domain.models.project import Project
from src.domain.interfaces import IExporter


class ExportService:
    """Service for exporting project data (SRP + OCP)."""
    
    def __init__(self):
        self._exporters: dict[str, IExporter] = {}
    
    def register_exporter(self, format_name: str, exporter: IExporter) -> None:
        """Register a new exporter (Open for extension)."""
        self._exporters[format_name.lower()] = exporter
    
    def export(self, project: Project, output_path: Path, format_name: str) -> None:
        """Export project using the specified format."""
        format_key = format_name.lower()
        
        if format_key not in self._exporters:
            raise ValueError(f"Unsupported export format: {format_name}")
        
        exporter = self._exporters[format_key]
        exporter.export(project, output_path)
    
    def get_available_formats(self) -> List[str]:
        """Get list of available export formats."""
        return [exp.get_format_name() for exp in self._exporters.values()]
    
    def get_file_extension(self, format_name: str) -> str:
        """Get file extension for a format."""
        format_key = format_name.lower()
        if format_key not in self._exporters:
            raise ValueError(f"Unsupported export format: {format_name}")
        
        return self._exporters[format_key].get_file_extension()