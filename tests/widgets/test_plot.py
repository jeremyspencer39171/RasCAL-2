from unittest.mock import MagicMock, patch

import pytest
import RATapi
from PyQt6 import QtWidgets

from rascal2.widgets.plot import ContourPlotWidget, PlotWidget, RefSLDWidget


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
    plot_widget.parent_model = MagicMock()
    plot_widget.reflectivity_plot = MagicMock()

    return plot_widget


@pytest.fixture
def sld_widget():
    sld_widget = RefSLDWidget(view)
    sld_widget.canvas = MagicMock()

    return sld_widget


@pytest.fixture
def contour_widget():
    contour_widget = ContourPlotWidget(view)
    contour_widget.canvas = MagicMock()

    return contour_widget


def test_plot_widget_update_plots(plot_widget):
    """Test that the plots are updated correctly when update_plots is called."""
    plot_widget.update_plots(MagicMock(), MagicMock(spec=RATapi.outputs.Results))

    assert not plot_widget.bayes_plots_button.isVisibleTo(plot_widget)
    plot_widget.reflectivity_plot.plot.assert_called_once()
    plot_widget.reflectivity_plot.reset_mock()

    plot_widget.update_plots(MagicMock(), MagicMock(spec=RATapi.outputs.BayesResults))

    assert plot_widget.bayes_plots_button.isVisibleTo(plot_widget)
    plot_widget.reflectivity_plot.plot.assert_called_once()


def test_ref_sld_toggle_setting(sld_widget):
    """Test that plot settings are hidden when the button is toggled."""
    assert not sld_widget.plot_controls.isVisibleTo(sld_widget)
    sld_widget.toggle_button.toggle()
    assert sld_widget.plot_controls.isVisibleTo(sld_widget)
    sld_widget.toggle_button.toggle()
    assert not sld_widget.plot_controls.isVisibleTo(sld_widget)


@patch("RATapi.plotting.RATapi.plotting.plot_ref_sld_helper")
def test_ref_sld_plot_event(mock_plot_sld, sld_widget):
    """Test that plot helper recieved correct flags from UI."""
    data = RATapi.events.PlotEventData()
    data.contrastNames = ["Hello"]

    assert sld_widget.current_plot_data is None
    sld_widget.plot_event(data)
    assert sld_widget.current_plot_data is data
    mock_plot_sld.assert_called_with(
        data,
        sld_widget.figure,
        delay=False,
        linear_x=False,
        q4=False,
        show_error_bar=True,
        show_grid=False,
        show_legend=True,
    )
    sld_widget.canvas.draw.assert_called_once()
    data.contrastNames = []
    sld_widget.plot_event(data)
    mock_plot_sld.assert_called_with(
        data,
        sld_widget.figure,
        delay=False,
        linear_x=False,
        q4=False,
        show_error_bar=True,
        show_grid=False,
        show_legend=False,
    )
    data.contrastNames = ["Hello"]
    sld_widget.x_axis.setCurrentText("Linear")
    sld_widget.y_axis.setCurrentText("Q^4")
    sld_widget.show_error_bar.setChecked(False)
    sld_widget.show_grid.setChecked(True)
    sld_widget.show_legend.setChecked(False)
    mock_plot_sld.assert_called_with(
        data,
        sld_widget.figure,
        delay=False,
        linear_x=True,
        q4=True,
        show_error_bar=False,
        show_grid=True,
        show_legend=False,
    )


@patch("RATapi.inputs.make_input")
def test_ref_sld_plot(mock_inputs, sld_widget):
    """Test that the plot is made when given a plot event."""
    project = MagicMock()
    result = MagicMock()
    data = MagicMock
    with patch("RATapi.events.PlotEventData", return_value=data):
        assert sld_widget.current_plot_data is None
        sld_widget.plot(project, result)
        assert sld_widget.current_plot_data is data
        sld_widget.canvas.draw.assert_called_once()


@patch("RATapi.plotting.RATapi.plotting.plot_contour")
def test_contour_plot_fit_names(mock_plot_contour, contour_widget):
    """Test that the contour plot widget plots when fit names are selected."""
    bayes_results = MagicMock(spec=RATapi.outputs.BayesResults)
    bayes_results.fitNames = ["A", "B", "C"]

    contour_widget.plot(None, bayes_results)
    contour_widget.x_param_box.setCurrentText("A")
    contour_widget.y_param_box.setCurrentText("B")

    mock_plot_contour.assert_called_once()
    mock_plot_contour.reset_mock()

    contour_widget.y_param_box.setCurrentText("C")
    mock_plot_contour.assert_called_once()


def test_contour_plot_fitnames(contour_widget):
    """Test that the names in each combobox are the results fitnames."""
    bayes_results = MagicMock(spec=RATapi.outputs.BayesResults)
    bayes_results.fitNames = ["A", "B", "C"]

    contour_widget.plot(None, bayes_results)

    for combo_box in [contour_widget.x_param_box, contour_widget.y_param_box]:
        assert [combo_box.itemText(i) for i in range(combo_box.count())] == ["", "A", "B", "C"]

    bayes_results.fitNames = ["A", "D"]
    contour_widget.plot(None, bayes_results)
    for combo_box in [contour_widget.x_param_box, contour_widget.y_param_box]:
        assert [combo_box.itemText(i) for i in range(combo_box.count())] == ["", "A", "D"]
