from typing import Dict, Any, Callable, TypeVar, Type

from src.domain.interfaces import (
    ILabelValidator,
    IMediaPreviewSource,
    IMediaScanner,
    IProjectRepository,
)

from src.domain.models.media.media_item import MediaType

from src.infrastructure.repositories import JsonProjectRepository
from src.infrastructure.exporters import CsvExporter, JsonExporter
from src.infrastructure.validators import SimpleLabelValidator

from src.infrastructure.scanners import (
    VideoScanner,
    AudioScanner,
    ImageScanner,
    TextScanner
)
from src.infrastructure.preview_sources import (
    VideoPreviewSource,
    AudioPreviewSource,
    ImagePreviewSource,
    TextPreviewSource
)

from src.application.services.project_service import MediaTypeFactory, ProjectService
from src.application.services.labeling_service import LabelingService
from src.application.services.export_service import ExportService


T = TypeVar('T')


class ServiceContainer:
    """Simple service container for dependency injection."""

    def __init__(self):
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}

    def register_singleton(self, interface: Type[T], implementation: T) -> None:
        """Register a singleton instance."""
        self._singletons[interface] = implementation

    def register_transient(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """Register a factory for creating new instances."""
        self._factories[interface] = factory

    def resolve(self, interface: Type[T]) -> T:
        """Resolve a service by its interface."""
        # Check singletons first
        if interface in self._singletons:
            return self._singletons[interface]

        # Check factories
        if interface in self._factories:
            return self._factories[interface]()

        raise ValueError(f"Service not registered: {interface}")

    def register_default_services(self) -> None:
        """Register default implementations."""
        # ------ Infrastructure layer - singletons ---------
        self.register_singleton(IProjectRepository, JsonProjectRepository())
        self.register_singleton(ILabelValidator, SimpleLabelValidator())

        # ------ Infrastructure layer - scanners ---------
        video_scanner = VideoScanner()
        image_scanner = ImageScanner()
        audio_scanner = AudioScanner()
        text_scanner = TextScanner()

        # Register by MediaType
        self.register_singleton(VideoScanner, video_scanner)
        self.register_singleton(ImageScanner, image_scanner)
        self.register_singleton(AudioScanner, audio_scanner)
        self.register_singleton(TextScanner, text_scanner)

        # ------ Infrastructure layer - preview sources ---------
        video_preview = VideoPreviewSource()
        image_preview = ImagePreviewSource()
        audio_preview = AudioPreviewSource()
        text_preview = TextPreviewSource()
        
        # Register by MediaType
        self.register_singleton(VideoPreviewSource, video_preview)
        self.register_singleton(ImagePreviewSource, image_preview)
        self.register_singleton(AudioPreviewSource, audio_preview)
        self.register_singleton(TextPreviewSource, text_preview)

        # ------ MediaTypeFactory ---------
        media_factory = MediaTypeFactory()
        
        # Register scanners
        media_factory.register_scanner(video_scanner)
        media_factory.register_scanner(image_scanner)
        media_factory.register_scanner(audio_scanner)
        media_factory.register_scanner(text_scanner)
        
        # Register previews
        media_factory.register_preview_source(video_preview)
        media_factory.register_preview_source(image_preview)
        media_factory.register_preview_source(audio_preview)
        media_factory.register_preview_source(text_preview)
        
        # Singleton
        self.register_singleton(MediaTypeFactory, media_factory)

        # ------ Application services ---------
        self.register_transient(
            ProjectService,
            lambda: ProjectService(
                repository=self.resolve(IProjectRepository),
                media_factory=self.resolve(MediaTypeFactory)
            )
        )

        self.register_transient(
            LabelingService,
            lambda: LabelingService(
                validator=self.resolve(ILabelValidator)
            )
        )

        # Export service with registered exporters
        export_service = ExportService()
        export_service.register_exporter('csv', CsvExporter())
        export_service.register_exporter('json', JsonExporter())
        self.register_singleton(ExportService, export_service)


# Global container instance
_container: ServiceContainer = None


def get_container() -> ServiceContainer:
    """Get the global service container."""
    global _container
    if _container is None:
        _container = ServiceContainer()
        _container.register_default_services()
    return _container


def reset_container() -> None:
    """Reset the global container (useful for testing)."""
    global _container
    _container = None
