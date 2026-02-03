import json
from pathlib import Path
from datetime import datetime

from src.domain.interfaces import IProjectRepository

from src.domain.models.project import Project
from src.domain.models.fragment import Fragment


class JsonProjectRepository(IProjectRepository):
    """JSON file-based project repository."""
    
    def save(self, project: Project, file_path: Path) -> None:
        """Save project to JSON file."""
        data = {
            'name': project.name,
            'folder_path': project.folder_path,
            'fragments': [self._fragment_to_dict(f) for f in project.fragments],
            'created_at': project.created_at.isoformat(),
            'modified_at': project.modified_at.isoformat()
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def load(self, file_path: Path) -> Project:
        """Load project from JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        project = Project(
            name=data['name'],
            folder_path=data['folder_path'],
            created_at=datetime.fromisoformat(data['created_at']),
            modified_at=datetime.fromisoformat(data['modified_at'])
        )
        
        for fragment_data in data.get('fragments', []):
            fragment = self._dict_to_fragment(fragment_data)
            project.add_fragment(fragment)
        
        return project
    
    def exists(self, file_path: Path) -> bool:
        """Check if project file exists."""
        return file_path.exists() and file_path.is_file()
    
    @staticmethod
    def _fragment_to_dict(fragment: Fragment) -> dict:
        """Convert fragment to dictionary."""
        return {
            'fragment_id': fragment.fragment_id,
            'video_path': fragment.video_path,
            'start_time': fragment.start_time,
            'duration': fragment.duration,
            'label': fragment.label or '',
            'notes': fragment.notes,
            'created_at': fragment.created_at.isoformat(),
            'modified_at': fragment.modified_at.isoformat()
        }
    
    @staticmethod
    def _dict_to_fragment(data: dict) -> Fragment:
        """Convert dictionary to fragment."""
        return Fragment(
            fragment_id=data['fragment_id'],
            video_path=data['video_path'],
            start_time=data['start_time'],
            duration=data.get('duration', 1.0),
            label=data.get('label') if data.get('label') else None,
            notes=data.get('notes', ''),
            created_at=datetime.fromisoformat(data['created_at']),
            modified_at=datetime.fromisoformat(data['modified_at'])
        )