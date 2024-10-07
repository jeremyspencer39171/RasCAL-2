from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import pytest
from PyQt6 import QtWidgets

from rascal2.dialogs.project_dialog import PROJECT_FILES, LoadDialog, LoadR1Dialog, NewProjectDialog, StartupDialog


class MockParentWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.presenter = MagicMock()
        self.toolbar = self.addToolBar("ToolBar")
        self.toolbar.setEnabled(False)
        self.show_project_dialog = MagicMock()


view = MockParentWindow()


@pytest.mark.parametrize(
    ("dialog", "num_widgets"),
    (
        [NewProjectDialog, 2],
        [LoadDialog, 1],
        [LoadR1Dialog, 1],
    ),
)
def test_project_dialog_initial_state(dialog, num_widgets):
    """
    Tests that each dialog has expected initial state.
    """
    with patch("rascal2.dialogs.project_dialog.update_recent_projects", return_value=[]):
        project_dialog = dialog(view)

    assert project_dialog.isModal()
    assert project_dialog.minimumWidth() == 700

    assert project_dialog.layout().count() == num_widgets + 2  # +2 for the buttons layout and a stretch
    buttons = project_dialog.layout().itemAt(num_widgets + 1).layout()
    assert isinstance(buttons, QtWidgets.QHBoxLayout)
    assert buttons.count() == 2
    assert buttons.itemAt(1).widget().text() == " Cancel"
    if isinstance(project_dialog, NewProjectDialog):
        assert buttons.itemAt(0).widget().text() == " Create"
    else:
        assert buttons.itemAt(0).widget().text() == " Load"

    if project_dialog == NewProjectDialog:
        assert project_dialog.project_name.placeholderText() == "Enter project name"
        assert project_dialog.project_name_label.text() == "Project Name:"
        assert project_dialog.project_name_error.text() == "Project name needs to be specified."
        assert project_dialog.project_name_error.isHidden()

    if dialog == LoadR1Dialog:
        assert project_dialog.project_folder.placeholderText() == "Select RasCAL-1 file"
        assert project_dialog.project_folder_label.text() == "RasCAL-1 file:"
    else:
        assert project_dialog.project_folder.placeholderText() == "Select project folder"
        assert project_dialog.project_folder_label.text() == "Project Folder:"
    assert project_dialog.project_folder_error.isHidden()
    assert project_dialog.project_folder.isReadOnly()


@pytest.mark.parametrize("name, name_valid", [("", False), ("Project", True)])
@pytest.mark.parametrize("folder, folder_valid", [("", False), ("Folder", True)])
@pytest.mark.parametrize("other_folder_error", [True, False])
def test_create_button(name, name_valid, folder, folder_valid, other_folder_error):
    """
    Tests project creation on the NewProjectDialog class.
    """
    project_dialog = NewProjectDialog(view)
    mock_create = view.presenter.create_project = MagicMock()

    create_button = project_dialog.layout().itemAt(3).layout().itemAt(0).widget()

    project_dialog.project_name.setText(name)
    project_dialog.project_folder.setText(folder)
    if other_folder_error:
        project_dialog.set_folder_error("Folder error!!")

    create_button.click()

    if name_valid and folder_valid and not other_folder_error:
        mock_create.assert_called_once()
    else:
        mock_create.assert_not_called()


@pytest.mark.parametrize("widget", [LoadDialog, LoadR1Dialog])
@pytest.mark.parametrize("folder, folder_valid", [("", False), ("Folder", True)])
@pytest.mark.parametrize("other_folder_error", [True, False])
def test_load_button(widget, folder, folder_valid, other_folder_error):
    """
    Tests project loading on the LoadDialog and LoadR1Dialog class.
    """

    with patch("rascal2.dialogs.project_dialog.update_recent_projects", return_value=[]):
        project_dialog = widget(view)
    if widget == LoadDialog:
        mock_load = view.presenter.load_project = MagicMock()
    else:
        mock_load = view.presenter.load_r1_project = MagicMock()
    load_button = project_dialog.layout().itemAt(2).layout().itemAt(0).widget()

    project_dialog.project_folder.setText(folder)
    if other_folder_error:
        project_dialog.set_folder_error("Folder error!!")

    load_button.click()

    if folder_valid and not other_folder_error:
        mock_load.assert_called_once()
        assert project_dialog.parent().toolbar.isEnabled()
    else:
        mock_load.assert_not_called()


