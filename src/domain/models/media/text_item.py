from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from pathlib import Path

from src.domain.models.media.media_item import MediaItem, MediaType


@dataclass
class TextItem(MediaItem):
    """
    A text document / snippet to be labeled
    
    content - in-memory text content (loaded from file_path on demand).
    encoding - file encoding, defaults to UTF-8 
    """
    
    content: Optional[str] = None
    encoding: str = "utf-8"
    
    
    def __init__(
        self,
        item_id: str,
        file_path: str,
        label: Optional[str] = None,
        notes: str = "",
        content: Optional[str] = None,
        encoding: str = "utf-8",
        created_at: Optional[datetime] = None,
        modified_at: Optional[datetime] = None,
    ) -> None:
        
        super().__init__(
            item_id=item_id,
            file_path=file_path,
            media_type=MediaType.TEXT,
            label=label,
            notes=notes,
            created_at=created_at or datetime.now(),
            modified_at=modified_at or datetime.now()
        )
        
        self.content = content
        self.encoding = encoding
        
    def get_text_name(self) -> str:
        return self.get_filename()
    
    def load_content(self) -> str:
        """
        Read file content into memory if not already loaded.
        """
        
        if self.content is None:
            path = Path(self.file_path)
            
            if not path.exists():
                raise FileNotFoundError(f"Text file not found: {self.file_path}")
            self.content = path.read_text(encoding=self.encoding)
            
        return self.content
    
    @property
    def word_count(self) -> Optional[int]:
        if self.content is None:
            return None
        return len(self.content.split())
    
    @property
    def preview(self) -> str:
        """
        First 100 characters for display in list
        """
        if not self.content:
            return ""
        return self.content[:100] + ("…" if len(self.content) > 100 else "")