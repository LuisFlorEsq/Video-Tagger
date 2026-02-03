from pathlib import Path
import cv2

from src.domain.interfaces import IVideoSource

class OpenCvVideoSource(IVideoSource):
    """OpenCV-based video source."""
    
    def get_duration(self, video_path: Path) -> float:
        """Get video duration in seconds."""
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        cap.release()
        
        if fps > 0:
            return frame_count / fps
        return 0.0
    
    def get_fps(self, video_path: Path) -> float:
        """Get video FPS."""
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        return fps
    
    def exists(self, video_path: Path) -> bool:
        """Check if video file exists and can be opened."""
        if not video_path.exists():
            return False
        
        cap = cv2.VideoCapture(str(video_path))
        is_valid = cap.isOpened()
        cap.release()
        return is_valid

