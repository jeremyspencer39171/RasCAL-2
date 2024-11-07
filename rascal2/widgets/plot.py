from typing import Optional, Union

import RATapi
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6 import QtCore, QtGui, QtWidgets

from rascal2.config import path_for


class PlotWidget(QtWidgets.QWidget):
    """Creates a UI for displaying the path lengths from the simulation result"""

    def __init__(self, parent):
        super().__init__()

        self.current_plot_data = None

        self.parent_model = parent.presenter.model
        main_layout = QtWidgets.QHBoxLayout()
        control_layout = QtWidgets.QHBoxLayout()
        plot_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(control_layout, 0)
        main_layout.addLayout(plot_layout, 4)
        self.setLayout(main_layout)

        self.create_plot_control()
        control_layout.addWidget(self.plot_controls)

        slider_layout = QtWidgets.QVBoxLayout()
        self.toggle_button = QtWidgets.QToolButton()
        self.toggle_button.toggled.connect(self.toggle_settings)
        self.toggle_button.setCheckable(True)
        self.toggle_settings(self.toggle_button.isChecked())
        self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Vertical)
        slider_layout.addWidget(self.toggle_button)
        slider_layout.addWidget(self.slider)
        slider_layout.setAlignment(self.slider, QtCore.Qt.AlignmentFlag.AlignHCenter)
        control_layout.addLayout(slider_layout)

        self.figure = Figure()
        self.figure.subplots(1, 2)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setParent(self)
        plot_layout.addWidget(self.canvas)
        self.setMinimumHeight(300)

        self.parent_model.results_updated.connect(
            lambda: self.plot(self.parent_model.project, self.parent_model.results)
        )

    def create_plot_control(self):
        """Creates the controls for customising plot"""
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
        layout.addStretch(1)
        self.plot_controls.setLayout(layout)

    def toggle_settings(self, toggled_on: bool):
        """Toggles the visibility of the plot controls"""
        self.plot_controls.setVisible(toggled_on)
        if toggled_on:
            self.toggle_button.setIcon(QtGui.QIcon(path_for("hide-settings.png")))
        else:
            self.toggle_button.setIcon(QtGui.QIcon(path_for("settings.png")))

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
            for axis in self.figure.axes:
                axis.clear()
            self.canvas.draw()
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
