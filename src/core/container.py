from typing import Dict, Any, Callable, TypeVar, Type

from src.domain.interfaces import (
    ILabelValidator,
    IMediaPreviewSource,
    IMediaScanner,
    IProjectRepository,
)

from src.infrastructure.repositories import JsonProjectRepository
from src.infrastructure.exporters import CsvExporter, JsonExporter
from src.infrastructure.validators import SimpleLabelValidator

from src.infrastructure.scanners import (
    VideoScanner,
    AudioScanner,
    ImageScanner,
    SignalScanner,
    TextScanner
)
from src.infrastructure.preview_sources import (
    VideoPreviewSource,
    AudioPreviewSource,
    ImagePreviewSource,
    SignalPreviewSource,
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

        # ---- Initiate infrastructure components ----
        scanners: list[IMediaScanner] = [
            VideoScanner(),
            ImageScanner(),
            AudioScanner(),
            SignalScanner(),
            TextScanner()
        ]

        preview_sources: list[IMediaPreviewSource] = [
            VideoPreviewSource(),
            ImagePreviewSource(),
            AudioPreviewSource(),
            SignalPreviewSource(),
            TextPreviewSource()
        ]

        # ------ MediaTypeFactory ---------
        media_factory = MediaTypeFactory()

        # Register scanners
        for scanner in scanners:
            media_factory.register_scanner(scanner=scanner)

        # Register previews
        for preview in preview_sources:
            media_factory.register_preview_source(preview_source=preview)

        # Register as a singleton
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
