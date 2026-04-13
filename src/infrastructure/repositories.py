from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Any

from src.core.logger import logger
from src.domain.interfaces import IProjectRepository

from src.domain.models.media.media_item import MediaItem, MediaType
from src.domain.models.media.image_item import ImageItem
from src.domain.models.media.audio_item import AudioItem
from src.domain.models.media.text_item import TextItem

from src.domain.models.fragment import Fragment
from src.domain.models.project import Project
from src.core.config import DEFAULT_LABELS


class JsonProjectRepository(IProjectRepository):
    """JSON file-based project repository."""
    
    def save(self, project: Project, file_path: Path) -> None:
        """Save project to JSON file."""
        try:
            logger.info(f"Iniciando guardado de proyecto: {project.name} en {file_path}")
            project.set_save_path(file_path)
            
            data = {
                'name': project.name,
                'folder_path': project.folder_path,
                'save_path': project.save_path,
                'media_type': project.media_type.value,
                'custom_labels': project.custom_labels,
                'items': [self._item_to_dict(it) for it in project.items],
                'created_at': project.created_at.isoformat(),
                'modified_at': project.modified_at.isoformat()
            }
                
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Proyecto '{project.name}' guardado exitosamente.")
            
        except Exception as e:
            logger.error(f"Error crítico al guardar proyecto {project.name}: {str(e)}", exc_info=True)
            raise
    
    def load(self, file_path: Path) -> Project:
        """Load project from JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # ----- Labels ------    
        raw_labels = data.get('custom_labels')
        custom_labels = (
            [lbl for lbl in raw_labels if lbl and lbl.strip()]
            if raw_labels
            else list()
        )
        
        # ----- Media type ------
        media_type = MediaType.from_str(data.get("media_type", "video"))  

        project = Project(
            name=data['name'],
            folder_path=data['folder_path'],
            save_path=data['save_path'],
            media_type=media_type,
            created_at=datetime.fromisoformat(data['created_at']),
            modified_at=datetime.fromisoformat(data['modified_at']),
            custom_labels=custom_labels
        )
        
        raw_items = data.get("items") or data.get("fragments", [])
        
        for item_data in raw_items:
            item = self._dict_to_item(item_data)
            project.add_item(item)
            
        return project
         
    def exists(self, file_path: Path) -> bool:
        """Check if project file exists."""
        return file_path.exists() and file_path.is_file()
    
    # ---------------------------------------------
    # Serialization helpers
    # ---------------------------------------------
    
    def _item_to_dict(self, item: MediaItem) -> dict:
        """Dispatch to the correct serializer based on type."""
        
        base = self._base_dict(item)
        
        if isinstance(item, Fragment):
            base.update(self._fragment_extra(item))
        elif isinstance(item, ImageItem):
            base.update(self._image_extra(item))
        elif isinstance(item, AudioItem):
            base.update(self._audio_extra(item))
        elif isinstance(item, TextItem):
            base.update(self._text_extra(item))
            
        return base
    
    def _dict_to_item(self, data: dict) -> MediaItem:
        """
        Dispatch to the correct deserializer
        """
        mt_str = data.get("media_type", "video")
        mt = MediaType.from_str(mt_str)
        
        if mt == MediaType.VIDEO:
            return self._dict_to_fragment(data)
        elif mt == MediaType.IMAGE:
            return self._dict_to_image(data)
        elif mt == MediaType.AUDIO:
            return self._dict_to_audio(data)
        elif mt == MediaType.TEXT:
            return self._dict_to_text(data)
        
        return self._dict_to_fragment(data) # Fallback
    
    # ---------------------------------------------
    # Base fields
    # ---------------------------------------------
    
    @staticmethod
    def _base_dict(item: MediaItem) -> dict:
        return {
            "item_id": item.item_id,
            "file_path": item.file_path,
            "media_type": item.media_type.value,
            "label": item.label or "",
            "notes": item.notes,
            "created_at": item.created_at.isoformat(),
            "modified_at": item.modified_at.isoformat()
        }
        
    @staticmethod
    def _base_from_dict(data: dict) -> dict:
        """Extract base MediaItem kwargs from a raw dict."""
        return {
            "label": data.get("label") or None,
            "notes": data.get("notes", ""),
            "created_at": datetime.fromisoformat(data["created_at"]),
            "modified_at": datetime.fromisoformat(data["modified_at"])
        }
        
    # ---------------------------------------------
    # Video Fragment
    # ---------------------------------------------
    
    @staticmethod
    def _fragment_extra(f: Fragment) -> dict:
    
        return {
            "fragment_id": f.fragment_id,
            "video_path":  f.video_path,
            "start_time":  f.start_time,
            "duration":    f.duration,
        }
        
    @staticmethod
    def _dict_to_fragment(data: dict) -> Fragment:
        base = JsonProjectRepository._base_from_dict(data)
        return Fragment(
            fragment_id=data.get("fragment_id") or data.get("item_id"),
            video_path=data.get("video_path") or data.get("file_path"),
            start_time=data.get("start_time", 0.0),
            duration=data.get("duration", 1.0),
            **base,
        )
        
    # ---------------------------------------------
    # ImageItem
    # ---------------------------------------------
    
    @staticmethod
    def _image_extra(img: ImageItem) -> dict:
        return {
            "width": img.width,
            "height": img.height
        }
        
    
    @staticmethod
    def _dict_to_image(data: dict) -> ImageItem:
        base = JsonProjectRepository._base_from_dict(data)
        return ImageItem(
            item_id=data.get("item_id") or data.get("fragment_id"),
            file_path=data.get("file_path") or data.get("video_path"),
            width=data.get("width"),
            height=data.get("height"),
            **base
        )
        
    # ---------------------------------------------
    # AudioItem
    # ---------------------------------------------
    
    @staticmethod
    def _audio_extra(audio: AudioItem) -> dict:
        return {
            "duration_s":  audio.duration_s,
            "sample_rate": audio.sample_rate,
        }
 
    @staticmethod
    def _dict_to_audio(data: dict) -> AudioItem:
        base = JsonProjectRepository._base_from_dict(data)
        return AudioItem(
            item_id=data.get("item_id") or data.get("fragment_id"),
            file_path=data.get("file_path") or data.get("video_path"),
            duration_s=data.get("duration_s"),
            sample_rate=data.get("sample_rate"),
            **base,
        )
        
    # ---------------------------------------------
    # TextItem
    # ---------------------------------------------
    
    @staticmethod
    def _text_extra(text: TextItem) -> dict:
        return {
            "encoding": text.encoding,
        }
 
    @staticmethod
    def _dict_to_text(data: dict) -> TextItem:
        base = JsonProjectRepository._base_from_dict(data)
        return TextItem(
            item_id=data.get("item_id") or data.get("fragment_id"),
            file_path=data.get("file_path") or data.get("video_path"),
            encoding=data.get("encoding", "utf-8"),
            **base,
        )