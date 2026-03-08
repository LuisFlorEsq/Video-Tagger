from pathlib import Path
from typing import List

from src.domain.interfaces import IFragmentScanner

class FileSystemFragmentScanner(IFragmentScanner):
    """File system-based fragment scanner."""
    
    SUPPORTED_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
    
    def scan_folder(self, folder_path: Path) -> List[Path]:
        """Scan folder for video files."""
        if not folder_path.exists() or not folder_path.is_dir():
            raise ValueError(f"Invalid folder path: {folder_path}")
        
        video_files = []
        for ext in self.SUPPORTED_EXTENSIONS:
            video_files.extend(folder_path.glob(f'*{ext}'))
            video_files.extend(folder_path.glob(f'*{ext.upper()}'))
        
        return sorted(set(video_files))
    
    def get_supported_extensions(self) -> List[str]:
        """Get supported extensions."""
        return self.SUPPORTED_EXTENSIONS.copy()

