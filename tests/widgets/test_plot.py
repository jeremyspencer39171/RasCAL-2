from unittest.mock import MagicMock, patch

import pytest
import RATapi
from PyQt6 import QtWidgets

from rascal2.widgets.plot import PlotWidget


class MockWindowView(QtWidgets.QMainWindow):
    """A mock MainWindowView class."""

    def __init__(self):
        super().__init__()
        self.presenter = MagicMock()
        self.presenter.model = MagicMock()


view = MockWindowView()


@pytest.fixture
def plot_widget():
    plot_widget = PlotWidget(view)
    plot_widget.canvas = MagicMock()

    return plot_widget


def test_toggle_setting(plot_widget):
    """Test that plot settings are hidden when the button is toggled."""
    assert not plot_widget.plot_controls.isVisibleTo(plot_widget)
    plot_widget.toggle_button.toggle()
    assert plot_widget.plot_controls.isVisibleTo(plot_widget)
    plot_widget.toggle_button.toggle()
    assert not plot_widget.plot_controls.isVisibleTo(plot_widget)


@patch("RATapi.plotting.RATapi.plotting.plot_ref_sld_helper")
def test_plot_event(mock_plot_sld, plot_widget):
    """Test that plot helper recieved correct flags from UI ."""
    data = RATapi.events.PlotEventData()
    data.contrastNames = ["Hello"]

    assert plot_widget.current_plot_data is None
    plot_widget.plot_event(data)
    assert plot_widget.current_plot_data is data
    mock_plot_sld.assert_called_with(
        data,
        plot_widget.figure,
        delay=False,
        linear_x=False,
        q4=False,
        show_error_bar=True,
        show_grid=False,
        show_legend=True,
    )
    plot_widget.canvas.draw.assert_called_once()
    data.contrastNames = []
    plot_widget.plot_event(data)
    mock_plot_sld.assert_called_with(
        data,
        plot_widget.figure,
        delay=False,
        linear_x=False,
        q4=False,
        show_error_bar=True,
        show_grid=False,
        show_legend=False,
    )
    data.contrastNames = ["Hello"]
    plot_widget.x_axis.setCurrentText("Linear")
    plot_widget.y_axis.setCurrentText("Q^4")
    plot_widget.show_error_bar.setChecked(False)
    plot_widget.show_grid.setChecked(True)
    plot_widget.show_legend.setChecked(False)
    mock_plot_sld.assert_called_with(
        data,
        plot_widget.figure,
        delay=False,
        linear_x=True,
        q4=True,
        show_error_bar=False,
        show_grid=True,
        show_legend=False,
    )


@patch("RATapi.inputs.make_input")
def test_plot(mock_inputs, plot_widget):
    """Test that plot settings are hidden when the button is toggled."""
    project = MagicMock()
    result = MagicMock()
    data = MagicMock
    with patch("RATapi.events.PlotEventData", return_value=data):
        assert plot_widget.current_plot_data is None
        plot_widget.plot(project, result)
        assert plot_widget.current_plot_data is data
        plot_widget.canvas.draw.assert_called_once()
