"""Tests for the Presenter."""

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError
from PyQt6 import QtWidgets
from RATapi import Controls

from rascal2.ui.presenter import MainWindowPresenter


class MockUndoStack:
    """A mock Undo stack."""

    def __init__(self):
        self.stack = []

    def push(self, command):
        command.redo()


class MockWindowView(QtWidgets.QMainWindow):
    """A mock MainWindowView class."""

    def __init__(self):
        super().__init__()
        self.undo_stack = MockUndoStack()


@pytest.fixture
def presenter():
    pr = MainWindowPresenter(MockWindowView())
    pr.model = MagicMock()
    pr.model.controls = Controls()

    return pr


@pytest.mark.parametrize(["param", "value"], [("nSamples", 50), ("calcSldDuringFit", True), ("parallel", "contrasts")])
def test_set_controls_data(presenter, param, value):
    """Check that setting values are correctly propagated to the Controls object."""
    assert presenter.edit_controls(param, value)
    assert getattr(presenter.model.controls, param) == value


@pytest.mark.parametrize(
    ["param", "value"], [("nSamples", "???"), ("calcSldDuringFit", "something"), ("parallel", "bad parallel setting")]
)
def test_controls_validation_error(presenter, param, value):
    """Test that data is not changed if invalid data is passed to set."""
    try:
        presenter.edit_controls(param, value)
    except ValidationError as err:
        with pytest.raises(ValidationError, match=f"{param}"):
            raise err
    else:
        raise AssertionError("Invalid data did not raise error!")
