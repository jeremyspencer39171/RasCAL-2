"""Tests for list tab/model views."""

from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest
from PyQt6 import QtWidgets
from RATapi import ClassList

from rascal2.widgets.project.lists import AbstractProjectListWidget, ClassListItemModel, StandardLayerModelWidget


class MockMainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.parent = MagicMock()
        self.model = MagicMock()
        self.project_widget = MagicMock()


parent = MockMainWindow()


@dataclass
class MockDataClass:
    name: str = "New Item"
    val: int = 0


class MockProjectListWidget(AbstractProjectListWidget):
    """A mock implementation of the project list widget."""

    def create_view(self, i):
        return QtWidgets.QLabel(self.model.classlist[i].name)

    def create_editor(self, i):
        return QtWidgets.QLabel(str(self.model.classlist[i].val))


@pytest.fixture
def mock_item_model():
    init_classlist = ClassList(
        [
            MockDataClass("a", 1),
            MockDataClass("b", 2),
            MockDataClass("c", 3),
        ]
    )
    return ClassListItemModel(init_classlist, parent)


@pytest.fixture
def mock_project_widget():
    def create_project_widget(edit_mode: bool = False):
        widget = MockProjectListWidget("mocks", parent)
        widget.update_model(
            ClassList(
                [
                    MockDataClass("a", 1),
                    MockDataClass("b", 2),
                    MockDataClass("c", 3),
                ]
            )
        )
        if edit_mode:
            widget.edit()

        return widget

    return create_project_widget


def test_classlist_item_model_init(mock_item_model):
    """Test that the ClassListItemModel has the expected data on creation."""
    init_classlist = ClassList(
        [
            MockDataClass("a", 1),
            MockDataClass("b", 2),
            MockDataClass("c", 3),
        ]
    )

    assert mock_item_model.classlist == init_classlist
    assert mock_item_model.item_type == MockDataClass
    assert not mock_item_model.edit_mode

    assert mock_item_model.rowCount() == 3
    for i, item in enumerate(init_classlist):
        assert mock_item_model.data(mock_item_model.index(i, 0)) == item.name
        assert mock_item_model.get_item(i) == item


def test_classlist_item_model_edit(mock_item_model):
    """Test that setting data in the ClassListItemModel works as expected."""
    mock_item_model.set_data(1, "val", 5)
    assert mock_item_model.get_item(1) == MockDataClass("b", 5)

    mock_item_model.set_data(2, "name", "d")
    assert mock_item_model.get_item(2) == MockDataClass("d", 3)


def test_classlist_item_model_append(mock_item_model):
    """Test that appending an item to the ClassListItemModel works as expected."""
    mock_item_model.append_item()

    assert mock_item_model.rowCount() == 4
    assert mock_item_model.get_item(-1) == MockDataClass()


def test_classlist_item_model_delete(mock_item_model):
    """Test that deleting items from the ClassListItemModel works as expected."""
    mock_item_model.delete_item(1)
    assert mock_item_model.rowCount() == 2
    assert mock_item_model.get_item(0) == MockDataClass("a", 1)
    assert mock_item_model.get_item(1) == MockDataClass("c", 3)


def test_project_list_widget_init():
    """Test the initial state of the abstract project list widget."""
    widget = AbstractProjectListWidget("nothing", parent)

    assert not widget.edit_mode
    assert not widget.add_button.isVisibleTo(widget)
    assert not widget.delete_button.isVisibleTo(widget)


def test_project_list_widget_edit():
    """Test the correct changes are made when edit mode is activated on the project list widget."""
    widget = AbstractProjectListWidget("nothing", parent)
    widget.edit()

    assert widget.edit_mode
    assert widget.add_button.isVisibleTo(widget)
    assert widget.delete_button.isVisibleTo(widget)


def test_project_list_widget_empty_model():
    """Test that a message is shown if an empty model is given to the widget."""
    widget = AbstractProjectListWidget("nothing", parent)
    empty_classlist = ClassList()
    empty_classlist._class_handle = None
    widget.update_model(empty_classlist)

    assert isinstance(widget.view_stack, QtWidgets.QLabel)
    assert widget.view_stack.text() == "No items are currently defined! Edit the project to add a item."


