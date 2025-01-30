"""Widget for the Project window."""

from copy import deepcopy

import RATapi
from PyQt6 import QtCore, QtGui, QtWidgets
from RATapi.utils.enums import Calculations, Geometries, LayerModels

from rascal2.config import path_for
from rascal2.widgets.project.models import (
    CustomFileWidget,
    DomainContrastWidget,
    LayerFieldWidget,
    ParameterFieldWidget,
    ProjectFieldWidget,
)


class ProjectWidget(QtWidgets.QWidget):
    """
    The Project MDI Widget
    """

    def __init__(self, parent):
        """
        Initialize widget.

        Parameters
        ----------
        parent: MainWindowView
                An instance of the MainWindowView
        """
        super().__init__()
        self.parent = parent
        self.parent_model = self.parent.presenter.model

        self.parent_model.project_updated.connect(self.update_project_view)
        self.parent_model.controls_updated.connect(self.handle_controls_update)

        self.tabs = {
            "Parameters": ["parameters"],
            "Experimental Parameters": ["scalefactors", "bulk_in", "bulk_out"],
            "Layers": ["layers"],
            "Data": [],
            "Backgrounds": [],
            "Domains": ["domain_ratios", "domain_contrasts"],
            "Custom Files": ["custom_files"],
            "Contrasts": [],
        }

        self.view_tabs = {}
        self.edit_tabs = {}
        self.draft_project = None

        project_view = self.create_project_view()
        project_edit = self.create_edit_view()

        self.project_tab.currentChanged.connect(self.edit_project_tab.setCurrentIndex)
        self.edit_project_tab.currentChanged.connect(self.project_tab.setCurrentIndex)

        self.stacked_widget = QtWidgets.QStackedWidget()
        self.stacked_widget.addWidget(project_view)
        self.stacked_widget.addWidget(project_edit)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

    def create_project_view(self) -> None:
        """Creates the project (non-edit) view"""
        project_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setSpacing(20)

        self.edit_project_button = QtWidgets.QPushButton(
            "Edit Project", self, objectName="bluebutton", icon=QtGui.QIcon(path_for("edit.png"))
        )
        self.edit_project_button.clicked.connect(self.show_edit_view)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        button_layout.addWidget(self.edit_project_button)

        main_layout.addLayout(button_layout)

        settings_layout = QtWidgets.QHBoxLayout()
        settings_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)

        absorption_label = QtWidgets.QLabel("Absorption:", self, objectName="boldlabel")
        self.absorption_checkbox = QtWidgets.QCheckBox()
        # this is how you make a checkbox read-only but still checkable from inside code...
        self.absorption_checkbox.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        settings_layout.addWidget(absorption_label)
        settings_layout.addWidget(self.absorption_checkbox)

        self.calculation_label = QtWidgets.QLabel("Calculation:", self, objectName="boldlabel")

        self.calculation_type = QtWidgets.QLineEdit(self)
        self.calculation_type.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.calculation_type.setReadOnly(True)

        settings_layout.addWidget(self.calculation_label)
        settings_layout.addWidget(self.calculation_type)

        self.model_type_label = QtWidgets.QLabel("Model Type:", self, objectName="boldlabel")

        self.model_type = QtWidgets.QLineEdit(self)
        self.model_type.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.model_type.setReadOnly(True)

        settings_layout.addWidget(self.model_type_label)
        settings_layout.addWidget(self.model_type)

        self.geometry_label = QtWidgets.QLabel("Geometry:", self, objectName="boldlabel")

        self.geometry_type = QtWidgets.QLineEdit(self)
        self.geometry_type.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.geometry_type.setReadOnly(True)

        settings_layout.addWidget(self.geometry_label)
        settings_layout.addWidget(self.geometry_type)

        main_layout.addLayout(settings_layout)

        self.project_tab = QtWidgets.QTabWidget()

        for tab, fields in self.tabs.items():
            widget = self.view_tabs[tab] = ProjectTabWidget(fields, self)
            self.project_tab.addTab(widget, tab)

        main_layout.addWidget(self.project_tab)
        project_widget.setLayout(main_layout)

        return project_widget

    def create_edit_view(self) -> None:
        """Creates the project edit view"""

        edit_project_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setSpacing(20)

        self.save_project_button = QtWidgets.QPushButton("Save Project", self, objectName="greybutton")
        self.save_project_button.setIcon(QtGui.QIcon(path_for("save-project.png")))
        self.save_project_button.clicked.connect(self.save_changes)

        self.cancel_button = QtWidgets.QPushButton("Cancel", self, objectName="redbutton")
        self.cancel_button.setIcon(QtGui.QIcon(path_for("cancel-dark.png")))
        self.cancel_button.clicked.connect(self.cancel_changes)

        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        buttons_layout.addWidget(self.save_project_button)
        buttons_layout.addWidget(self.cancel_button)
        main_layout.addLayout(buttons_layout)

        settings_layout = QtWidgets.QHBoxLayout()
        settings_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)

        absorption_label = QtWidgets.QLabel("Absorption:", self, objectName="boldlabel")
        self.edit_absorption_checkbox = QtWidgets.QCheckBox()

        settings_layout.addWidget(absorption_label)
        settings_layout.addWidget(self.edit_absorption_checkbox)

        self.edit_calculation_label = QtWidgets.QLabel("Calculation:", self, objectName="boldlabel")

        self.calculation_combobox = QtWidgets.QComboBox(self)
        self.calculation_combobox.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self.calculation_combobox.addItems([calc for calc in Calculations])

        settings_layout.addWidget(self.edit_calculation_label)
        settings_layout.addWidget(self.calculation_combobox)

        self.edit_model_type_label = QtWidgets.QLabel("Model Type:", self, objectName="boldlabel")

        self.model_combobox = QtWidgets.QComboBox(self)
        self.model_combobox.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self.model_combobox.addItems([model for model in LayerModels])

        settings_layout.addWidget(self.edit_model_type_label)
        settings_layout.addWidget(self.model_combobox)

        self.edit_geometry_label = QtWidgets.QLabel("Geometry:", self, objectName="boldlabel")

        self.geometry_combobox = QtWidgets.QComboBox(self)
        self.geometry_combobox.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self.geometry_combobox.addItems([geo for geo in Geometries])

        settings_layout.addWidget(self.edit_geometry_label)
        settings_layout.addWidget(self.geometry_combobox)
        main_layout.addLayout(settings_layout)

        self.edit_absorption_checkbox.checkStateChanged.connect(
            lambda s: self.update_draft_project({"absorption": s == QtCore.Qt.CheckState.Checked})
        )
        self.calculation_combobox.currentTextChanged.connect(lambda s: self.update_draft_project({"calculation": s}))
        self.calculation_combobox.currentTextChanged.connect(lambda: self.handle_tabs())
        self.model_combobox.currentTextChanged.connect(lambda s: self.update_draft_project({"model": s}))
        self.model_combobox.currentTextChanged.connect(lambda: self.handle_tabs())
        self.geometry_combobox.currentTextChanged.connect(lambda s: self.update_draft_project({"geometry": s}))
        self.edit_project_tab = QtWidgets.QTabWidget()

        for tab, fields in self.tabs.items():
            widget = self.edit_tabs[tab] = ProjectTabWidget(fields, self, edit_mode=True)
            self.edit_project_tab.addTab(widget, tab)

        self.edit_absorption_checkbox.checkStateChanged.connect(
            lambda s: self.edit_tabs["Layers"].tables["layers"].set_absorption(s == QtCore.Qt.CheckState.Checked)
        )

        main_layout.addWidget(self.edit_project_tab)

        edit_project_widget.setLayout(main_layout)

        return edit_project_widget

    def update_project_view(self) -> None:
        """Updates the project view."""
        # draft project is a dict containing all the attributes of the parent model,
        # because we don't want validation errors going off while editing the model is in-progress
        self.draft_project: dict = create_draft_project(self.parent_model.project)

        self.absorption_checkbox.setChecked(self.parent_model.project.absorption)
        self.calculation_type.setText(self.parent_model.project.calculation)
        self.model_type.setText(self.parent_model.project.model)
        self.geometry_type.setText(self.parent_model.project.geometry)

        self.edit_absorption_checkbox.setChecked(self.parent_model.project.absorption)
        self.calculation_combobox.setCurrentText(self.parent_model.project.calculation)
        self.model_combobox.setCurrentText(self.parent_model.project.model)
        self.geometry_combobox.setCurrentText(self.parent_model.project.geometry)

        for tab in self.tabs:
            self.view_tabs[tab].update_model(self.draft_project)
            self.edit_tabs[tab].update_model(self.draft_project)

        self.handle_tabs()
        self.handle_controls_update()

    def update_draft_project(self, new_values: dict) -> None:
        """
        Updates the draft project.

        Parameters
        ----------
        new_values: dict
            A dictionary of new values to update in the draft project.

        """
        self.draft_project.update(new_values)

    def handle_tabs(self) -> None:
        """Displays or hides tabs as relevant."""
        # the domains tab should only be visible if calculating domains
        domain_tab_index = list(self.view_tabs).index("Domains")
        is_domains = self.calculation_combobox.currentText() == Calculations.Domains
        self.project_tab.setTabVisible(domain_tab_index, is_domains)
        self.edit_project_tab.setTabVisible(domain_tab_index, is_domains)

        # the layers tab and domain contrasts table should only be visible in standard layers
        layers_tab_index = list(self.view_tabs).index("Layers")
        is_layers = self.model_combobox.currentText() == LayerModels.StandardLayers
        self.project_tab.setTabVisible(layers_tab_index, is_layers)
        self.edit_project_tab.setTabVisible(layers_tab_index, is_layers)
        self.view_tabs["Domains"].tables["domain_contrasts"].setVisible(is_layers)
        self.edit_tabs["Domains"].tables["domain_contrasts"].setVisible(is_layers)

    def handle_controls_update(self):
        """Handle updates to Controls that need to be reflected in the project."""
        if self.draft_project is None:
            return

        controls = self.parent_model.controls

        for tab in self.tabs:
            self.view_tabs[tab].handle_controls_update(controls)
            self.edit_tabs[tab].handle_controls_update(controls)

    def show_project_view(self) -> None:
        """Show project view"""
        self.setWindowTitle("Project")
        self.parent.controls_widget.run_button.setEnabled(True)
        self.stacked_widget.setCurrentIndex(0)

    def show_edit_view(self) -> None:
        """Show edit view"""
        self.setWindowTitle("Edit Project")
        self.update_project_view()
        self.parent.controls_widget.run_button.setEnabled(False)
        self.stacked_widget.setCurrentIndex(1)

    def save_changes(self) -> None:
        """Save changes to the project."""
        try:
            self.validate_draft_project()
        except ValueError as err:
            self.parent.terminal_widget.write_error(f"Could not save draft project:\n  {err}")
        else:
            self.parent.presenter.edit_project(self.draft_project)
            self.update_project_view()
            self.parent.controls_widget.run_button.setEnabled(True)
            self.show_project_view()

    def validate_draft_project(self):
        """Check that the draft project is valid."""
        errors = []
        if self.draft_project["model"] == LayerModels.StandardLayers and self.draft_project["layers"]:
            layer_attrs = list(self.draft_project["layers"][0].model_fields)
            layer_attrs.remove("name")
            layer_attrs.remove("hydrate_with")
            # ensure all layer parameters have been filled in, and all names are layers that exist
            valid_params = [p.name for p in self.draft_project["parameters"]]
            for i, layer in enumerate(self.draft_project["layers"]):
                missing_params = []
                invalid_params = []
                for attr in layer_attrs:
                    param = getattr(layer, attr)
                    if param == "":
                        missing_params.append(attr)
                    elif param not in valid_params:
                        invalid_params.append((attr, param))

                if missing_params:
                    noun = "a parameter" if len(missing_params) == 1 else "parameters"
                    msg = f"Layer '{layer.name}' (row {i + 1}) is missing {noun}: {', '.join(missing_params)}"
                    errors.append(msg)
                if invalid_params:
                    noun = "an invalid value" if len(invalid_params) == 1 else "invalid values"
                    msg = f"Layer '{layer.name}' (row {i + 1}) has {noun}: {{0}}".format(
                        ",\n  ".join(f'"{v}" for parameter {p}' for p, v in invalid_params)
                    )
                    errors.append(msg)

        if errors:
            raise ValueError("\n  ".join(errors))

    def cancel_changes(self) -> None:
        """Cancel changes to the project."""
        self.update_project_view()
        self.show_project_view()

    def set_editing_enabled(self, enabled: bool):
        """Enable or disable project editing, for example during a run."""
        self.edit_project_button.setEnabled(enabled)
        for tab_name, tab_items in self.tabs.items():
            for table in tab_items:
                if table in RATapi.project.parameter_class_lists:
                    self.view_tabs[tab_name].tables[table].setEnabled(enabled)


