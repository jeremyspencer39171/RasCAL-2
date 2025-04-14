"""Widget for setting up the Controls class."""

from typing import Any, Callable

from pydantic import ValidationError
from PyQt6 import QtCore, QtGui, QtWidgets
from RATapi.controls import common_fields, fields
from RATapi.utils.enums import Procedures

from rascal2.config import path_for
from rascal2.widgets.inputs import get_validated_input


class ControlsWidget(QtWidgets.QWidget):
    """Widget for editing the Controls window."""

    def __init__(self, parent):
        super().__init__()
        self.view = parent
        self.presenter = parent.presenter
        self.presenter.model.controls_updated.connect(self.update_ui)

        # create fit settings view and setup connection to model
        self.fit_settings_layout = QtWidgets.QStackedLayout()
        self.fit_settings = QtWidgets.QWidget()
        self.fit_settings.setLayout(self.fit_settings_layout)
        self.fit_settings.setBackgroundRole(QtGui.QPalette.ColorRole.Base)

        # create run and stop buttons
        self.run_button = QtWidgets.QPushButton(icon=QtGui.QIcon(path_for("play.png")), text="Run")
        self.run_button.toggled.connect(self.toggle_run_button)
        self.run_button.setStyleSheet("background-color: green;")
        self.run_button.setCheckable(True)

        self.stop_button = QtWidgets.QPushButton(icon=QtGui.QIcon(path_for("stop.png")), text="Stop")
        self.stop_button.pressed.connect(self.presenter.interrupt_terminal)
        self.stop_button.setStyleSheet("background-color: red;")
        self.stop_button.setEnabled(False)

        # validation label for if user tries to run with invalid controls
        self.validation_label = QtWidgets.QLabel("")
        self.validation_label.setStyleSheet("color : red")
        self.validation_label.font().setPointSize(10)
        self.validation_label.setWordWrap(True)
        self.validation_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Expanding)
        self.validation_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)

        # create box containing chi-squared value
        chi_layout = QtWidgets.QHBoxLayout()
        self.chi_squared = QtWidgets.QLineEdit()
        self.chi_squared.setReadOnly(True)
        chi_layout.addWidget(QtWidgets.QLabel("Current chi-squared:"))
        chi_layout.addWidget(self.chi_squared)
        chi_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # create dropdown to choose procedure
        procedure_layout = QtWidgets.QHBoxLayout()
        procedure_layout.addWidget(QtWidgets.QLabel("Procedure:"))
        self.procedure_dropdown = QtWidgets.QComboBox()
        self.procedure_dropdown.addItems([p.value for p in Procedures])
        self.procedure_dropdown.currentIndexChanged.connect(self.set_procedure)
        procedure_layout.addWidget(self.procedure_dropdown)

        # create button to hide/show fit settings
        self.fit_settings_button = QtWidgets.QPushButton()
        self.fit_settings_button.setCheckable(True)
        self.fit_settings_button.toggled.connect(self.toggle_fit_settings)
        self.fit_settings_button.setChecked(True)

        # compose buttons & widget
        buttons_layout = QtWidgets.QVBoxLayout()
        buttons_layout.addWidget(self.run_button)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)

        procedure_box = QtWidgets.QVBoxLayout()
        procedure_box.addLayout(chi_layout)
        procedure_box.addLayout(buttons_layout)
        procedure_box.addLayout(procedure_layout)
        procedure_box.addWidget(self.fit_settings_button, alignment=QtCore.Qt.AlignmentFlag.AlignVCenter)
        procedure_box.addWidget(self.validation_label, alignment=QtCore.Qt.AlignmentFlag.AlignVCenter)

        widget_layout = QtWidgets.QHBoxLayout()
        widget_layout.addLayout(procedure_box)
        widget_layout.addWidget(self.fit_settings)

        self.setLayout(widget_layout)

    def setup_controls(self):
        """Setup the parts of the widget which depend on the Controls object."""
        # clear any chi-squared from previous controls
        self.chi_squared.setText("")

        # add fit settings for each procedure
        for procedure in Procedures:
            proc_settings = [f for f in fields.get(procedure, []) if f != "procedure"]
            fit_set = FitSettingsWidget(self, proc_settings, self.presenter)
            self.fit_settings_layout.addWidget(fit_set)

        # set initial procedure to whatever is in the Controls object
        init_procedure = [p.value for p in Procedures].index(self.presenter.model.controls.procedure)
        self.procedure_dropdown.setCurrentIndex(init_procedure)

    def update_ui(self):
        """Updates UI without firing signals to avoid recursion"""
        init_procedure = [p.value for p in Procedures].index(self.presenter.model.controls.procedure)
        self.procedure_dropdown.blockSignals(True)
        self.procedure_dropdown.setCurrentIndex(init_procedure)
        self.procedure_dropdown.blockSignals(False)
        self.fit_settings_layout.setCurrentIndex(init_procedure)
        settings = self.fit_settings_layout.currentWidget()
        if settings is None:
            return

        for field, widget in settings.rows.items():
            widget.editor.blockSignals(True)
            settings.update_data(field)
            widget.editor.blockSignals(False)

    def toggle_fit_settings(self, toggled: bool):
        """Toggle whether the fit settings table is visible.

        Parameters
        ----------
        toggled : bool
            Whether the button is toggled on or off.

        """
        if toggled:
            self.fit_settings.show()
            self.fit_settings_button.setText("Hide fit settings")
        else:
            self.fit_settings.hide()
            self.fit_settings_button.setText("Show fit settings")

    def toggle_run_button(self, toggled: bool):
        """Toggle whether the optimisation is currently running.

        Parameters
        ----------
        toggled : bool
            Whether the button is toggled on or off.

        """
        if toggled:
            invalid_inputs = self.fit_settings_layout.currentWidget().get_invalid_inputs()
            if invalid_inputs:
                # can use an f-string in Python 3.12 and up for the fit settings,
                # but below that you cannot put '\n' in an f-string
                # so we use this method for compatibility
                self.validation_label.setText(
                    "Could not run due to invalid fit settings:\n    "
                    + "\n    ".join(invalid_inputs)
                    + "\nFix these inputs and try again.\n"
                    "See fit settings for more details.\n"
                )
                self.run_button.setChecked(False)
                return
            self.validation_label.setText("")
            self.view.set_editing_enabled(False)
            self.run_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.presenter.run()
        else:
            self.view.set_editing_enabled(True)
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def set_procedure(self, index: int):
        """Change the Controls procedure and update the table.

        Parameters
        ----------
        index : int
            The index of the procedure to change to in the procedure list.

        """
        self.fit_settings_layout.setCurrentIndex(index)
        procedure = [p.value for p in Procedures][index]
        self.presenter.edit_controls("procedure", procedure)
        # synchronise common fields between procedures
        for field in common_fields:
            if field not in ["procedure"]:
                self.fit_settings_layout.currentWidget().update_data(field)


