"""Widget for the Project window."""

from copy import deepcopy

import RATapi
from PyQt6 import QtCore, QtGui, QtWidgets
from RATapi.utils.enums import Calculations, Geometries, LayerModels

from rascal2.config import path_for
from rascal2.widgets.project.models import ParameterFieldWidget, ProjectFieldWidget


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
        super().__init__(parent)
        self.parent = parent
        self.parent_model = self.parent.presenter.model

        self.parent_model.project_updated.connect(self.update_project_view)
        self.parent_model.controls_updated.connect(self.handle_controls_update)

        self.tabs = {
            "Parameters": ["parameters"],
            "Experimental Parameters": ["scalefactors", "bulk_in", "bulk_out"],
            "Layers": [],
            "Data": [],
            "Backgrounds": [],
            "Contrasts": [],
            "Domains": [],
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
        main_layout = QtWidgets.QGridLayout()
        main_layout.setVerticalSpacing(20)

        self.edit_project_button = QtWidgets.QPushButton(
            "Edit Project", self, objectName="bluebutton", icon=QtGui.QIcon(path_for("edit.png"))
        )
        self.edit_project_button.clicked.connect(self.show_edit_view)
        main_layout.addWidget(self.edit_project_button, 0, 5)

        self.calculation_label = QtWidgets.QLabel("Calculation:", self, objectName="boldlabel")

        self.calculation_type = QtWidgets.QLineEdit(self)
        self.calculation_type.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.calculation_type.setReadOnly(True)

        main_layout.addWidget(self.calculation_label, 1, 0, 1, 1)
        main_layout.addWidget(self.calculation_type, 1, 1, 1, 1)

        self.model_type_label = QtWidgets.QLabel("Model Type:", self, objectName="boldlabel")

        self.model_type = QtWidgets.QLineEdit(self)
        self.model_type.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.model_type.setReadOnly(True)

        main_layout.addWidget(self.model_type_label, 1, 2, 1, 1)
        main_layout.addWidget(self.model_type, 1, 3, 1, 1)

        self.geometry_label = QtWidgets.QLabel("Geometry:", self, objectName="boldlabel")

        self.geometry_type = QtWidgets.QLineEdit(self)
        self.geometry_type.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.geometry_type.setReadOnly(True)

        main_layout.addWidget(self.geometry_label, 1, 4, 1, 1)
        main_layout.addWidget(self.geometry_type, 1, 5, 1, 1)

        self.project_tab = QtWidgets.QTabWidget()

        for tab, fields in self.tabs.items():
            widget = self.view_tabs[tab] = ProjectTabWidget(fields, self)
            self.project_tab.addTab(widget, tab)

        main_layout.addWidget(self.project_tab, 2, 0, 1, 6)
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

        layout = QtWidgets.QHBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.save_project_button)
        layout.addWidget(self.cancel_button)
        main_layout.addLayout(layout)

        self.edit_calculation_label = QtWidgets.QLabel("Calculation:", self, objectName="boldlabel")

        self.calculation_combobox = QtWidgets.QComboBox(self)
        self.calculation_combobox.addItems([calc for calc in Calculations])

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.edit_calculation_label)
        layout.addWidget(self.calculation_combobox)

        self.edit_model_type_label = QtWidgets.QLabel("Model Type:", self, objectName="boldlabel")

        self.model_combobox = QtWidgets.QComboBox(self)
        self.model_combobox.addItems([model for model in LayerModels])

        layout.addWidget(self.edit_model_type_label)
        layout.addWidget(self.model_combobox)

        self.edit_geometry_label = QtWidgets.QLabel("Geometry:", self, objectName="boldlabel")

        self.geometry_combobox = QtWidgets.QComboBox(self)
        self.geometry_combobox.addItems([geo for geo in Geometries])

        layout.addWidget(self.edit_geometry_label)
        layout.addWidget(self.geometry_combobox)
        main_layout.addLayout(layout)

        self.calculation_combobox.currentTextChanged.connect(lambda s: self.update_draft_project({"calculation": s}))
        self.calculation_combobox.currentTextChanged.connect(lambda: self.handle_domains_tab())
        self.model_combobox.currentTextChanged.connect(lambda s: self.update_draft_project({"model": s}))
        self.geometry_combobox.currentTextChanged.connect(lambda s: self.update_draft_project({"geometry": s}))
        self.edit_project_tab = QtWidgets.QTabWidget()

        for tab, fields in self.tabs.items():
            widget = self.edit_tabs[tab] = ProjectTabWidget(fields, self, edit_mode=True)
            self.edit_project_tab.addTab(widget, tab)

        main_layout.addWidget(self.edit_project_tab)

        edit_project_widget.setLayout(main_layout)

        return edit_project_widget

    def update_project_view(self) -> None:
        """Updates the project view."""
        # draft project is a dict containing all the attributes of the parent model,
        # because we don't want validation errors going off while editing the model is in-progress
        self.draft_project: dict = create_draft_project(self.parent_model.project)

        self.calculation_type.setText(self.parent_model.project.calculation)
        self.model_type.setText(self.parent_model.project.model)
        self.geometry_type.setText(self.parent_model.project.geometry)

        self.calculation_combobox.setCurrentText(self.parent_model.project.calculation)
        self.model_combobox.setCurrentText(self.parent_model.project.model)
        self.geometry_combobox.setCurrentText(self.parent_model.project.geometry)

        for tab in self.tabs:
            self.view_tabs[tab].update_model(self.draft_project)
            self.edit_tabs[tab].update_model(self.draft_project)

        self.handle_domains_tab()
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

    def handle_domains_tab(self) -> None:
        """Displays or hides the domains tab"""
        domain_tab_index = list(self.view_tabs).index("Domains")
        is_domains = self.calculation_combobox.currentText() == Calculations.Domains
        self.project_tab.setTabVisible(domain_tab_index, is_domains)
        self.edit_project_tab.setTabVisible(domain_tab_index, is_domains)

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
        self.stacked_widget.setCurrentIndex(0)

    def show_edit_view(self) -> None:
        """Show edit view"""
        self.setWindowTitle("Edit Project")
        self.update_project_view()
        self.stacked_widget.setCurrentIndex(1)

    def save_changes(self) -> None:
        """Save changes to the project."""
        self.parent.presenter.edit_project(self.draft_project)
        self.update_project_view()
        self.show_project_view()

    def cancel_changes(self) -> None:
        """Cancel changes to the project."""
        self.update_project_view()
        self.show_project_view()


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
