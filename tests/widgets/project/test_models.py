from unittest.mock import MagicMock

import pydantic
import pytest
import RATapi
from PyQt6 import QtCore, QtWidgets

import rascal2.widgets.delegates as delegates
import rascal2.widgets.inputs as inputs
from rascal2.widgets.project.models import (
    ClassListModel,
    ParameterFieldWidget,
    ParametersModel,
    ProjectFieldWidget,
)


class MockMainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.presenter = MagicMock()
        self.update_project = MagicMock()


class DataModel(pydantic.BaseModel, validate_assignment=True):
    """A test Pydantic model."""

    name: str = "Test Model"
    value: int = 15


@pytest.fixture
def classlist():
    """A test ClassList."""
    return RATapi.ClassList([DataModel(name="A", value=1), DataModel(name="B", value=6), DataModel(name="C", value=18)])


@pytest.fixture
def table_model(classlist):
    """A test ClassListModel."""
    return ClassListModel(classlist, parent)


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


parent = MockMainWindow()


def test_model_init(table_model, classlist):
    """Test that initialisation works correctly for ClassListModels."""
    model = table_model

    assert model.classlist == classlist
    assert model.item_type == DataModel
    assert model.headers == ["name", "value"]
    assert not model.edit_mode


def test_model_layout_data(table_model):
    """Test that the model layout and data is as expected."""
    model = table_model

    assert model.rowCount() == 3
    assert model.columnCount() == 3

    expected_data = [[None, "A", 1], [None, "B", 6], [None, "C", 18]]
    headers = [None, "Name", "Value"]

    for row in [0, 1, 2]:
        for column in [0, 1, 2]:
            assert model.data(model.index(row, column)) == expected_data[row][column]

    for column in [0, 1, 2]:
        assert model.headerData(column, QtCore.Qt.Orientation.Horizontal) == headers[column]


def test_model_set_data(table_model):
    """Test that data can be set successfully, but is thrown out if it breaks the Pydantic model rules."""
    model = table_model

    assert model.setData(model.index(1, 2), 4)
    assert model.classlist[1].value == 4

    assert model.setData(model.index(1, 1), "D")
    assert model.classlist[1].name == "D"

    assert not model.setData(model.index(2, 2), 19.4)
    assert model.classlist[2].value == 18


def test_append(table_model):
    """Test that append_item successfully adds an item of the relevant type."""
    model = table_model

    model.append_item()

    assert len(model.classlist) == 4
    assert model.classlist[-1].name == "Test Model"
    assert model.classlist[-1].value == 15


def test_delete(table_model):
    """Test that delete_item deletes the item at the desired index."""
    model = table_model

    model.delete_item(1)

    assert len(model.classlist) == 2
    assert [m.name for m in model.classlist] == ["A", "C"]
    assert [m.value for m in model.classlist] == [1, 18]


def test_project_field_init():
    """Test that the ProjectFieldWidget is initialised correctly."""
    widget = ProjectFieldWidget("test", parent)

    assert widget.table.model() is None
    assert widget.add_button.isHidden()


def test_project_field_update_model(classlist):
    """Test that the correct changes are made when the model is updated in the ProjectFieldWidget."""
    widget = ProjectFieldWidget("test", parent)
    widget.update_model(classlist)

    assert widget.table.isColumnHidden(0)

    assert widget.model.classlist == classlist
    assert isinstance(
        widget.table.itemDelegateForColumn(1).createEditor(None, None, widget.model.index(1, 1)),
        inputs.BaseInputWidget,
    )
    assert isinstance(
        widget.table.itemDelegateForColumn(2).createEditor(None, None, widget.model.index(1, 2)),
        inputs.IntInputWidget,
    )


def test_edit_mode(classlist):
    """Test that edit mode makes the expected changes."""
    widget = ProjectFieldWidget("test", parent)
    widget.update_model(classlist)
    widget.edit()

    assert widget.model.edit_mode
    assert not widget.add_button.isHidden()
    assert not widget.table.isColumnHidden(0)

    for row in [0, 1, 2]:
        assert isinstance(widget.table.indexWidget(widget.model.index(row, 0)), QtWidgets.QPushButton)


def test_delete_button(classlist):
    """Test that delete buttons work as expected."""
    widget = ProjectFieldWidget("Test", parent)
    widget.update_model(classlist)

    delete_button = widget.make_delete_button(1)
    delete_button.click()

    assert len(widget.model.classlist) == 2
    assert [m.name for m in widget.model.classlist] == ["A", "C"]
    assert [m.value for m in widget.model.classlist] == [1, 18]


def test_parameter_edit_mode(param_classlist):
    """Test that parameter tab edit mode makes the expected changes."""
    widget = ProjectFieldWidget("Test", parent)
    widget.update_model(param_classlist([]))
    widget.edit()

    assert widget.model.edit_mode
    assert not widget.add_button.isHidden()
    assert not widget.table.isColumnHidden(0)

    for row in [0, 1, 2]:
        assert isinstance(widget.table.indexWidget(widget.model.index(row, 0)), QtWidgets.QPushButton)


@pytest.mark.parametrize("protected", ([], [0, 2], [1]))
@pytest.mark.parametrize("prior_type", ("uniform", "gaussian"))
def test_parameter_flags(param_model, prior_type, protected):
    """Test that protected parameters are successfully recorded and flagged, and parameter flags are set correctly."""
    model = param_model(protected)
    for param in model.classlist:
        param.prior_type = prior_type

    assert model.protected_indices == protected

    model.edit_mode = True

    for row in [0, 1, 2]:
        for column in range(1, model.columnCount()):
            item_flags = model.flags(model.index(row, column))
            match model.headers[column - 1]:
                case "name":
                    if row in protected:
                        assert not item_flags & QtCore.Qt.ItemFlag.ItemIsEditable
                    else:
                        assert item_flags & QtCore.Qt.ItemFlag.ItemIsEditable
                case "fit":
                    assert item_flags & QtCore.Qt.ItemFlag.ItemIsUserCheckable
                case "mu" | "sigma":
                    if prior_type == "uniform":
                        assert item_flags == QtCore.Qt.ItemFlag.NoItemFlags
                    else:
                        assert item_flags & QtCore.Qt.ItemFlag.ItemIsEditable


def test_param_item_delegates(param_classlist):
    """Test that parameter models have the expected item delegates."""
    widget = ParameterFieldWidget("Test", parent)
    widget.parent = MagicMock()
    widget.update_model(param_classlist([]))

    for column, header in enumerate(widget.model.headers, start=1):
        if header in ["min", "value", "max"]:
            assert isinstance(widget.table.itemDelegateForColumn(column), delegates.ValueSpinBoxDelegate)
        else:
            assert isinstance(widget.table.itemDelegateForColumn(column), delegates.ValidatedInputDelegate)


def test_hidden_bayesian_columns(param_classlist):
    """Test that Bayes columns are hidden when procedure is not Bayesian."""
    widget = ParameterFieldWidget("Test", parent)
    widget.parent = MagicMock()
    widget.update_model(param_classlist([]))
    mock_controls = widget.parent.parent.parent_model.controls = MagicMock()
    mock_controls.procedure = "calculate"
    bayesian_columns = ["prior_type", "mu", "sigma"]

    widget.handle_bayesian_columns("calculate")

    for item in bayesian_columns:
        index = widget.model.headers.index(item)
        assert widget.table.isColumnHidden(index + 1)

    widget.handle_bayesian_columns("dream")

    for item in bayesian_columns:
        index = widget.model.headers.index(item)
        assert not widget.table.isColumnHidden(index + 1)
