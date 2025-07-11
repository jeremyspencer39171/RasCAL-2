from unittest.mock import MagicMock

import pydantic
import pytest
import ratapi
from PyQt6 import QtCore, QtWidgets
from ratapi.utils.enums import Calculations, Geometries, LayerModels

from rascal2.widgets.project.project import ProjectTabWidget, ProjectWidget, create_draft_project
from rascal2.widgets.project.tables import (
    ClassListTableModel,
    ParameterFieldWidget,
    ParametersModel,
    ProjectFieldWidget,
)


class MockModel(QtCore.QObject):
    def __init__(self):
        super().__init__()
        self.project = ratapi.Project()
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
        self.controls_widget = MagicMock()


class DataModel(pydantic.BaseModel, validate_assignment=True):
    """A test Pydantic model."""

    name: str = "Test Model"
    value: int = 15


parent = MockMainWindow()


@pytest.fixture
def classlist():
    """A test ClassList."""
    return ratapi.ClassList([DataModel(name="A", value=1), DataModel(name="B", value=6), DataModel(name="C", value=18)])


@pytest.fixture
def table_model(classlist):
    """A test ClassListTableModel."""
    return ClassListTableModel(classlist, parent)


@pytest.fixture
def setup_project_widget():
    parent = MockMainWindow()
    project_widget = ProjectWidget(parent)
    project_widget.update_project_view()
    return project_widget


@pytest.fixture
def project_with_draft():
    draft = create_draft_project(ratapi.Project())
    project = ProjectWidget(parent)
    project.draft_project = draft
    return project


