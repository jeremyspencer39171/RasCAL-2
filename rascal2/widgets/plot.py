"""The Plot MDI widget."""

from abc import abstractmethod
from inspect import isclass
from typing import Optional, Union

import RATapi
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6 import QtCore, QtGui, QtWidgets

from rascal2.config import path_for


class PlotWidget(QtWidgets.QWidget):
    """The MDI plot widget."""

    def __init__(self, parent):
        super().__init__(parent)

        self.parent_model = parent.presenter.model
        self.parent_model.results_updated.connect(
            lambda: self.update_plots(self.parent_model.project, self.parent_model.results)
        )

        layout = QtWidgets.QVBoxLayout()

        self.bayes_plots_dialog = BayesPlotsDialog(parent)
        self.bayes_plots_dialog.setWindowTitle("Bayes Results")

        button_layout = QtWidgets.QHBoxLayout()
        self.bayes_plots_button = QtWidgets.QPushButton("View Bayes plots")
        self.bayes_plots_button.setVisible(False)
        self.bayes_plots_button.pressed.connect(self.bayes_plots_dialog.exec)

        button_layout.addWidget(self.bayes_plots_button)
        button_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.reflectivity_plot = RefSLDWidget(self)
        layout.addLayout(button_layout)
        layout.addWidget(self.reflectivity_plot)

        self.setLayout(layout)

    def update_plots(self, project: RATapi.Project, results: RATapi.outputs.Results | RATapi.outputs.BayesResults):
        """Update the plot widget to match the parent model."""
        self.reflectivity_plot.plot(project, results)
        self.bayes_plots_dialog.results_outdated = True
        self.bayes_plots_button.setVisible(isinstance(results, RATapi.outputs.BayesResults))

    def plot_event(self, event):
        """Handle plot event data."""
        self.reflectivity_plot.plot_event(event)

    def clear(self):
        """Clear the Ref/SLD canvas."""
        self.reflectivity_plot.clear()


class BayesPlotsDialog(QtWidgets.QDialog):
    """The modal dialog for the Bayes plots."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent_model = parent.presenter.model

        layout = QtWidgets.QVBoxLayout()

        self.plot_tabs = QtWidgets.QTabWidget()

        # store bool for whether plots represent the current results object
        self.results_outdated = True

        plots = {
            "Corner Plot": CornerPlotWidget,
            "Contour Plots": ContourPlotWidget,
            "Posteriors": HistPlotWidget,
            "Diagnostics": ChainPlotWidget,
        }

        for plot_type, plot_widget in plots.items():
            self.add_tab(plot_type, plot_widget)

        layout.addWidget(self.plot_tabs)

        self.setLayout(layout)

        self.setModal(True)

    def add_tab(self, plot_type: str, plot_widget: "AbstractPlotWidget"):
        """Add a widget as a tab to the plot widget.

        Parameters
        ----------
        plot_type : str
            The name of the plot type.
        plot_widget : AbstractPlotWidget
            The plot widget to add as a tab.

        """
        # create widget instance if a widget class handle was given
        # rather than an instance
        if isclass(plot_widget):
            plot_widget = plot_widget(self)

        self.plot_tabs.addTab(plot_widget, plot_type)

        if self.parent_model.results is not None:
            plot_widget.plot(self.parent_model.project, self.parent_model.results)

    def exec(self):
        """Update plots if needed and execute the dialog."""
        if self.results_outdated:
            for index in range(0, self.plot_tabs.count()):
                self.plot_tabs.widget(index).plot(self.parent_model.project, self.parent_model.results)
            self.results_outdated = False

        super().exec()


class AbstractPlotWidget(QtWidgets.QWidget):
    """Widget to contain a plot and relevant settings."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.current_plot_data = None

        main_layout = QtWidgets.QHBoxLayout()

        plot_settings = self.make_control_layout()

        export_button = QtWidgets.QPushButton("Export plot...")
        export_button.pressed.connect(self.export)

        plot_settings.addStretch(1)
        plot_settings.addWidget(export_button)

        # self.plot_controls contains hideable controls
        self.plot_controls = QtWidgets.QWidget()
        self.plot_controls.setLayout(plot_settings)

        self.toggle_button = QtWidgets.QToolButton()
        self.toggle_button.toggled.connect(self.toggle_settings)
        self.toggle_button.setCheckable(True)
        self.toggle_settings(self.toggle_button.isChecked())

        # plot_toolbar contains always-visible toolbar
        plot_toolbar = QtWidgets.QVBoxLayout()
        plot_toolbar.addWidget(self.toggle_button)
        for toolbar_widget in self.make_toolbar_widgets():
            plot_toolbar.addWidget(toolbar_widget)

        plot_toolbar.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignHCenter)

        sidebar = QtWidgets.QHBoxLayout()
        sidebar.addWidget(self.plot_controls)
        sidebar.addLayout(plot_toolbar)

        self.figure = self.make_figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setParent(self)
        self.setMinimumHeight(300)

        main_layout.addLayout(sidebar, 0)
        main_layout.addWidget(self.canvas, 4)
        self.setLayout(main_layout)

    def toggle_settings(self, toggled_on: bool):
        """Toggles the visibility of the plot controls"""
        self.plot_controls.setVisible(toggled_on)
        if toggled_on:
            self.toggle_button.setIcon(QtGui.QIcon(path_for("hide-settings.png")))
        else:
            self.toggle_button.setIcon(QtGui.QIcon(path_for("settings.png")))

    @abstractmethod
    def make_control_layout(self) -> QtWidgets.QLayout:
        """Make the plot control panel.

        Returns
        -------
        QtWidgets.QLayout
            The control panel layout for the plot.

        """
        raise NotImplementedError

    def make_toolbar_widgets(self) -> list[QtWidgets.QWidget]:
        """Make widgets for the toolbar.

        Returns
        -------
        list[QtWidgets.QWidget]
            A list of toolbar widgets.

        """
        return []

    def make_figure(self) -> Figure:
        """Make the figure to plot onto.

        Returns
        -------
        Figure
            The figure to plot onto.

        """
        fig = Figure()
        return fig

    @abstractmethod
    def plot(self, project: RATapi.Project, results: Union[RATapi.outputs.Results, RATapi.outputs.BayesResults]):
        """Plot from the current project and results.

        Parameters
        ----------
        problem : RATapi.Project
            The project.
        results : Union[RATapi.outputs.Results, RATapi.outputs.BayesResults]
            The calculation results.

        """
        raise NotImplementedError

    def clear(self):
        """Clear the canvas."""
        for axis in self.figure.axes:
            axis.clear()
        self.canvas.draw()

    def export(self):
        """Save the figure to a file."""
        filepath = QtWidgets.QFileDialog.getSaveFileName(self, "Export Plot")
        if filepath:
            self.figure.savefig(filepath[0])


