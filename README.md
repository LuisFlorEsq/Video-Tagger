# Video Frame Tagging

A desktop application for labeling and annotating video fragment datasets. Built with Python and PySide6, designed for research workflows at the Centro de Investigación en Computación — IPN.

---

## Overview

Video Frame Tagging lets you point the tool at a folder of video clips, assign categorical labels to each one, track your progress, and export the results as a structured CSV file ready for machine learning pipelines.

The workflow is intentionally linear: open a folder → review each fragment → assign a label → export. The application handles saving state between sessions so annotation work can be paused and resumed at any time.

---

## Features

- **Project-based workflow** — each folder of videos becomes a named project with persistent state saved to a JSON file
- **Fragment viewer** — plays each video clip with playback controls and a timeline scrubber
- **Label assignment** — click any label from the panel to tag the current fragment instantly
- **Navigation** — move forward and backward through fragments sequentially, with optional skip for unlabeled items
- **Auto-save** — labels are saved automatically 3 seconds after each assignment (requires the project to have been saved at least once)
- **Video sync** — detects new video files added to the project folder after the project was created and adds them as new fragments
- **CSV export** — exports fragment ID, filename, path, duration, label, and timestamps to a flat CSV file
- **Progress tracking** — progress bar and labeled/total counter visible at all times while a project is open

---

## Requirements

| Dependency | Version |
|---|---|
| Python | 3.10 or later |
| PySide6 | 6.x |
| OpenCV (`opencv-python`) | 4.x |
| pandas | 2.x |

Install all dependencies with:

```bash
pip install -r requirements.txt
```

---

## Project structure

```
├── main.py                          # Entry point
└── src/
    ├── domain/
    │   ├── interfaces.py            # Abstract interfaces (IProjectRepository, IVideoSource, …)
    │   └── models/
    │       ├── project.py           # Project entity
    │       ├── fragment.py          # Fragment entity
    │       └── label.py             # Label model
    ├── application/
    │   └── services/
    │       ├── project_service.py   # Project lifecycle (create, load, save, sync)
    │       ├── labeling_service.py  # Label assignment and validation
    │       ├── navigation_service.py# Fragment cursor (next, previous, position)
    │       └── export_service.py    # Export orchestration
    ├── infrastructure/
    │   ├── repositories.py          # JSON-based project persistence
    │   ├── exporters.py             # CSV and JSON exporters
    │   ├── scanners.py              # Filesystem video scanner
    │   ├── validators.py            # Label validation rules
    │   └── video.py                 # OpenCV video metadata reader
    ├── presentation/
    │   ├── styles.py                # Design tokens and component stylesheets
    │   └── widgets/
    │       ├── main_window.py       # Top-level window and view coordinator
    │       ├── project_browser.py   # Project and fragment list view
    │       ├── fragment_viewer.py   # Video playback and labeling view
    │       ├── label_panel.py       # Label picker panel
    │       └── video_player.py      # Video player widget
    └── core/
        ├── container.py             # Dependency injection container
        ├── video_loader.py          # Background video metadata loader thread
        └── qt_config.py             # Qt message handler and warning suppression
        |__ config.py                # Constants definition (default labels)
```

---

## Architecture

The application follows Clean Architecture with four layers. Dependencies point inward only — the UI never imports from infrastructure, and the domain has no knowledge of Qt or the filesystem.

```
Presentation  →  Application  →  Domain  ←  Infrastructure
(PySide6 UI)     (Services)     (Models)     (Files, OpenCV)
```

**Dependency injection** is handled by `container.py`. Infrastructure implementations are registered against domain interfaces at startup, and services receive their dependencies through constructor injection. Nothing is hardcoded — swapping the storage format or video backend requires only a change in the container registration.

---

## Getting started

### 1. Clone the repository

