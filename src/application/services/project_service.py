from pathlib import Path

from src.domain.models.project import Project
from src.domain.models.fragment import Fragment
from src.domain.interfaces import (
    IProjectRepository, IVideoSource, 
    IFragmentScanner
)


class ProjectService:
    """Service for project-related operations (SRP)."""
    
    def __init__(
        self, 
        repository: IProjectRepository,
        scanner: IFragmentScanner,
        video_source: IVideoSource
    ):
        self._repository = repository
        self._scanner = scanner
        self._video_source = video_source
    
    def create_project_from_folder(self, folder_path: Path) -> Project:
        """Create a new project by scanning a folder for video fragments."""
        if not folder_path.exists():
            raise ValueError(f"La carpeta no existe: {folder_path}")
        
        # Scan for video files
        video_files = self._scanner.scan_folder(folder_path)
        
        if not video_files:
            raise ValueError("No se encontraron archivos de video")
        
        # Create project
        project = Project(
            name=folder_path.name,
            folder_path=str(folder_path)
        )
        
        # Create fragments from video files
        for i, video_file in enumerate(sorted(video_files)):
            duration = self._video_source.get_duration(video_file)
            
            fragment = Fragment(
                fragment_id=f"fragment_{i+1:03d}",
                video_path=str(video_file),
                start_time=0.0,
                duration=min(1.0, duration)
            )
            project.add_fragment(fragment)
        
        return project
    
    def save_project(self, project: Project, file_path: Path) -> None:
        """Save a project to file."""
        self._repository.save(project, file_path)
    
    def auto_save_project(self, project: Project) -> bool:
        """
        Auto-save project to its saved location.
        
        Args:
            project: Project to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        save_path = project.get_save_path()
        
        if not save_path:
            return False
        
        try:
            self._repository.save(project, save_path)
            return True
        except Exception as e:
            print(f"Auto-save failed: {e}")
            return False
    
    def load_project(self, file_path: Path) -> Project:
        """Load a project from file."""
        if not self._repository.exists(file_path):
            raise ValueError(f"El proyecto no existe: {file_path}")
        
        return self._repository.load(file_path)
    
    def get_new_videos(self, project: Project) -> set[Path]:
        """Get the count of new videos in a project folder

        Args:
            project (Project): Projec to check

        Returns:
            set: Set of new videos detected
        """
        folder_path = Path(project.folder_path)
        
        if not folder_path.exists():
            return set()
        
        all_videos = self._scanner.scan_folder(folder_path=folder_path)
        existing_paths = {Path(f.video_path) for f in project.fragments}
        new_videos = set(all_videos) - existing_paths
        
        return new_videos
        
    def sync_new_videos(self, project: Project, new_videos: set[Path]) -> int:
        """
        Add new_videos detected as fragments for the current project
        Args:
            project (Project): Project to sync
            new_videos (set[Path]): The Paths of the detected new videos

        Returns:
            int: Number of new fragments added
        """
        if not new_videos:
            return 0
        
        existing_ids = [f.fragment_id for f in project.fragments]
        max_id = 0
        
        for fid in existing_ids:
            try:
                num = int(fid.split('_')[-1])
                max_id = max(max_id, num)
            except ValueError:
                pass
        next_id = max_id + 1
        
        added = 0        
        for video_path in new_videos:
            try:
                duration = self._video_source.get_duration(video_path)
                fragment = Fragment(
                    fragment_id=f"fragment_{next_id:03d}",
                    video_path=str(video_path),
                    start_time=0.0,
                    duration=min(1.0, duration)
                )
                project.add_fragment(fragment)
                next_id += 1
                added += 1
            except Exception as e:
                print(f"Failed to add {video_path}: {e}")
                continue
            
        return added
    
    def get_project_summary(self, project: Project) -> dict:
        """Get a summary of project statistics."""
        return {
            'name': project.name,
            'total_fragments': project.get_total_count(),
            'labeled': project.get_labeled_count(),
            'unlabeled': project.get_unlabeled_count(),
            'progress_percentage': project.get_progress_percentage(),
            'label_statistics': project.get_label_statistics()
        }