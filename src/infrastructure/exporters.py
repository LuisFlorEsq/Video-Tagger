import json
from pathlib import Path
import pandas as pd
from datetime import datetime

from src.domain.interfaces import IExporter
from src.domain.models.project import Project


class CsvExporter(IExporter):
    """CSV file exporter."""
    
    def export(self, project: Project, output_path: Path) -> None:
        """Export project to CSV file."""
        data = []
        
        for fragment in project.fragments:
            row = {
                'fragment_id': fragment.fragment_id,
                'video_name': fragment.get_video_name(),
                'video_path': fragment.video_path,
                'start_time': fragment.start_time,
                'duration': fragment.duration,
                'label': fragment.label or '',
                'is_labeled': fragment.is_labeled(),
                'notes': fragment.notes,
                'created_at': fragment.created_at.isoformat(),
                'modified_at': fragment.modified_at.isoformat()
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
    
    def get_file_extension(self) -> str:
        """Get file extension."""
        return '.csv'
    
    def get_format_name(self) -> str:
        """Get format name."""
        return 'CSV'


class JsonExporter(IExporter):
    """JSON file exporter (different from repository - this is for export)."""
    
    def export(self, project: Project, output_path: Path) -> None:
        """Export project to JSON file."""
        data = {
            'project_name': project.name,
            'exported_at': datetime.now().isoformat(),
            'statistics': {
                'total_fragments': project.get_total_count(),
                'labeled_fragments': project.get_labeled_count(),
                'progress_percentage': project.get_progress_percentage(),
                'label_distribution': project.get_label_statistics()
            },
            'fragments': [
                {
                    'fragment_id': f.fragment_id,
                    'video_name': f.get_video_name(),
                    'video_path': f.video_path,
                    'start_time': f.start_time,
                    'duration': f.duration,
                    'label': f.label or '',
                    'notes': f.notes
                }
                for f in project.fragments
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2)
    
    def get_file_extension(self) -> str:
        """Get file extension."""
        return '.json'
    
    def get_format_name(self) -> str:
        """Get format name."""
        return 'JSON'