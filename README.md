# Video-Tagger

**Video-Tagger** is a desktop video annotation tool that allows users to load local video files, inspect individual frames, and assign tags for labeling, analysis, or dataset creation.

## TODO:

- [X] Add synchronized file updates linked to the project (partial progress saving).
- [X] Add an option to **update an existing project** instead of forcing the user to save it again.
- [X] Ensure the project is saved even if the **“Save Project”** button is not explicitly pressed.
- [X] Save the project when the `_on_back()` method is executed, when the application is closed, or prompt the user asking whether they want to save changes.
- [X] Add a button to return to the previous fragment, remove the current tag, and adjust the layout and size of the buttons.
- [] Add functionality to check the project status when resuming (reload the project’s saved state).
- [] Update the current logic to deactivate buttons when we are in the first and last fragment of the project.
- [] Create a portable executable
- [] Add an admin view to manage system configuration (e.g. manage available labels)