class FitSettingsWidget(QtWidgets.QWidget):
    """Widget containing the fit settings form.

    Parameters
    ----------
    parent : QWidget
        The parent widget of this widget.
    settings : list
        The list of relevant settings that this widget should show.
    presenter : MainWindowPresenter
        The RasCAL presenter.

    """

    def __init__(self, parent, settings, presenter):
        super().__init__(parent)
        self.presenter = presenter
        self.controls = presenter.model.controls
        self.rows = {}
        self.datasetter = {}
        self.val_labels = {}

        settings_grid = QtWidgets.QGridLayout()
        settings_grid.setContentsMargins(10, 10, 10, 10)
        controls_fields = self.get_controls_attribute("model_fields")
        for i, setting in enumerate(settings):
            field_info = controls_fields[setting]
            self.rows[setting] = get_validated_input(field_info)
            self.rows[setting].layout().setContentsMargins(5, 0, 0, 0)
            self.datasetter[setting] = self.create_model_data_setter(setting)
            self.rows[setting].edited_signal.connect(self.datasetter[setting])

            # the label gives a description of the controls field on mouseover
            label = QtWidgets.QLabel(setting)
            label.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)
            label.setToolTip(field_info.description)

            self.val_labels[setting] = QtWidgets.QLabel()
            self.val_labels[setting].setStyleSheet("QLabel { color : red; }")
            self.val_labels[setting].font().setPointSize(10)
            self.val_labels[setting].setWordWrap(True)
            self.val_labels[setting].setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
            self.update_data(setting)
            settings_grid.addWidget(label, 2 * i, 0)
            settings_grid.addWidget(self.rows[setting], 2 * i, 1)
            settings_grid.addWidget(self.val_labels[setting], 2 * i + 1, 1)

        settings_grid.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        fit_settings = QtWidgets.QWidget(self)
        fit_settings.setLayout(settings_grid)

        scroll_area = QtWidgets.QScrollArea(self)
        scroll_area.setWidget(fit_settings)
        scroll_area.setWidgetResizable(True)
        widget_layout = QtWidgets.QVBoxLayout()
        widget_layout.addWidget(scroll_area)

        self.setLayout(widget_layout)

    def update_data(self, setting):
        """Update the view to match the data in the model.

        Parameters
        ----------
        setting : str
            The setting to update.

        """
        try:
            self.rows[setting].set_data(self.get_controls_attribute(setting))
        except TypeError:
            self.rows[setting].set_data(str(self.get_controls_attribute(setting)))

    def create_model_data_setter(self, setting: str) -> Callable:
        """Create a model data setter for a fit setting.

        Parameters
        ----------
        setting : str
            The setting to which the setter connects.

        Returns
        -------
        Callable
            A function which sets the model data to the current value of the view input.

        """

        def set_model_data():
            value = self.rows[setting].get_data()
            try:
                self.presenter.edit_controls(setting, value)
            except ValidationError as err:
                self.set_validation_text(setting, err.errors()[0]["msg"])
            else:
                self.set_validation_text(setting, "")

        return set_model_data

    def get_invalid_inputs(self) -> list[str]:
        """Return all control inputs which are currently not valid.

        Returns
        -------
        list[str]
            A list of setting names which are currently not valid.

        """
        return [s for s in self.val_labels if self.val_labels[s].text() != ""]

    def set_validation_text(self, setting, text):
        """Set validation text on an invalid setting.

        Parameters
        ----------
        setting : str
            The setting which is invalid.
        text : str
            The error message to provide under the setting.

        """
        self.val_labels[setting].setText(text)
        if text == "":
            self.rows[setting].editor.setStyleSheet("")
        else:
            self.rows[setting].editor.setStyleSheet("color : red")

    def get_controls_attribute(self, setting) -> Any:
        """Get the value of an attribute in the model's Controls object.

        Parameters
        ----------
        setting : str
            Which setting in the Controls object should be read.

        Returns
        -------
        value : Any
            The value of the setting in the model's Controls object.

        """
        value = getattr(self.controls, setting)
        return value
