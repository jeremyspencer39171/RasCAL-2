"""Unit tests for the main window view."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PyQt6 import QtWidgets

from rascal2.settings import MDIGeometries, Settings
from rascal2.ui.view import MainWindowView


class MockFigureCanvas(QtWidgets.QWidget):
    """A mock figure canvas."""

    def draw(*args, **kwargs):
        pass


@pytest.fixture
def test_view():
    """An instance of MainWindowView."""
    with patch("rascal2.widgets.plot.FigureCanvas", return_value=MockFigureCanvas()):
        yield MainWindowView()


@pytest.mark.parametrize(
    "geometry",
    [
        ((1, 2, 196, 24, True), (1, 2, 196, 24, True), (1, 2, 196, 24, True), (1, 2, 196, 24, True)),
        ((1, 2, 196, 24, True), (3, 78, 196, 24, True), (1, 2, 204, 66, False), (12, 342, 196, 24, True)),
    ],
)
@patch("rascal2.ui.view.ProjectWidget.update_project_view")
@patch("rascal2.ui.view.MainWindowPresenter")
@patch("rascal2.ui.view.ControlsWidget.setup_controls")
class TestMDISettings:
    def test_reset_mdi(self, mock1, mock2, mock3, test_view, geometry):
        """Test that resetting the MDI works."""
        test_view.settings = Settings()
        test_view.setup_mdi()
        test_view.settings.mdi_defaults = MDIGeometries(
            plots=geometry[0], project=geometry[1], terminal=geometry[2], controls=geometry[3]
        )
        test_view.reset_mdi_layout()
        for window in test_view.mdi.subWindowList():
            # get corresponding MDIGeometries entry for the widget
            widget_name = window.windowTitle().lower().split(" ")[-1]
            w_geom = window.geometry()
            assert getattr(test_view.settings.mdi_defaults, widget_name) == (
                w_geom.x(),
                w_geom.y(),
                w_geom.width(),
                w_geom.height(),
                window.isMinimized(),
            )

    def test_set_mdi(self, mock1, mock2, mock3, test_view, geometry):
        """Test that setting the MDI adds the expected object to settings."""
        test_view.settings = Settings()
        test_view.setup_mdi()
        widgets_in_order = []

        for i, window in enumerate(test_view.mdi.subWindowList()):
            widgets_in_order.append(window.windowTitle().lower().split(" ")[-1])
            window.setGeometry(*geometry[i][0:4])
            if geometry[i][4] is True:
                window.showMinimized()

        test_view.save_mdi_layout()
        for i, widget in enumerate(widgets_in_order):
            window = test_view.mdi.subWindowList()[i]
            assert getattr(test_view.settings.mdi_defaults, widget) == (
                window.x(),
                window.y(),
                window.width(),
                window.height(),
                window.isMinimized(),
            )


def test_set_enabled(test_view):
    """Tests that the list of disabled elements are disabled on initialisation, and can be enabled."""
    for element in test_view.disabled_elements:
        assert not element.isEnabled()
    test_view.enable_elements()
    for element in test_view.disabled_elements:
        assert element.isEnabled()


@patch("PyQt6.QtWidgets.QFileDialog.getExistingDirectory")
def test_get_project_folder(mock_get_dir: MagicMock):
    """Test that getting a specified folder works as expected."""
    view = MainWindowView()
    mock_overwrite = MagicMock(return_value=True)

    tmp = tempfile.mkdtemp()
    view.presenter.create_project("test", tmp)
    mock_get_dir.return_value = tmp

    with patch.object(view, "show_confirm_dialog", new=mock_overwrite):
        assert view.get_project_folder() == tmp

    # check overwrite is triggered if project already in folder
    Path(tmp, "controls.json").touch()
    with patch.object(view, "show_confirm_dialog", new=mock_overwrite):
        assert view.get_project_folder() == tmp
    mock_overwrite.assert_called_once()

    def change_dir(*args, **kwargs):
        """Change directory so mocked save_as doesn't recurse forever."""
        mock_get_dir.return_value = "OTHERPATH"

    # check not saved if overwrite is cancelled
    # to avoid infinite recursion (which only happens because of the mock),
    # set the mock to change the directory to some other path once called
    mock_overwrite = MagicMock(return_value=False, side_effect=change_dir)

    with patch.object(view, "show_confirm_dialog", new=mock_overwrite):
        assert view.get_project_folder() == "OTHERPATH"

    mock_overwrite.assert_called_once()