@pytest.fixture
def param_classlist():
    def _classlist(protected_indices):
        return ratapi.ClassList(
            [
                ratapi.models.ProtectedParameter(name=str(i)) if i in protected_indices else ratapi.models.Parameter()
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
    assert project_widget.calculation_type.text() == Calculations.Normal
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
    assert project_widget.calculation_combobox.currentText() == Calculations.Normal
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
    Tests clicking the edit button causes the stacked widget to change state.
    """
    project_widget = setup_project_widget

    assert project_widget.stacked_widget.currentIndex() == 0
    project_widget.edit_project_button.click()
    assert project_widget.stacked_widget.currentIndex() == 1

    assert project_widget.geometry_combobox.currentText() == Geometries.AirSubstrate
    assert project_widget.model_combobox.currentText() == LayerModels.StandardLayers
    assert project_widget.calculation_combobox.currentText() == Calculations.Normal

    project_widget.cancel_button.click()
    assert project_widget.stacked_widget.currentIndex() == 0

    assert project_widget.geometry_type.text() == Geometries.AirSubstrate
    assert project_widget.model_type.text() == LayerModels.StandardLayers
    assert project_widget.calculation_type.text() == Calculations.Normal


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

    assert project_widget.calculation_combobox.currentText() == Calculations.Normal
    assert project_widget.calculation_type.text() == Calculations.Normal
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
    project_widget.handle_tabs()

    domains_tab_index = 5
    assert project_widget.project_tab.isTabVisible(domains_tab_index)
    assert project_widget.edit_project_tab.isTabVisible(domains_tab_index)


def test_project_tab_init():
    """Test that the project tab correctly creates field widgets."""
    fields = ["my_field", "parameters", "bulk_in"]

    tab = ProjectTabWidget(fields, parent)

    for field in fields:
        if field in ratapi.project.parameter_class_lists:
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


@pytest.mark.parametrize(
    "input_params",
    [
        ([0, 1, 1, 2, 1], [0, 0, 3, 0, 1]),
        ([0, 0, 0, 1, 0], [0, 0, 1, 1, 0]),
        ([3, 3, 3, 2, 0], [0, 0, 3, 0, 1]),
    ],
)
@pytest.mark.parametrize("absorption", [True, False])
def test_project_tab_validate_layers(input_params, absorption):
    """Test that the project tab produces the correct result for validating the layers tab."""
    params = ["Param 1", "Param 2", "Invalid Param", ""]
    if absorption:
        attrs = ["thickness", "SLD_real", "SLD_imaginary", "roughness", "hydration"]
        layer_class = ratapi.models.AbsorptionLayer
    else:
        attrs = ["thickness", "SLD", "roughness", "hydration"]
        layer_class = ratapi.models.Layer
    layers = ratapi.ClassList(
        [
            layer_class(**{attr: params[input_params[0][i]] for i, attr in enumerate(attrs)}),
            layer_class(**{attr: params[input_params[1][i]] for i, attr in enumerate(attrs)}),
        ]
    )

    expected_err = []
    for i, layer in enumerate(layers):
        missing_params = [p for j, p in enumerate(attrs) if input_params[i][j] == 3]
        invalid_params = [p for j, p in enumerate(attrs) if input_params[i][j] == 2]

        if missing_params:
            noun = "a parameter" if len(missing_params) == 1 else "parameters"
            msg = f"Layer '{layer.name}' (row {i + 1}) is missing {noun}: {', '.join(missing_params)}"
            expected_err.append(msg)
        if invalid_params:
            noun = "an invalid value" if len(invalid_params) == 1 else "invalid values"
            inner_msg = [f'"Invalid Param" for parameter {p}' for p in invalid_params]
            msg = f"Layer '{layer.name}' (row {i + 1}) has {noun}: {', '.join(inner_msg)}"
            expected_err.append(msg)

    draft = create_draft_project(ratapi.Project())
    draft["layers"] = layers
    draft["parameters"] = ratapi.ClassList(
        [
            ratapi.models.Parameter(name="Param 1"),
            ratapi.models.Parameter(name="Param 2"),
        ]
    )

    project = ProjectWidget(parent)
    project.draft_project = draft

    assert list(project.validate_layers()) == expected_err


@pytest.mark.parametrize(
    "calculation, model_values",
    [
        (Calculations.Normal, ([0, 1, 1, 2, 1], [0, 0, 1, 0, 1])),
        (Calculations.Normal, ([0, 0, 0, 1, 0], [0, 0, 1, 1, 0])),
        (Calculations.Normal, ([0, 0, 0, 1, 0], [0, 0, 1, 3, 0])),
        (Calculations.Normal, ([2, 2, 3, 2, 0], [0, 0, 2, 0, 1])),
        (Calculations.Domains, ([0, 1], [1, 1])),
        (Calculations.Domains, ([0, 2], [0, 1])),
        (Calculations.Domains, ([0, 1], [1, 2])),
        (Calculations.Domains, ([2, 3], [1, 3])),
    ],
)
def test_project_tab_validate_contrast_models_standard(calculation, model_values, project_with_draft):
    """Test that contrast values are correctly validated for a standard layers calculation."""
    model_names = ["1", "2", "Invalid 1", "Invalid 2"]
    models = [[model_names[i] for i in model_values[j]] for j in [0, 1]]
    contrasts = ratapi.ClassList(
        [
            ratapi.models.Contrast(
                name=f"contrast {i}",
                data="Simulation",
                background="Background 1",
                bulk_in="SLD Air",
                bulk_out="SLD D2O",
                scalefactor="Scalefactor 1",
                resolution="Resolution 1",
                model=models[i],
            )
            for i in [0, 1]
        ]
    )

    expected_err = []
    for i in [0, 1]:
        invalid = []
        if 2 in model_values[i]:
            invalid.append("Invalid 1")
        if 3 in model_values[i]:
            invalid.append("Invalid 2")

        if invalid:
            noun = "an invalid model value" if len(invalid) == 1 else "invalid model values"
            msg = f"Contrast 'contrast {i}' (row {i + 1}) has {noun}: {{0}}".format(", ".join(invalid))
            expected_err.append(msg)

    draft = project_with_draft.draft_project
    draft["calculation"] = calculation
    draft["contrasts"] = contrasts
    draft["parameters"] = ratapi.ClassList(ratapi.models.Parameter(name="p"))
    draft["layers"] = ratapi.ClassList(
        [
            ratapi.models.Layer(name="1", thickness="p", SLD="p", roughness="p"),
            ratapi.models.Layer(name="2", thickness="p", SLD="p", roughness="p"),
        ]
    )
    draft["domain_contrasts"] = ratapi.ClassList(
        [
            ratapi.models.DomainContrast(name="1", model=["1", "2"]),
            ratapi.models.DomainContrast(name="2", model=["1", "2"]),
        ]
    )

    assert list(project_with_draft.validate_contrasts()) == expected_err


@pytest.mark.parametrize("contrast_models", [[0, 0], [0, 1], [1, 0], [1, 1]])
@pytest.mark.parametrize("calc_type", [LayerModels.CustomLayers, LayerModels.CustomXY])
def test_project_tab_validate_contrast_models_custom(contrast_models, calc_type, project_with_draft):
    """Test that contrast values are correctly validated for a custom layers/XY calculation."""
    custom_files = ["Custom File 1", "Invalid Custom File"]
    contrasts = ratapi.ClassList(
        [
            ratapi.models.Contrast(
                name=f"contrast {i}",
                data="Simulation",
                background="Background 1",
                bulk_in="SLD Air",
                bulk_out="SLD D2O",
                scalefactor="Scalefactor 1",
                resolution="Resolution 1",
                model=[custom_files[model_index]],
            )
            for i, model_index in enumerate(contrast_models)
        ]
    )

    expected_err = []
    for i, model_index in enumerate(contrast_models):
        if model_index == 1:
            expected_err.append(f"Contrast 'contrast {i}' (row {i + 1}) has invalid model: Invalid Custom File")

    draft = project_with_draft.draft_project
    draft["model"] = calc_type
    draft["custom_files"] = ratapi.ClassList([ratapi.models.CustomFile(name="Custom File 1", filename="test.py")])
    draft["contrasts"] = contrasts

    assert list(project_with_draft.validate_contrasts()) == expected_err
