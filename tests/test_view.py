"""Unit tests for the main window view."""

from unittest.mock import patch

import pytest

from rascal2.core.settings import MDIGeometries, Settings
from rascal2.ui.view import MainWindowView


@pytest.mark.parametrize(
    "geometry",
    [
        ((1, 2, 196, 24, True), (1, 2, 196, 24, True), (1, 2, 196, 24, True), (1, 2, 196, 24, True)),
        ((1, 2, 196, 24, True), (3, 78, 196, 24, True), (1, 2, 204, 66, False), (12, 342, 196, 24, True)),
    ],
)
@patch("rascal2.ui.view.MainWindowPresenter")
@patch("rascal2.ui.view.ControlsWidget.setup_controls")
class TestMDISettings:
    def test_reset_mdi(self, mock1, mock2, geometry):
        """Test that resetting the MDI works."""
        view = MainWindowView()
        view.settings = Settings()
        view.setup_mdi()
        view.settings.mdi_defaults = MDIGeometries(
            plots=geometry[0], project=geometry[1], terminal=geometry[2], controls=geometry[3]
        )
        view.reset_mdi_layout()
        for window in view.mdi.subWindowList():
            # get corresponding MDIGeometries entry for the widget
            widget_name = window.windowTitle().lower().split(" ")[-1]
            wgeom = window.geometry()
            assert getattr(view.settings.mdi_defaults, widget_name) == (
                wgeom.x(),
                wgeom.y(),
                wgeom.width(),
                wgeom.height(),
                window.isMinimized(),
            )

    def test_set_mdi(self, mock1, mock2, geometry):
        """Test that setting the MDI adds the expected object to settings."""
        view = MainWindowView()
        view.settings = Settings()
        view.setup_mdi()
        widgets_in_order = []

        for i, window in enumerate(view.mdi.subWindowList()):
            widgets_in_order.append(window.windowTitle().lower().split(" ")[-1])
            window.setGeometry(*geometry[i][0:4])
            if geometry[i][4] is True:
                window.showMinimized()

        view.save_mdi_layout()
        for i, widget in enumerate(widgets_in_order):
            window = view.mdi.subWindowList()[i]
            assert getattr(view.settings.mdi_defaults, widget) == (
                window.x(),
                window.y(),
                window.width(),
                window.height(),
                window.isMinimized(),
            )
