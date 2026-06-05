from __future__ import annotations

import pytest

from src.application.services.export_service import ExportService
from src.application.services.labeling_service import LabelingService
from src.application.services.project_service import ProjectService
from src.domain.models.media import MediaType
from src.infrastructure.exporters import CsvExporter, JsonExporter
from src.infrastructure.repositories import JsonProjectRepository
from src.infrastructure.validators import SimpleLabelValidator


@pytest.mark.integration
def test_main_flow_create_label_save_reload_and_export(tmp_path, media_factory):
    source_folder = tmp_path / "videos"
    source_folder.mkdir()
    (source_folder / "clip_01.mp4").write_bytes(b"a")
    (source_folder / "clip_02.mp4").write_bytes(b"b")

    repository = JsonProjectRepository()
    project_service = ProjectService(repository=repository, media_factory=media_factory)
    labeling_service = LabelingService(SimpleLabelValidator())
    export_service = ExportService()
    export_service.register_exporter("csv", CsvExporter())
    export_service.register_exporter("json", JsonExporter())

    project = project_service.create_project_from_folder(source_folder, MediaType.VIDEO)
    assert project.get_total_count() == 2

    first_item = project.items[0]
    labeling_service.assign_label(first_item, project, "Etiqueta 1")

    project_path = tmp_path / "project.json"
    project_service.save_project(project, project_path)
    assert project_service.auto_save_project(project) is True

    reloaded = project_service.load_project(project_path)
    assert reloaded.get_total_count() == 2
    assert reloaded.items[0].label == "Etiqueta 1"

    csv_path = tmp_path / "export.csv"
    json_path = tmp_path / "export.json"
    export_service.export(reloaded, csv_path, "csv")
    export_service.export(reloaded, json_path, "json")

    assert csv_path.exists()
    assert json_path.exists()