def test_cancel_button():
    """
    Tests cancel button on the StartupDialog class.
    """
    project_dialog = StartupDialog(view)

    cancel_button = project_dialog.layout().itemAt(2).layout().itemAt(0).widget()

    with patch.object(project_dialog, "reject", wraps=project_dialog.reject) as mock_reject:
        cancel_button.click()
        mock_reject.assert_called_once()


def test_folder_selector():
    """
    Tests the folder selector and verification on the StartupDialog class.
    """
    project_dialog = StartupDialog(view)
    project_dialog.folder_selector = MagicMock()
    project_dialog.folder_selector.return_value = "/test/folder/path"

    # When folder verification succeeds.
    project_dialog.open_folder_selector()

    assert project_dialog.project_folder.text() == "/test/folder/path"
    assert project_dialog.project_folder_error.isHidden()

    # When folder verification fails.
    def error(folder_path):
        raise ValueError("Folder verification error!")

    project_dialog.verify_folder = error

    project_dialog.open_folder_selector()

    assert project_dialog.project_folder.text() == ""
    assert project_dialog.project_folder_error.text() == "Folder verification error!"
    assert not project_dialog.project_folder_error.isHidden()


@pytest.mark.parametrize(
    "recent",
    [
        [],
        ["proj1"],
        ["proj1", "proj2"],
        ["proj1", "proj2", "proj3", "invisible1", "invisible2"],
    ],
)
def test_recent_projects(recent):
    """Tests that the Recent Projects list is as expected."""

    with patch("rascal2.dialogs.project_dialog.update_recent_projects", return_value=recent):
        project_dialog = LoadDialog(view)

    assert project_dialog.layout().count() == (4 if recent else 3)

    if recent:
        recent_projects = project_dialog.layout().itemAt(1).layout()
        assert recent_projects.count() == min(len(recent) + 1, 4)

        for i, label in enumerate(["Recent projects:"] + recent[0:3]):
            assert label in recent_projects.itemAt(i).widget().text()


@pytest.mark.parametrize(
    "contents, has_project",
    [
        ([], False),
        (["file.txt, settings.json", "data/"], False),
        (["controls.json"], True),
        (["controls.json", "logs/", "plots/", ".otherfile"], True),
    ],
)
def test_verify_folder(contents, has_project):
    """Test folder verification for create and load widgets."""
    with TemporaryDirectory() as tmp:
        for file in contents:
            Path(tmp, file).touch()

        if has_project:
            LoadDialog(view).verify_folder(tmp)
            with pytest.raises(ValueError, match="Folder already contains a project."):
                NewProjectDialog(view).verify_folder(tmp)
        else:
            NewProjectDialog(view).verify_folder(tmp)
            with pytest.raises(ValueError, match="No project found in this folder."):
                LoadDialog(view).verify_folder(tmp)


def test_load_invalid_json():
    """If project loading produces an error (which it does for invalid JSON), raise that error in the textbox."""

    def error(dir):
        raise ValueError("Project load error!")

    view.presenter.load_project = error
    dialog = LoadDialog(view)
    with TemporaryDirectory() as tmp:
        for file in PROJECT_FILES:
            Path(tmp, file).touch()

        dialog.project_folder.setText(tmp)
        dialog.load_project()

    assert not dialog.project_folder_error.isHidden()
    assert dialog.project_folder_error.text() == "Project load error!"


def test_load_recent_project():
    """Ensure that the load_recent_project slot loads the project it was initialised with."""
    dialog = LoadDialog(view)
    view.presenter.load_project = MagicMock()

    with TemporaryDirectory() as tmp:
        for file in PROJECT_FILES:
            Path(tmp, file).touch()

        dialog.load_recent_project(tmp)()
        assert dialog.project_folder.text() == tmp
        view.presenter.load_project.assert_called_once_with(tmp)
