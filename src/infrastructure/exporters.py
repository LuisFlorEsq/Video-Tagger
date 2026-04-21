import json
from pathlib import Path
import pandas as pd
from datetime import datetime

from src.domain.interfaces import IExporter
from src.domain.models.project import Project
from src.domain.models.media.media_item import MediaItem


def _item_to_row(item: MediaItem) -> dict:
    """
    Converts any MediaItem subclass to a flat dict for export
    
    Common fields are always present
    Type-specific fields default to None / '' when absent.
    """
    
    return {
        # Shared
        "item_id":    item.item_id,
        "media_type": item.media_type.value,
        "filename":   item.get_filename(),
        "file_path":  item.file_path,
        "label":      item.label or "",
        "is_labeled": item.is_labeled(),
        "notes":      item.notes,
        "created_at": item.created_at.isoformat(),
        "modified_at": item.modified_at.isoformat(),
        
        # Video
        "start_time": getattr(item, "start_time", None),
        "duration":   getattr(item, "duration",   None),
        
        # Image
        "width":      getattr(item, "width",       None),
        "height":     getattr(item, "height",      None),
        "source_key": getattr(item, "source_key", None),
        
        # Audio
        "duration_s": getattr(item, "duration_s",  None),
        "sample_rate": getattr(item, "sample_rate", None),

        # Signal
        "shape": getattr(item, "shape", None),
        "dtype": getattr(item, "dtype", None),
        "channels": getattr(item, "channels", None),
        
        # Text
        "encoding":   getattr(item, "encoding",    None),
    }


class CsvExporter(IExporter):
    """CSV file exporter."""
    
    def export(self, project: Project, output_path: Path) -> None:
        """Export project to CSV file."""
        rows = [_item_to_row(item) for item in project.items]
        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)
    
    def get_file_extension(self) -> str:
        """Get file extension."""
        return '.csv'
    
    def get_format_name(self) -> str:
        """Get format name."""
        return 'CSV'


class JsonExporter(IExporter):
    """JSON file exporter."""
    
    def export(self, project: Project, output_path: Path) -> None:
        """Export project to JSON file."""
        data = {
            'project_name': project.name,
            'media_type': project.media_type.value,
            'exported_at': datetime.now().isoformat(),
            'statistics': {
                'total_items': project.get_total_count(),
                'labeled_items': project.get_labeled_count(),
                'progress_percentage': project.get_progress_percentage(),
                'label_distribution': project.get_label_statistics()
            },
            'items': [_item_to_row(item) for item in project.items],
        }
        
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
    
    def get_file_extension(self) -> str:
        """Get file extension."""
        return '.json'
    
    def get_format_name(self) -> str:
        """Get format name."""
        return 'JSON'