```bash
git clone https://github.com/LuisFlorEsq/Video-Tagger.git
cd Video-Tagger
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the application

```bash
python main.py
```

---

## Usage

### Creating a project

1. Click **Nuevo proyecto** in the sidebar.
2. Select the folder that contains your video fragments. The application scans for `.mp4`, `.avi`, `.mov`, `.mkv`, `.flv`, and `.wmv` files (case-insensitive).
3. The project is created in memory. Use **Guardar** to write it to a `.json` file before labeling if you want auto-save to work.

### Labeling fragments

1. Double-click any fragment in the list to open it in the viewer.
2. Click a label in the right panel to assign it. The status chip updates immediately.
3. Use **→** or **←** to move to the next or previous fragment. If a fragment has no label, you will be asked whether to skip it.
4. Use **Eliminar etiqueta actual** (small link at the bottom of the panel) to remove a label and return the fragment to unlabeled state.

### Filtering the list

The toolbar above the fragment list shows three filter pills: **Todos**, **Sin etiquetar**, and **Etiquetados**. Each pill shows the live count for that category. Click any pill to filter the list. The count label on the left updates to show how many items are visible out of the total.

### Saving a project

Use **Guardar** in the sidebar or `Ctrl+S` from the menu. The project is saved as a `.json` file. Once a save path exists, the application auto-saves silently 3 seconds after each label change.

### Syncing new videos

If you add video files to the project folder after the project was created, click **Sincronizar videos** in the sidebar. The button shows the count of detected new files. Confirming adds them as new fragments at the end of the list.

### Exporting to CSV

Click **Exportar CSV** in the sidebar or use `Ctrl+E` from the menu. The export includes one row per fragment with the following columns:

| Column | Description |
|---|---|
| `fragment_id` | Unique identifier (e.g. `fragment_003`) |
| `video_name` | Filename only |
| `video_path` | Full path to the video file |
| `start_time` | Start offset in seconds |
| `duration` | Duration in seconds |
| `label` | Assigned label, or empty string if unlabeled |
| `is_labeled` | Boolean |
| `notes` | Annotator notes (if any) |
| `created_at` | ISO 8601 timestamp |
| `modified_at` | ISO 8601 timestamp of last label change |

---

## Project file format

Projects are saved as `.json` files with the following structure:

```json
{
  "name": "my_dataset",
  "folder_path": "/path/to/videos",
  "save_path": "/path/to/my_dataset.json",
  "created_at": "2025-03-26T10:00:00",
  "modified_at": "2025-03-26T14:32:11",
  "fragments": [
    {
      "fragment_id": "fragment_001",
      "video_path": "/path/to/videos/clip_001.mp4",
      "start_time": 0.0,
      "duration": 1.0,
      "label": "Etiqueta 1",
      "notes": "",
      "created_at": "2025-03-26T10:00:00",
      "modified_at": "2025-03-26T14:30:05"
    }
  ]
}
```

---

## Supported video formats

`.mp4` · `.avi` · `.mov` · `.mkv` · `.flv` · `.wmv`

Both lowercase and uppercase extensions are detected.

---

## Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+N` | New project from folder |
| `Ctrl+O` | Open existing project |
| `Ctrl+S` | Save project |
| `Ctrl+E` | Export to CSV |
| `Ctrl+Q` | Quit |

---

## Known limitations

- The scanner only reads video files from the **top level** of the selected folder. Subdirectories are not traversed.
- Each fragment represents a fixed clip starting at `start_time = 0.0`. Splitting a long video into timed segments is not handled by the tool — pre-split clips are expected as input.
- The label list is currently defined at startup. There is no in-app UI for adding or renaming labels. To customize labels, modify the `DEFAULT_LABELS` constant in `src/presentation/widgets/label_panel.py` before running.

---

## License

Centro de Investigación en Computación — IPN. All rights reserved.

---

### TODO LIST

- [X] Add synchronized file updates linked to the project (partial progress saving).
- [X] Add an option to **update an existing project** instead of forcing the user to save it again.
- [X] Ensure the project is saved even if the **“Save Project”** button is not explicitly pressed.
- [X] Save the project when the `_on_back()` method is executed, when the application is closed, or prompt the user asking whether they want to save changes.
- [X] Add a button to return to the previous fragment, remove the current tag, and adjust the layout and size of the buttons.
- [] Add functionality to check the project status when resuming (reload the project’s saved state).
- [] Update the current logic to deactivate buttons when we are in the first and last fragment of the project.
- [] Create a portable executable
- [] Add an admin view to manage system configuration (e.g. manage available labels)
- [] Ensure that when the user clicks on "Cerrar Proyecto" all the metadata is cleared because if the user close the project and then try to exit the app with fragments unlabeled the system still has project data in memmory
- [] Consider to delete confirmation to exit with unlabeled fragments

