import pytest

from rascal2.widgets.startup import StartUpWidget
from tests.dialogs.test_project_dialog import MockParentWindow


@pytest.fixture
def setup_startup_widget():
    parent = MockParentWindow()
    startup_widget = StartUpWidget(parent)
    return startup_widget, parent


def test_startup_widget_initial_state(setup_startup_widget):
    """
    Tests the initial state of the start up widget.
    """
    startup_widget, _ = setup_startup_widget
    assert startup_widget.new_project_button.isEnabled()
    assert startup_widget.import_project_button.isEnabled()
    assert startup_widget.import_r1_button.isEnabled()

    assert startup_widget.new_project_label.text() == "New\nProject"
    assert startup_widget.import_project_label.text() == "Import Existing\nProject"
    assert startup_widget.import_r1_label.text() == "Import RasCAL-1\nProject"


@pytest.mark.parametrize("button", ["new_project_button", "import_project_button", "import_r1_button"])
def test_show_project_dialog_called(setup_startup_widget, button):
    """
    Tests the show_project_dialog method is called once.
    """
    startup_widget, parent = setup_startup_widget
    getattr(startup_widget, button).click()
    parent.show_project_dialog.assert_called_once()
