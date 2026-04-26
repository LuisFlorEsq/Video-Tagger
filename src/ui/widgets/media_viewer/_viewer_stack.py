from PySide6.QtCore import Signal
from PySide6.QtWidgets import QStackedWidget

from src.application.services.labeling_service import LabelingService
from src.application.services.navigation_service import NavigationService
from src.application.services.project_service import ProjectService

from src.core.logger import logger
from src.domain.models.media import MediaItem, MediaType
from src.domain.models.project import Project

from src.ui.widgets.media_viewer import (
    ImageViewer,
    AudioViewer,
    SignalViewer,
    TextViewer,
    VideoViewer,
)


class ViewerStack(QStackedWidget):
    """
    Owns one media widget per MediaType
    """

    item_labeled = Signal(MediaItem)  # emits MediaItem
    prev_requested = Signal()
    next_requested = Signal()
    back_requested = Signal()
    auto_saved = Signal()

    def __init__(
        self,
        labeling_service: LabelingService,
        project_service: ProjectService,
        available_labels: list | None = None,
        parent=None,
    ) -> None:

        super().__init__(parent)

        self._labeling_service = labeling_service
        self._project_service = project_service
        self._available_labels = list(available_labels or [])

        self._viewers: dict[MediaType, object] = {}
        self._current_viewer = None

        self._build_viewers()

    # ---- Construction ------

    def _build_viewers(self) -> None:
        kwargs = dict(
            labeling_service=self._labeling_service,
            project_service=self._project_service,
            available_labels=self._available_labels or None,
        )

        for mt, cls in [
            (MediaType.VIDEO, VideoViewer),
            (MediaType.IMAGE, ImageViewer),
            (MediaType.AUDIO, AudioViewer),
            (MediaType.SIGNAL, SignalViewer),
            (MediaType.TEXT, TextViewer),
        ]:
            viewer = cls(**kwargs)
            self._viewers[mt] = viewer
            self.addWidget(viewer)
            self._wire_viewer(viewer)

        # Start on video viewer
        self._current_viewer = self._viewers[MediaType.VIDEO]
        self.setCurrentWidget(self._current_viewer)

    def _wire_viewer(self, viewer) -> None:
        """
        Connect each viewer signal to the defined signals
        """

        viewer.item_labeled.connect(self.item_labeled)
        viewer.prev_requested.connect(self.prev_requested)
        viewer.next_requested.connect(self.next_requested)
        viewer.back_requested.connect(self.back_requested)
        viewer.auto_saved.connect(self.auto_saved)

    # --------- Public API ---------

    @staticmethod
    def _viewer_name(viewer) -> str:
        return viewer.__class__.__name__

    def load_item(self, item: MediaItem, project: Project) -> None:
        """
        Dispatches to the correct viewer based on item.media_type
        """

        viewer = self._viewers.get(item.media_type)
        if viewer is None:
            viewer = self._viewers[MediaType.VIDEO]  # Fallback to VIDEO viewer

        previous_viewer = self._current_viewer
        if previous_viewer is not None:
            logger.debug(
                "ViewerStack stopping viewer | reason=switch_viewer | viewer=%s",
                self._viewer_name(previous_viewer),
            )
            previous_viewer.stop()

        if self._current_viewer is not viewer:
            self._current_viewer = viewer
            self.setCurrentWidget(viewer)

        if self._current_viewer is None:
            self._current_viewer = viewer
            self.setCurrentWidget(viewer)

        viewer.load_item(item, project)

    def set_navigation_service(self, nav: NavigationService) -> None:
        for viewer in self._viewers.values():
            viewer.set_navigation_service(nav)

    def get_current_item(self) -> MediaItem:
        """Returns the active item regardless of type"""
        return self._current_viewer.get_current_item() if self._current_viewer else None

    def update_labels(self, labels: list) -> None:
        self._available_labels = list(labels)
        for viewer in self._viewers.values():
            viewer.update_labels(labels)

    def focus_label_list(self) -> None:
        if self._current_viewer:
            self._current_viewer.focus_label_list()

    def reset(self) -> None:
        for viewer in self._viewers.values():
            viewer.reset()
        self._current_viewer = self._viewers.get(
            MediaType.VIDEO
        )  # Fallback again to Video viewer
        if self._current_viewer is not None:
            self.setCurrentWidget(self._current_viewer)

    def stop_all_media(self, reason: str = "leave_fragment_view") -> None:
        for viewer in self._viewers.values():
            if hasattr(viewer, "stop_video"):
                logger.debug(
                    "ViewerStack stopping viewer | reason=%s | viewer=%s",
                    reason,
                    self._viewer_name(viewer),
                )
                viewer.stop_video()
            elif hasattr(viewer, "stop"):
                logger.debug(
                    "ViewerStack stopping viewer | reason=%s | viewer=%s",
                    reason,
                    self._viewer_name(viewer),
                )
                viewer.stop()
