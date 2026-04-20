from src.domain.models.project import Project

def format_project_progress(project: Project, summary: dict) -> str:
    return (
        f"{project.name} — "
        f"{summary['labeled']}/{summary['total_fragments']} etiquetados "
        f"({summary['progress_percentage']:.1f}%)"
    )


def format_project_badge(summary: dict) -> str:
    return f"{summary['labeled']} / {summary['total_fragments']} etiquetados"


def format_project_stats(summary: dict) -> str:
    return (
        f"{summary['labeled']}/{summary['total_fragments']} "
        f"etiquetados ({summary['progress_percentage']:.0f}%)"
    )