# Video-Tagger

**Video-Tagger** is a desktop video annotation tool that allows users to load local video files, inspect individual frames, and assign tags for labeling, analysis, or dataset creation.

## TODO

* Add an option to **update an existing project** instead of forcing the user to save it again.
* Ensure the project is saved even if the **“Save Project”** button is not explicitly pressed.
* Add a button to return to the previous fragment, remove the current tag, and adjust the layout and size of the buttons.
* Save the project when the `_on_back()` method is executed, when the application is closed, or prompt the user asking whether they want to save changes.
* Change the current logic so that the **Details (Status)** panel is updated only after pressing **“Save and Continue”**, or update it on view entry while updating only the tag panel when a tag is selected.
* Add synchronized file updates linked to the project (partial progress saving).
* Add functionality to check the project status when resuming (reload the project’s saved state).