class RefSLDWidget(AbstractPlotWidget):
    """Creates a UI for displaying the path lengths from the simulation result"""

    def make_control_layout(self):
        self.plot_controls = QtWidgets.QWidget()
        self.x_axis = QtWidgets.QComboBox()
        self.x_axis.addItems(["Log", "Linear"])
        self.x_axis.currentTextChanged.connect(lambda: self.plot_event())
        self.y_axis = QtWidgets.QComboBox()
        self.y_axis.addItems(["Ref", "Q^4"])
        self.y_axis.currentTextChanged.connect(lambda: self.plot_event())
        self.show_error_bar = QtWidgets.QCheckBox("Show Error Bars")
        self.show_error_bar.setChecked(True)
        self.show_error_bar.checkStateChanged.connect(lambda: self.plot_event())
        self.show_grid = QtWidgets.QCheckBox("Show Grid")
        self.show_grid.checkStateChanged.connect(lambda: self.plot_event())
        self.show_legend = QtWidgets.QCheckBox("Show Legend")
        self.show_legend.setChecked(True)
        self.show_legend.checkStateChanged.connect(lambda: self.plot_event())

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel("X-Axis"))
        layout.addWidget(self.x_axis)
        layout.addWidget(QtWidgets.QLabel("Y-Axis"))
        layout.addWidget(self.y_axis)
        layout.addWidget(self.show_error_bar)
        layout.addWidget(self.show_grid)
        layout.addWidget(self.show_legend)

        return layout

    def make_toolbar_widgets(self) -> list[QtWidgets.QWidget]:
        self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Vertical)

        return [self.slider]

    def make_figure(self) -> Figure:
        figure = Figure()
        figure.subplots(1, 2)

        return figure

    def plot(self, project: RATapi.Project, results: Union[RATapi.outputs.Results, RATapi.outputs.BayesResults]):
        """Plots the reflectivity and SLD profiles.

        Parameters
        ----------
        problem : RATapi.Project
            The project
        results : Union[RATapi.outputs.Results, RATapi.outputs.BayesResults]
            The calculation results.
        """
        if project is None or results is None:
            self.clear()
            return

        data = RATapi.events.PlotEventData()

        data.modelType = project.model
        data.reflectivity = results.reflectivity
        data.shiftedData = results.shiftedData
        data.sldProfiles = results.sldProfiles
        data.resampledLayers = results.resampledLayers
        data.dataPresent = RATapi.inputs.make_data_present(project)
        data.subRoughs = results.contrastParams.subRoughs
        data.resample = RATapi.inputs.make_resample(project)
        data.contrastNames = [contrast.name for contrast in project.contrasts]
        self.plot_event(data)

    def plot_event(self, data: Optional[RATapi.events.PlotEventData] = None):
        """Updates the ref and SLD plots from a provided or cached plot event

        Parameters
        ----------
        data : Optional[RATapi.events.PlotEventData]
            plot event data, cached data is used if none is provided
        """

        if data is not None:
            self.current_plot_data = data

        if self.current_plot_data is None:
            return

        show_legend = self.show_legend.isChecked() if self.current_plot_data.contrastNames else False
        RATapi.plotting.plot_ref_sld_helper(
            self.current_plot_data,
            self.figure,
            delay=False,
            linear_x=self.x_axis.currentText() == "Linear",
            q4=self.y_axis.currentText() == "Q^4",
            show_error_bar=self.show_error_bar.isChecked(),
            show_grid=self.show_grid.isChecked(),
            show_legend=show_legend,
        )
        self.figure.tight_layout(pad=1)
        self.canvas.draw()


