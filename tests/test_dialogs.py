from unittest.mock import MagicMock, patch

import pytest
from PyQt6 import QtWidgets

from rascal2.dialogs.project_dialog import ProjectDialog


class MockPresenter(QtWidgets.QMainWindow):
    def create_project(self, name: str, folder: str):
        pass


class MockParentWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.presenter = MockPresenter()
        self.toolbar = self.addToolBar("ToolBar")
        self.toolbar.setEnabled(False)
        self.show_project_dialog = MagicMock()


@pytest.fixture
def setup_project_dialog_widget():
    parent = MockParentWindow()
    project_dialog = ProjectDialog(parent)
    return project_dialog, parent


def test_project_dialog_initial_state(setup_project_dialog_widget):
    """
    Tests the inital state of the ProjectDialog class.
    """
    project_dialog, _ = setup_project_dialog_widget

    assert project_dialog.isModal()
    assert project_dialog.minimumWidth() == 700

    assert project_dialog.create_button.isEnabled()
    assert project_dialog.cancel_button.isEnabled()
    assert project_dialog.browse_button.isEnabled()

    assert project_dialog.create_button.text() == " Create"
    assert project_dialog.cancel_button.text() == " Cancel"
    assert project_dialog.browse_button.text() == " Browse"

    assert project_dialog.project_name.placeholderText() == "Enter project name"
    assert project_dialog.project_name_label.text() == "Project Name:"
    assert project_dialog.project_name_error.text() == "Project name needs to be specified."
    assert project_dialog.project_name_error.isHidden()

    assert project_dialog.project_folder.placeholderText() == "Select project folder"
    assert project_dialog.project_folder_label.text() == "Project Folder:"
    assert project_dialog.project_folder_error.text() == "An empty project folder needs to be selected."
    assert project_dialog.project_folder_error.isHidden()
    assert project_dialog.project_folder.isReadOnly()


@patch("os.listdir")
def test_inline_error_msgs(mock_listdir, setup_project_dialog_widget):
    """
    Tests the project name and folder inline errors.
    """
    project_dialog, _ = setup_project_dialog_widget

    mock_listdir.return_value = [".hiddenfile"]

    # tests the project name and folder inline errors.
    project_dialog.create_button.click()

    assert not project_dialog.project_name_error.isHidden()
    assert not project_dialog.project_folder_error.isHidden()

    # tests the project name inline error.
    project_dialog.project_folder.setText("test-folder")
    project_dialog.folder_path = "test-folder"
    project_dialog.create_button.click()

    assert not project_dialog.project_name_error.isHidden()
    assert project_dialog.project_folder_error.isHidden()

    # tests the project folder inline error.
    project_dialog.project_name.setText("test-name")
    project_dialog.project_folder.setText("")
    project_dialog.folder_path = ""
    project_dialog.create_button.click()

    assert project_dialog.project_name_error.isHidden()
    assert not project_dialog.project_folder_error.isHidden()


@patch("os.listdir")
@patch.object(MockPresenter, "create_project")
def test_create_button(mock_create_project, mock_listdir, setup_project_dialog_widget):
    """
    Tests create button on the ProjectDialog class.
    """
    project_dialog, _ = setup_project_dialog_widget

    mock_listdir.return_value = []

    project_dialog.project_name.setText("test-name")
    project_dialog.project_folder.setText("test-folder")
    project_dialog.folder_path = "test-folder"
    project_dialog.create_button.click()
    mock_create_project.assert_called_once()
    assert project_dialog.parent().toolbar.isEnabled()


def test_cancel_button(setup_project_dialog_widget):
    """
    Tests cancel button on the ProjectDialog class.
    """
    project_dialog, _ = setup_project_dialog_widget

    with patch.object(project_dialog, "reject", wraps=project_dialog.reject) as mock_reject:
        project_dialog.cancel_button.click()
        mock_reject.assert_called_once()


@patch("os.listdir")
@patch("PyQt6.QtWidgets.QFileDialog.getExistingDirectory")
def test_browse_button(mock_get_existing_directory, mock_listdir, setup_project_dialog_widget):
    """
    Tests the browse button on the ProjectDialog class.
    """
    project_dialog, _ = setup_project_dialog_widget

    # When empty folder is selected.
    mock_get_existing_directory.return_value = "/test/folder/path"
    mock_listdir.return_value = [".hiddenfile"]

    project_dialog.browse_button.click()

    assert project_dialog.project_folder.text() == "/test/folder/path"
    assert project_dialog.project_folder_error.isHidden()

    # When a non empty folder is selected.
    mock_listdir.return_value = [".hiddenfile", "testfile"]

    project_dialog.browse_button.click()

    assert project_dialog.project_folder.text() == ""
    assert not project_dialog.project_folder_error.isHidden()