@pytest.mark.parametrize("edit_mode, expected_labels", ([False, ["a", "b", "c"]], [True, ["1", "2", "3"]]))
def test_project_list_widget_build(mock_project_widget, edit_mode, expected_labels):
    """Test that the project list widget builds correctly when given a model."""

    widget = mock_project_widget(edit_mode)

    assert widget.view_stack.count() == 3

    for i, val in enumerate(expected_labels):
        widget.view_stack.setCurrentIndex(i)

        assert widget.view_stack.currentWidget().text() == val


@pytest.mark.parametrize("edit_mode, expected_labels", ([False, ["a", "b", "c"]], [True, ["1", "2", "3"]]))
def test_project_list_widget_choose(mock_project_widget, edit_mode, expected_labels):
    """Test that the current widget changes when the item is selected."""

    widget = mock_project_widget(edit_mode)

    for i, label in enumerate(expected_labels):
        sel_mod = widget.list.selectionModel()
        sel_mod.setCurrentIndex(widget.model.index(i, 0), sel_mod.SelectionFlag.ClearAndSelect)
        assert widget.view_stack.currentWidget().text() == label


@pytest.mark.parametrize("edit_mode, expected_label", ([False, "New Item"], [True, "0"]))
def test_project_list_widget_append(mock_project_widget, edit_mode, expected_label):
    """Test that items are correctly appended to a project list widget."""

    widget = mock_project_widget(edit_mode)

    widget.append_item()

    assert widget.view_stack.count() == 4

    widget.view_stack.setCurrentIndex(3)
    assert widget.view_stack.currentWidget().text() == expected_label


def test_project_list_widget_delete(mock_project_widget):
    """Test that items are correctly deleted from a project list widget."""

    widget = mock_project_widget()

    sel_mod = widget.list.selectionModel()
    sel_mod.setCurrentIndex(widget.model.index(1, 0), sel_mod.SelectionFlag.ClearAndSelect)

    widget.delete_item()

    assert widget.view_stack.count() == 2

    for i, expected_label in enumerate(["a", "c"]):
        widget.view_stack.setCurrentIndex(i)
        assert widget.view_stack.currentWidget().text() == expected_label


def test_standard_layer_widget_init():
    """Test that the StandardLayerModelWidget initialises as expected."""

    widget = StandardLayerModelWidget(["a", "b", "c"], parent)

    assert widget.layer_list.model().stringList() == ["a", "b", "c"]


@pytest.mark.parametrize("selected_index", [0, 1, 2])
def test_standard_layer_widget_append(selected_index):
    """Test that the StandardLayerModelWidget appends items correctly."""
    init_list = ["a", "b", "c"]
    widget = StandardLayerModelWidget(init_list, parent)

    sel_mod = widget.layer_list.selectionModel()
    sel_mod.setCurrentIndex(widget.model.index(selected_index, 0), sel_mod.SelectionFlag.ClearAndSelect)
    widget.append_item()

    assert widget.model.stringList() == init_list[: selected_index + 1] + [""] + init_list[selected_index + 1 :]
    assert widget.layer_list.state() == widget.layer_list.State.EditingState


@pytest.mark.parametrize("selected_index", [0, 1, 2])
def test_standard_layer_widget_delete(selected_index):
    """Test that the StandardLayerModelWidget deletes items correctly."""
    init_list = ["a", "b", "c"]
    widget = StandardLayerModelWidget(init_list, parent)

    sel_mod = widget.layer_list.selectionModel()
    sel_mod.setCurrentIndex(widget.model.index(selected_index, 0), sel_mod.SelectionFlag.ClearAndSelect)
    widget.delete_item()

    assert widget.model.stringList() == init_list[:selected_index] + init_list[selected_index + 1 :]


@pytest.mark.parametrize("selected_index", [0, 1, 2])
@pytest.mark.parametrize("delta", [1, -1, 2, -2, 5])
def test_standard_layer_widget_move(selected_index, delta):
    """Test that the StandardLayerModelWidget moves items correctly."""
    init_list = ["a", "b", "c"]
    widget = StandardLayerModelWidget(init_list, parent)

    sel_mod = widget.layer_list.selectionModel()
    sel_mod.setCurrentIndex(widget.model.index(selected_index, 0), sel_mod.SelectionFlag.ClearAndSelect)
    widget.move_item(delta)

    init_list.insert(max(selected_index + delta, 0), init_list.pop(selected_index))
    assert widget.model.stringList() == init_list