class CornerPlotWidget(AbstractPlotWidget):
    """Widget for plotting corner plots."""

    def make_control_layout(self):
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel("Not yet implemented!"))

        return layout

    def plot(self, _, results):
        self.clear()
        if isinstance(results, RATapi.outputs.BayesResults):
            fig = RATapi.plotting.plot_corner(results, return_fig=True)
            self.canvas.figure = fig
            self.canvas.draw()


class HistPlotWidget(AbstractPlotWidget):
    """Widget for plotting Bayesian posterior panels."""

    def make_control_layout(self):
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel("Not yet implemented!"))

        return layout

    def plot(self, _, results):
        self.clear()
        if isinstance(results, RATapi.outputs.BayesResults):
            fig = RATapi.plotting.plot_hists(results, return_fig=True)
            self.canvas.figure = fig
            self.canvas.draw()


class ContourPlotWidget(AbstractPlotWidget):
    """Widget for plotting a contour plot of two parameters."""

    def make_control_layout(self):
        control_layout = QtWidgets.QVBoxLayout()

        self.x_param_box = QtWidgets.QComboBox(self)
        self.x_param_box.currentTextChanged.connect(lambda: self.draw_plot())
        self.x_param_box.setDisabled(True)

        self.y_param_box = QtWidgets.QComboBox(self)
        self.y_param_box.currentTextChanged.connect(lambda: self.draw_plot())
        self.y_param_box.setDisabled(True)

        self.smooth_checkbox = QtWidgets.QCheckBox(self)
        self.smooth_checkbox.setChecked(True)
        self.smooth_checkbox.checkStateChanged.connect(lambda: self.draw_plot())

        x_param_row = QtWidgets.QHBoxLayout()
        x_param_row.addWidget(QtWidgets.QLabel("x Parameter:"))
        x_param_row.addWidget(self.x_param_box)

        y_param_row = QtWidgets.QHBoxLayout()
        y_param_row.addWidget(QtWidgets.QLabel("y Parameter:"))
        y_param_row.addWidget(self.y_param_box)

        smooth_row = QtWidgets.QHBoxLayout()
        smooth_row.addWidget(QtWidgets.QLabel("Smooth contour:"))
        smooth_row.addWidget(self.smooth_checkbox)

        control_layout.addLayout(x_param_row)
        control_layout.addLayout(y_param_row)
        control_layout.addLayout(smooth_row)

        return control_layout

    def plot(self, _, results: Union[RATapi.outputs.Results, RATapi.outputs.BayesResults]):
        """Plot the contour for two parameters."""
        fit_params = results.fitNames

        if not isinstance(results, RATapi.outputs.BayesResults):
            self.current_plot_data = None
        else:
            self.current_plot_data = results

        if self.current_plot_data is None:
            self.clear()
            self.x_param_box.setDisabled(True)
            self.y_param_box.setDisabled(True)
            return

        self.x_param_box.setDisabled(False)
        self.y_param_box.setDisabled(False)

        # reset fit parameter options
        old_x_param = self.x_param_box.currentText()
        old_y_param = self.y_param_box.currentText()
        self.x_param_box.clear()
        self.y_param_box.clear()

        self.x_param_box.addItems([""] + fit_params)
        if old_x_param in fit_params:
            self.x_param_box.setCurrentText(old_x_param)
        self.y_param_box.addItems([""] + fit_params)
        if old_y_param in fit_params:
            self.y_param_box.setCurrentText(old_y_param)

        self.draw_plot()

    def make_figure(self) -> Figure:
        """Make the figure to plot onto.

        Returns
        -------
        Figure
            The figure to plot onto.

        """
        fig = Figure()
        fig.subplots(1, 1)
        return fig

    def draw_plot(self):
        self.clear()
        if self.current_plot_data is None:
            return

        x_param = self.x_param_box.currentText()
        y_param = self.y_param_box.currentText()
        smooth = self.smooth_checkbox.checkState() == QtCore.Qt.CheckState.Checked

        if x_param != "" and y_param != "":
            RATapi.plotting.plot_contour(self.current_plot_data, x_param, y_param, smooth, axes=self.figure.axes[0])
            self.canvas.draw()


class ChainPlotWidget(AbstractPlotWidget):
    """Widget for plotting a Bayesian chain panel."""

    def make_control_layout(self):
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel("Not yet implemented!"))

        return layout

    def plot(self, _, results):
        self.clear()
        if isinstance(results, RATapi.outputs.BayesResults):
            fig = RATapi.plotting.plot_chain(results, return_fig=True)
            self.canvas.figure = fig
            self.canvas.draw()
