"""Widget for the Project window."""

from collections.abc import Generator
from copy import deepcopy

import RATapi
from pydantic import ValidationError
from PyQt6 import QtCore, QtGui, QtWidgets
from RATapi.utils.custom_errors import custom_pydantic_validation_error
from RATapi.utils.enums import Calculations, Geometries, LayerModels

from rascal2.config import path_for
from rascal2.widgets.project.lists import ContrastWidget, DataWidget
from rascal2.widgets.project.tables import (
    BackgroundsFieldWidget,
    CustomFileWidget,
    DomainContrastWidget,
    LayerFieldWidget,
    ParameterFieldWidget,
    ProjectFieldWidget,
    ResolutionsFieldWidget,
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
            "Data": ["data"],
            "Backgrounds": ["background_parameters", "backgrounds"],
            "Resolutions": ["resolution_parameters", "resolutions"],
            "Domains": ["domain_ratios", "domain_contrasts"],
            "Custom Files": ["custom_files"],
            "Contrasts": ["contrasts"],
        }
        # track which tabs are lists (for syncing)
        self.list_tabs = ["Contrasts", "Data"]

        self.view_tabs = {}
        self.edit_tabs = {}
        self.draft_project = None
        # for making model type changes non-destructive
        self.old_contrast_models = {}

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

        absorption_label = QtWidgets.QLabel("Absorption:", self, objectName="BoldLabel")
        self.absorption_checkbox = QtWidgets.QCheckBox()
        self.absorption_checkbox.setDisabled(True)

        settings_layout.addWidget(absorption_label)
        settings_layout.addWidget(self.absorption_checkbox)

        self.calculation_label = QtWidgets.QLabel("Calculation:", self, objectName="BoldLabel")

        self.calculation_type = QtWidgets.QLineEdit(self)
        self.calculation_type.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.calculation_type.setReadOnly(True)

        settings_layout.addWidget(self.calculation_label)
        settings_layout.addWidget(self.calculation_type)

        self.model_type_label = QtWidgets.QLabel("Model Type:", self, objectName="BoldLabel")

        self.model_type = QtWidgets.QLineEdit(self)
        self.model_type.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.model_type.setReadOnly(True)

        settings_layout.addWidget(self.model_type_label)
        settings_layout.addWidget(self.model_type)

        self.geometry_label = QtWidgets.QLabel("Geometry:", self, objectName="BoldLabel")

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

        absorption_label = QtWidgets.QLabel("Absorption:", self, objectName="BoldLabel")
        self.edit_absorption_checkbox = QtWidgets.QCheckBox()

        settings_layout.addWidget(absorption_label)
        settings_layout.addWidget(self.edit_absorption_checkbox)

        self.edit_calculation_label = QtWidgets.QLabel("Calculation:", self, objectName="BoldLabel")

        self.calculation_combobox = QtWidgets.QComboBox(self)
        self.calculation_combobox.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self.calculation_combobox.addItems([calc for calc in Calculations])

        settings_layout.addWidget(self.edit_calculation_label)
        settings_layout.addWidget(self.calculation_combobox)

        self.edit_model_type_label = QtWidgets.QLabel("Model Type:", self, objectName="BoldLabel")

        self.model_combobox = QtWidgets.QComboBox(self)
        self.model_combobox.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self.model_combobox.addItems([model for model in LayerModels])

        settings_layout.addWidget(self.edit_model_type_label)
        settings_layout.addWidget(self.model_combobox)

        self.edit_geometry_label = QtWidgets.QLabel("Geometry:", self, objectName="BoldLabel")

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
        # when calculation type changed, update the draft project, show/hide the domains tab,
        # and change contrasts to have ratio
        self.calculation_combobox.currentTextChanged.connect(lambda s: self.update_draft_project({"calculation": s}))
        self.calculation_combobox.currentTextChanged.connect(lambda: self.handle_tabs())
        self.calculation_combobox.currentTextChanged.connect(
            lambda s: self.edit_tabs["Contrasts"].tables["contrasts"].set_domains(s == Calculations.Domains)
        )

        # when model type changed, hide/show layers tab and change model field in contrasts
        self.model_combobox.currentTextChanged.connect(lambda: self.handle_tabs())
        self.model_combobox.currentTextChanged.connect(lambda s: self.handle_model_update(s))

        self.geometry_combobox.currentTextChanged.connect(lambda s: self.update_draft_project({"geometry": s}))
        self.edit_project_tab = QtWidgets.QTabWidget()

        for tab, fields in self.tabs.items():
            widget = self.edit_tabs[tab] = ProjectTabWidget(fields, self, edit_mode=True)
            self.edit_project_tab.addTab(widget, tab)

        self.edit_absorption_checkbox.checkStateChanged.connect(
            lambda s: self.edit_tabs["Layers"].tables["layers"].set_absorption(s == QtCore.Qt.CheckState.Checked)
        )

        for tab in ["Experimental Parameters", "Layers", "Backgrounds", "Domains"]:
            for table in self.edit_tabs[tab].tables.values():
                table.edited.connect(lambda: self.edit_tabs["Contrasts"].tables["contrasts"].update_item_view())

        main_layout.addWidget(self.edit_project_tab)

        edit_project_widget.setLayout(main_layout)

        return edit_project_widget

    def update_project_view(self) -> None:
        """Updates the project view."""
        # draft project is a dict containing all the attributes of the parent model,
        # because we don't want validation errors going off while editing the model is in-progress
        self.draft_project: dict = create_draft_project(self.parent_model.project)

        for tab in self.tabs:
            self.view_tabs[tab].update_model(self.draft_project)
            self.edit_tabs[tab].update_model(self.draft_project)

        self.absorption_checkbox.setChecked(self.parent_model.project.absorption)
        self.calculation_type.setText(self.parent_model.project.calculation)
        self.model_type.setText(self.parent_model.project.model)
        self.geometry_type.setText(self.parent_model.project.geometry)

        self.edit_absorption_checkbox.setChecked(self.parent_model.project.absorption)
        self.calculation_combobox.setCurrentText(self.parent_model.project.calculation)
        self.model_combobox.setCurrentText(self.parent_model.project.model)
        self.geometry_combobox.setCurrentText(self.parent_model.project.geometry)

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

    def handle_model_update(self, new_type):
        """Handle updates to the model type.

        Parameters
        ----------
        new_type : LayerModels
            The new layer model.

        """
        if self.draft_project is None:
            return

        old_type = self.draft_project["model"]
        self.update_draft_project({"model": new_type})

        # we use 'xor' (^) as "if the old type was standard layers and the new type isn't, or vice versa"
        if (old_type == LayerModels.StandardLayers) ^ (new_type == LayerModels.StandardLayers):
            old_contrast_models = {}
            # clear contrasts as what the 'model' means has changed!
            for contrast in self.draft_project["contrasts"]:
                old_contrast_models[contrast.name] = contrast.model
                contrast.model = self.old_contrast_models.get(contrast.name, [])

            self.old_contrast_models = old_contrast_models
            self.edit_tabs["Contrasts"].tables["contrasts"].update_item_view()

    def show_project_view(self) -> None:
        """Show project view"""
        self.setWindowTitle("Project")
        self.parent.controls_widget.run_button.setEnabled(True)
        self.stacked_widget.setCurrentIndex(0)

    def show_edit_view(self) -> None:
        """Show edit view"""
        self.setWindowTitle("Edit Project")

        # sync selected items for list tabs
        view_indices = {
            tab: self.view_tabs[tab].tables[tab.lower()].list.selectionModel().currentIndex().row()
            for tab in self.list_tabs
        }

        self.update_project_view()
        self.parent.controls_widget.run_button.setEnabled(False)

        for tab in self.list_tabs:
            edit_widget = self.edit_tabs[tab].tables[tab.lower()]
            idx = view_indices[tab]
            edit_widget.list.selectionModel().setCurrentIndex(
                edit_widget.model.index(idx, 0), QtCore.QItemSelectionModel.SelectionFlag.ClearAndSelect
            )

        self.stacked_widget.setCurrentIndex(1)

    def save_changes(self) -> None:
        """Save changes to the project."""
        # sync list items (wrap around update_project_view() which sets them to zero by default)
        # the list can lose focus when a contrast is edited... default to first item if this happens
        edit_indices = {
            tab: max(self.edit_tabs[tab].tables[tab.lower()].list.selectionModel().currentIndex().row(), 0)
            for tab in self.list_tabs
        }

        errors = "\n  ".join(self.validate_draft_project())
        if errors:
            self.parent.terminal_widget.write_error(f"Could not save draft project:\n  {errors}")
        else:
            # catch errors from Pydantic as fallback rather than crashing
            try:
                self.parent.presenter.edit_project(self.draft_project)
            except ValidationError as err:
                custom_error_list = custom_pydantic_validation_error(err.errors(include_url=False))
                custom_errors = ValidationError.from_exception_data(err.title, custom_error_list, hide_input=True)
                self.parent.terminal_widget.write_error(f"Could not save draft project:\n  {custom_errors}")
            else:
                self.update_project_view()
                self.parent.controls_widget.run_button.setEnabled(True)

                for tab in self.list_tabs:
                    view_widget = self.view_tabs[tab].tables[tab.lower()]
                    idx = edit_indices[tab]
                    view_widget.list.selectionModel().setCurrentIndex(
                        view_widget.model.index(idx, 0), QtCore.QItemSelectionModel.SelectionFlag.ClearAndSelect
                    )

                self.show_project_view()

    def validate_draft_project(self) -> Generator[str, None, None]:
        """Get all errors with the draft project."""
        yield from self.validate_layers()
        yield from self.validate_contrasts()

    def validate_layers(self) -> Generator[str, None, None]:
        """Ensure that all layers in the draft project are valid, and yield errors if not.

        Yields
        ------
        str
            The message for each error in layers.

        """
        project = self.draft_project
        if project["model"] == LayerModels.StandardLayers and project["layers"]:
            layer_attrs = list(project["layers"][0].model_fields)
            layer_attrs.remove("name")
            layer_attrs.remove("hydrate_with")
            # ensure all layer parameters have been filled in, and all names are parameters that exist
            valid_params = [p.name for p in project["parameters"]] + [""]
            for i, layer in enumerate(project["layers"]):
                missing_params = []
                invalid_params = []
                for attr in layer_attrs:
                    param = getattr(layer, attr)
                    if param == "" and attr != "hydration":  # hydration is allowed to be blank
                        missing_params.append(attr)
                    elif param not in valid_params:
                        invalid_params.append((attr, param))

                if missing_params:
                    noun = "a parameter" if len(missing_params) == 1 else "parameters"
                    msg = f"Layer '{layer.name}' (row {i + 1}) is missing {noun}: {', '.join(missing_params)}"
                    yield msg
                if invalid_params:
                    noun = "an invalid value" if len(invalid_params) == 1 else "invalid values"
                    msg = f"Layer '{layer.name}' (row {i + 1}) has {noun}: {{0}}".format(
                        ",\n  ".join(f'"{v}" for parameter {p}' for p, v in invalid_params)
                    )
                    yield msg

    def validate_contrasts(self) -> Generator[str, None, None]:
        """Ensure that all contrast parameters in the draft project are valid, and yield errors if not.

        Yields
        ------
        str
            The messages for each error in contrasts.

        """
        project = self.draft_project
        if project["contrasts"]:
            contrast_attrs = list(project["contrasts"][0].model_fields)
            contrast_attrs.remove("name")
            contrast_attrs.remove("background_action")
            contrast_attrs.remove("model")
            contrast_attrs.remove("resample")
            for i, contrast in enumerate(project["contrasts"]):
                missing_params = []
                invalid_params = []
                for attr in contrast_attrs:
                    project_field_name = attr if attr in ["data", "bulk_in", "bulk_out"] else attr + "s"
                    valid_params = [p.name for p in project[project_field_name]]
                    param = getattr(contrast, attr)
                    if param == "":
                        missing_params.append(attr)
                    elif param not in valid_params:
                        invalid_params.append((attr, param))

                if missing_params:
                    msg = f"Contrast '{contrast.name}' (row {i + 1}) is missing: {', '.join(missing_params)}"
                    yield msg
                if invalid_params:
                    noun = "an invalid value" if len(invalid_params) == 1 else "invalid values"
                    msg = f"Contrast '{contrast.name}' (row {i + 1}) has {noun}: {{0}}".format(
                        ",\n  ".join(f'"{v}" for field {p}' for p, v in invalid_params)
                    )
                    yield msg

                model = contrast.model
                if project["model"] == LayerModels.StandardLayers:
                    if project["calculation"] == Calculations.Domains:
                        model_field_name = "domain_contrasts"
                    else:
                        model_field_name = "layers"
                    valid_params = [p.name for p in project[model_field_name]]
                    # strip out empty items
                    model = [item for item in model if item != ""]
                    invalid_model_vals = [item for item in model if item not in valid_params]
                    # this is the fastest way to get all unique items from a list without changing the order...
                    invalid_model_vals = list(dict.fromkeys(invalid_model_vals))
                    if invalid_model_vals:
                        noun = "an invalid model value" if len(invalid_model_vals) == 1 else "invalid model values"
                        msg = f"Contrast '{contrast.name}' (row {i + 1}) has {noun}: {{0}}".format(
                            ", ".join(invalid_model_vals)
                        )
                        yield msg
                else:
                    if not model:
                        msg = f"Contrast '{contrast.name}' (row {i + 1}) has no model set"
                        yield msg
                    elif model[0] not in [f.name for f in project["custom_files"]]:
                        msg = f"Contrast '{contrast.name}' (row {i + 1}) has invalid model: {model[0]}"
                        yield msg

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
            elif field == "backgrounds":
                self.tables[field] = BackgroundsFieldWidget(field, self)
            elif field == "resolutions":
                self.tables[field] = ResolutionsFieldWidget(field, self)
            elif field == "layers":
                self.tables[field] = LayerFieldWidget(field, self)
            elif field == "domain_contrasts":
                self.tables[field] = DomainContrastWidget(field, self)
            elif field == "custom_files":
                self.tables[field] = CustomFileWidget(field, self)
            elif field == "contrasts":
                self.tables[field] = ContrastWidget(field, self)
            elif field == "data":
                self.tables[field] = DataWidget(field, self)
            else:
                self.tables[field] = ProjectFieldWidget(field, self)
            layout.addWidget(self.tables[field])

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        # one widget must be given, not a layout,
        # or scrolling won't work properly!
        tab_widget = QtWidgets.QWidget()
        tab_widget.setLayout(layout)
        scroll_area.setWidget(tab_widget)
        scroll_area.setWidgetResizable(True)

        widget_layout = QtWidgets.QVBoxLayout()
        widget_layout.setContentsMargins(0, 0, 0, 0)
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