class ProjectTabWidget(QtWidgets.QWidget):
    """Widget that combines multiple ProjectFieldWidgets to create a tab of the project window.

    Subclasses must reimplement the function update_model.

    Parameters
    ----------
    fields : list[str]
        The fields to display in the tab.
    parent : QtWidgets.QWidget
        The parent to this widget.

    """

    def __init__(self, fields: list[str], parent, edit_mode: bool = False):
        super().__init__(parent)
        self.parent = parent
        self.fields = fields
        self.edit_mode = edit_mode
        self.tables = {}

        layout = QtWidgets.QVBoxLayout()
        for field in self.fields:
            if field in RATapi.project.parameter_class_lists:
                self.tables[field] = ParameterFieldWidget(field, self)
            elif field == "layers":
                self.tables[field] = LayerFieldWidget(field, self)
            elif field == "domain_contrasts":
                self.tables[field] = DomainContrastWidget(field, self)
            elif field == "custom_files":
                self.tables[field] = CustomFileWidget(field, self)
            else:
                self.tables[field] = ProjectFieldWidget(field, self)
            layout.addWidget(self.tables[field])

        scroll_area = QtWidgets.QScrollArea()
        # one widget must be given, not a layout,
        # or scrolling won't work properly!
        tab_widget = QtWidgets.QFrame()
        tab_widget.setLayout(layout)
        scroll_area.setWidget(tab_widget)
        scroll_area.setWidgetResizable(True)

        widget_layout = QtWidgets.QVBoxLayout()
        widget_layout.addWidget(scroll_area)

        self.setLayout(widget_layout)

    def update_model(self, new_model):
        """Update the model for each table.

        Parameters
        ----------
        new_model
            The new model data.

        """
        for field, table in self.tables.items():
            classlist = new_model[field]
            table.update_model(classlist)
            if self.edit_mode:
                table.edit()
            if "layers" in self.tables:
                self.tables["layers"].set_absorption(new_model["absorption"])

    def handle_controls_update(self, controls):
        """Reflect changes to the Controls object."""
        for field in RATapi.project.parameter_class_lists:
            if field in self.tables:
                self.tables[field].handle_bayesian_columns(controls.procedure)


def create_draft_project(project: RATapi.Project) -> dict:
    """Create a draft project (dictionary of project attributes) from a Project.

    Parameters
    ----------
    project : RATapi.Project
        The project to create a draft from.

    Returns
    -------
    dict
        The draft project.

    """
    # in an ideal world, we could just copy and dump the Project with something like
    # project.model_copy(deep=True).model_dump()
    # but some references get shared for some reason: e.g. draft_project['parameters'].append
    # will point towards project.parameters.append (???) and so on

    draft_project = {}
    for field in RATapi.Project.model_fields:
        attr = getattr(project, field)
        if isinstance(attr, RATapi.ClassList):
            draft_project[field] = RATapi.ClassList(deepcopy(attr.data))
            draft_project[field]._class_handle = getattr(project, field)._class_handle
        else:
            draft_project[field] = attr
    return draft_project
