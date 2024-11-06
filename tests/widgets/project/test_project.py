from unittest.mock import MagicMock

import pydantic
import pytest
import RATapi
from PyQt6 import QtCore, QtWidgets
from RATapi.utils.enums import Calculations, Geometries, LayerModels

from rascal2.widgets.project.models import (
    ClassListModel,
    ParameterFieldWidget,
    ParametersModel,
    ProjectFieldWidget,
)
from rascal2.widgets.project.project import (
    ProjectTabWidget,
    ProjectWidget,
)


class MockModel(QtCore.QObject):
    def __init__(self):
        super().__init__()
        self.project = RATapi.Project()
        self.controls = MagicMock()
        self.project_updated = MagicMock()
        self.controls_updated = MagicMock()


class MockPresenter(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.model = MockModel()
        self.edit_project = MagicMock()


class MockMainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.presenter = MockPresenter()


class DataModel(pydantic.BaseModel, validate_assignment=True):
    """A test Pydantic model."""

    name: str = "Test Model"
    value: int = 15


parent = MockMainWindow()


@pytest.fixture
def classlist():
    """A test ClassList."""
    return RATapi.ClassList([DataModel(name="A", value=1), DataModel(name="B", value=6), DataModel(name="C", value=18)])


@pytest.fixture
def table_model(classlist):
    """A test ClassListModel."""
    return ClassListModel(classlist, parent)


@pytest.fixture
def setup_project_widget():
    parent = MockMainWindow()
    project_widget = ProjectWidget(parent)
    project_widget.update_project_view()
    return project_widget


@pytest.fixture
def param_classlist():
    def _classlist(protected_indices):
        return RATapi.ClassList(
            [
                RATapi.models.ProtectedParameter(name=str(i)) if i in protected_indices else RATapi.models.Parameter()
                for i in [0, 1, 2]
            ]
        )

    return _classlist


@pytest.fixture
def param_model(param_classlist):
    def _param_model(protected_indices):
        model = ParametersModel(param_classlist(protected_indices), parent)
        return model

    return _param_model


def test_project_widget_initial_state(setup_project_widget):
    """
    Tests the inital state of the ProjectWidget class.
    """
    project_widget = setup_project_widget

    # Check the layout of the project view
    assert project_widget.stacked_widget.currentIndex() == 0

    assert project_widget.edit_project_button.isEnabled()
    assert project_widget.edit_project_button.text() == "Edit Project"

    assert project_widget.calculation_label.text() == "Calculation:"
    assert project_widget.calculation_type.text() == Calculations.NonPolarised
    assert project_widget.calculation_type.isReadOnly()

    assert project_widget.model_type_label.text() == "Model Type:"
    assert project_widget.model_type.text() == LayerModels.StandardLayers
    assert project_widget.model_type.isReadOnly()

    assert project_widget.geometry_label.text() == "Geometry:"
    assert project_widget.geometry_type.text() == Geometries.AirSubstrate
    assert project_widget.geometry_type.isReadOnly()

    # Check the layout of the edit view
    assert project_widget.save_project_button.isEnabled()
    assert project_widget.save_project_button.text() == "Save Project"

    assert project_widget.cancel_button.isEnabled()
    assert project_widget.cancel_button.text() == "Cancel"

    assert project_widget.edit_calculation_label.text() == "Calculation:"
    assert project_widget.calculation_combobox.currentText() == Calculations.NonPolarised
    for ix, calc in enumerate(Calculations):
        assert project_widget.calculation_combobox.itemText(ix) == calc

    assert project_widget.edit_model_type_label.text() == "Model Type:"
    assert project_widget.model_combobox.currentText() == LayerModels.StandardLayers
    for ix, model in enumerate(LayerModels):
        assert project_widget.model_combobox.itemText(ix) == model

    assert project_widget.edit_geometry_label.text() == "Geometry:"
    assert project_widget.geometry_combobox.currentText() == Geometries.AirSubstrate
    for ix, geometry in enumerate(Geometries):
        assert project_widget.geometry_combobox.itemText(ix) == geometry

    for ix, tab in enumerate(project_widget.tabs):
        assert project_widget.project_tab.tabText(ix) == tab
        assert project_widget.edit_project_tab.tabText(ix) == tab

    assert project_widget.project_tab.currentIndex() == 0
    assert project_widget.edit_project_tab.currentIndex() == 0


def test_edit_cancel_button_toggle(setup_project_widget):
    """
    Tests clicking the edit button cuases the stacked widget to change state.
    """
    project_widget = setup_project_widget

    assert project_widget.stacked_widget.currentIndex() == 0
    project_widget.edit_project_button.click()
    assert project_widget.stacked_widget.currentIndex() == 1

    assert project_widget.geometry_combobox.currentText() == Geometries.AirSubstrate
    assert project_widget.model_combobox.currentText() == LayerModels.StandardLayers
    assert project_widget.calculation_combobox.currentText() == Calculations.NonPolarised

    project_widget.cancel_button.click()
    assert project_widget.stacked_widget.currentIndex() == 0

    assert project_widget.geometry_type.text() == Geometries.AirSubstrate
    assert project_widget.model_type.text() == LayerModels.StandardLayers
    assert project_widget.calculation_type.text() == Calculations.NonPolarised


def test_save_changes_to_model_project(setup_project_widget):
    """
    Tests that making changes to the project settings
    """
    project_widget = setup_project_widget

    project_widget.edit_project_button.click()

    project_widget.calculation_combobox.setCurrentText(Calculations.Domains)
    project_widget.geometry_combobox.setCurrentText(Geometries.SubstrateLiquid)
    project_widget.model_combobox.setCurrentText(LayerModels.CustomXY)

    assert project_widget.draft_project["geometry"] == Geometries.SubstrateLiquid
    assert project_widget.draft_project["model"] == LayerModels.CustomXY
    assert project_widget.draft_project["calculation"] == Calculations.Domains

    project_widget.save_changes()
    assert project_widget.parent.presenter.edit_project.call_count == 1


def test_cancel_changes_to_model_project(setup_project_widget):
    """
    Tests that making changes to the project settings and
    not saving them reverts the changes.
    """
    project_widget = setup_project_widget

    project_widget.edit_project_button.click()

    project_widget.calculation_combobox.setCurrentText(Calculations.Domains)
    project_widget.geometry_combobox.setCurrentText(Geometries.SubstrateLiquid)
    project_widget.model_combobox.setCurrentText(LayerModels.CustomXY)

    assert project_widget.draft_project["geometry"] == Geometries.SubstrateLiquid
    assert project_widget.draft_project["model"] == LayerModels.CustomXY
    assert project_widget.draft_project["calculation"] == Calculations.Domains

    project_widget.cancel_button.click()
    assert project_widget.parent.presenter.edit_project.call_count == 0

    assert project_widget.calculation_combobox.currentText() == Calculations.NonPolarised
    assert project_widget.calculation_type.text() == Calculations.NonPolarised
    assert project_widget.model_combobox.currentText() == LayerModels.StandardLayers
    assert project_widget.model_type.text() == LayerModels.StandardLayers
    assert project_widget.geometry_combobox.currentText() == Geometries.AirSubstrate
    assert project_widget.geometry_type.text() == Geometries.AirSubstrate


def test_domains_tab(setup_project_widget):
    """
    Tests that domain tab is visible.
    """
    project_widget = setup_project_widget
    project_widget.edit_project_button.click()
    project_widget.calculation_combobox.setCurrentText(Calculations.Domains)
    assert project_widget.draft_project["calculation"] == Calculations.Domains
    project_widget.handle_domains_tab()

    domains_tab_index = 5
    assert project_widget.project_tab.isTabVisible(domains_tab_index)
    assert project_widget.edit_project_tab.isTabVisible(domains_tab_index)


def test_project_tab_init():
    """Test that the project tab correctly creates field widgets."""
    fields = ["my_field", "parameters", "bulk_in"]

    tab = ProjectTabWidget(fields, parent)

    for field in fields:
        if field in RATapi.project.parameter_class_lists:
            assert isinstance(tab.tables[field], ParameterFieldWidget)
        else:
            assert isinstance(tab.tables[field], ProjectFieldWidget)


@pytest.mark.parametrize("edit_mode", [True, False])
def test_project_tab_update_model(classlist, param_classlist, edit_mode):
    """Test that updating a ProjectTabEditWidget produces the desired models."""

    new_model = {"my_field": classlist, "parameters": param_classlist([])}

    tab = ProjectTabWidget(list(new_model), parent, edit_mode=edit_mode)
    # change the parent to a mock to avoid spec issues
    for table in tab.tables.values():
        table.parent = MagicMock()
    tab.update_model(new_model)

    for field in new_model:
        assert tab.tables[field].model.classlist == new_model[field]
        assert tab.tables[field].model.edit_mode == edit_mode
