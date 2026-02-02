"""Manages frame annotations and provides data access."""
import json
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

from src.models.frame import FrameAnnotation


class AnnotationManager:
    """Manages all frame annotations for a project."""
    
    def __init__(self):
        self.annotations: Dict[int, FrameAnnotation] = {}
        self._modified = False
    
    def add_annotation(self, annotation: FrameAnnotation) -> None:
        """Add or update an annotation."""
        self.annotations[annotation.frame_number] = annotation
        self._modified = True
    
    def get_annotation(self, frame_number: int) -> Optional[FrameAnnotation]:
        """Get annotation for a specific frame."""
        return self.annotations.get(frame_number)
    
    def remove_annotation(self, frame_number: int) -> bool:
        """Remove an annotation. Returns True if removed."""
        if frame_number in self.annotations:
            del self.annotations[frame_number]
            self._modified = True
            return True
        return False
    
    def get_all_annotations(self) -> List[FrameAnnotation]:
        """Get all annotations sorted by frame number."""
        return sorted(self.annotations.values(), key=lambda x: x.frame_number)
    
    def get_labeled_frames(self) -> List[FrameAnnotation]:
        """Get only frames with labels."""
        return [a for a in self.get_all_annotations() if a.label]
    
    def save_to_file(self, filepath: Path) -> None:
        """Save annotations to JSON file."""
        data = {
            'annotations': [a.to_dict() for a in self.get_all_annotations()]
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        self._modified = False
    
    def load_from_file(self, filepath: Path) -> None:
        """Load annotations from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.annotations.clear()
        for item in data['annotations']:
            annotation = FrameAnnotation.from_dict(item)
            self.annotations[annotation.frame_number] = annotation
        self._modified = False
    
    def export_to_csv(self, filepath: Path) -> None:
        """Export annotations to CSV file."""
        if not self.annotations:
            raise ValueError("No annotations to export")
        
        data = [a.to_dict() for a in self.get_all_annotations()]
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
    
    def get_label_statistics(self) -> Dict[str, int]:
        """Get count of each label."""
        stats = {}
        for annotation in self.annotations.values():
            if annotation.label:
                stats[annotation.label] = stats.get(annotation.label, 0) + 1
        return stats
    
    @property
    def is_modified(self) -> bool:
        """Check if annotations have been modified since last save."""
        return self._modified
    
    def clear(self) -> None:
        """Clear all annotations."""
        self.annotations.clear()
        self._modified = False