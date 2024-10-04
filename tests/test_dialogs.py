from unittest.mock import MagicMock, patch

import pytest
from PyQt6 import QtCore, QtWidgets

from rascal2.core.settings import Settings, SettingsGroups
from rascal2.dialogs.project_dialog import ProjectDialog
from rascal2.dialogs.settings_dialog import SettingsDialog, SettingsTab
from rascal2.widgets.inputs import ValidatedInputWidget


class MockPresenter:
    def __init__(self):
        super().__init__()
        self.model = MagicMock()
        self.model.save_path = ""

    def create_project(self, name: str, folder: str):
        pass


class MockParentWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.presenter = MockPresenter()
        self.settings = Settings(editor_fontsize=15, terminal_fontsize=8)
        self.save_path = ""
        self.show_project_dialog = MagicMock()


@pytest.fixture
def setup_project_dialog_widget():
    parent = MockParentWindow()
    project_dialog = ProjectDialog(parent)
    return project_dialog, parent


@pytest.fixture
def settings_dialog_with_parent():
    parent = MockParentWindow()
    settings_dialog = SettingsDialog(parent)
    return settings_dialog, parent


def test_project_dialog_initial_state(setup_project_dialog_widget):
    """
    Tests the initial state of the ProjectDialog class.
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


def test_settings_dialog_initialisation(settings_dialog_with_parent):
    """Ensure the settings dialog is initialised with the correct layout"""
    settings_dialog, _ = settings_dialog_with_parent
    layout = settings_dialog.layout()

    # Check tab layout exists with the correct number of tabs
    tab_layout = layout.itemAt(0).widget()
    assert isinstance(tab_layout, QtWidgets.QTabWidget)
    assert tab_layout.count() == 1

    # Check button layout exists with the correct buttons
    button_layout = layout.itemAt(1)
    for button in [settings_dialog.accept_button, settings_dialog.cancel_button, settings_dialog.reset_button]:
        assert button_layout.indexOf(button) != -1


def test_settings_dialog_accept_button(settings_dialog_with_parent):
    """Ensure the accept button saves the changed settings."""
    settings_dialog, parent = settings_dialog_with_parent
    new_font_size = 50
    settings_dialog.settings.editor_fontsize = new_font_size
    with patch.object(Settings, "save") as mock_save:
        settings_dialog.accept_button.click()
        mock_save.assert_called_once_with(parent.save_path)
    assert parent.settings.editor_fontsize == new_font_size
    assert settings_dialog.result() == 1


def test_settings_dialog_cancel_button(settings_dialog_with_parent):
    """Ensure the cancel button rejects the changed settings."""
    settings_dialog, parent = settings_dialog_with_parent
    settings_dialog.settings.editor_fontsize = 50
    settings_dialog.cancel_button.click()
    assert parent.settings.editor_fontsize == 15
    assert settings_dialog.result() == 0


def test_settings_dialog_reset_button(settings_dialog_with_parent):
    """Ensure the reset button changes the settings to the global defaults."""
    settings_dialog, parent = settings_dialog_with_parent
    new_font_size = 50
    settings_dialog.settings.editor_fontsize = new_font_size
    with patch("rascal2.dialogs.settings_dialog.delete_local_settings") as mock_delete:
        settings_dialog.reset_button.click()
        mock_delete.assert_called_once_with(parent.save_path)
    assert parent.settings == Settings()
    assert settings_dialog.result() == 1


@pytest.mark.parametrize(
    "tab_group, settings_labels",
    [
        (SettingsGroups.General, ["Style", "Editor Fontsize"]),
    ],
)
def test_settings_dialog_tabs(settings_dialog_with_parent, tab_group, settings_labels):
    """Test the settings dialog tabs contain the correct settings"""
    settings_dialog, _ = settings_dialog_with_parent
    tab = SettingsTab(settings_dialog, tab_group)
    layout = tab.layout()

    num_rows = layout.rowCount()
    assert num_rows == len(settings_labels)
    assert layout.columnCount() == 2

    for row in range(num_rows):
        label = layout.itemAtPosition(row, 0).widget()
        assert isinstance(label, QtWidgets.QLabel)
        assert label.text() == settings_labels[row]
        assert isinstance(layout.itemAtPosition(row, 1).widget(), ValidatedInputWidget)


@pytest.mark.parametrize(
    "tab_group, test_values",
    [
        # Test for non-default style later, when another is added
        (SettingsGroups.General, {"style": "light", "editor_fontsize": 5, "terminal_fontsize": 5}),
    ],
)
def test_settings_dialog_widgets(settings_dialog_with_parent, tab_group, test_values):
    """Test the widgets are connected to a slot that correctly changes the corresponding setting."""
    settings_dialog, _ = settings_dialog_with_parent
    tab = SettingsTab(settings_dialog, tab_group)

    # We block the signal and then emit it later as for some widgets the "edited_signal" signal
    # is not emitted when changing through "set_data"
    for setting, widget in tab.widgets.items():
        widget_value = test_values[setting]
        with QtCore.QSignalBlocker(widget):
            try:
                widget.set_data(widget_value)
            except TypeError:
                widget.set_data(str(widget_value))
                data_input = str(widget_value)
            else:
                data_input = widget_value

        # Some signals require the data, some do not
        try:
            widget.edited_signal.emit(data_input)
        except TypeError:
            widget.edited_signal.emit()

        assert getattr(settings_dialog.settings, setting) == widget_value
