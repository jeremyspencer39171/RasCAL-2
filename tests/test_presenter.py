"""Tests for the Presenter."""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError
from PyQt6 import QtWidgets
from RATapi import Controls
from RATapi.events import ProgressEventData
from RATapi.inputs import ProblemDefinition

from rascal2.core.runner import LogData
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
        self.controls_widget = MagicMock()
        self.terminal_widget = MagicMock()
        self.handle_results = MagicMock()
        self.reset_widgets = MagicMock()
        self.logging = MagicMock()
        self.settings = MagicMock()
        self.get_project_folder = lambda: "new path/"


@pytest.fixture
def presenter():
    pr = MainWindowPresenter(MockWindowView())
    pr.runner = MagicMock()
    pr.model.controls = Controls()
    pr.model.project = MagicMock()
    pr.model.save_path = "some_path/"

    return pr


@pytest.mark.parametrize(["param", "value"], [("nSamples", 50), ("calcSldDuringFit", True), ("parallel", "contrasts")])
def test_set_controls_data(presenter, param, value):
    """Check that setting values are correctly propagated to the Controls object."""
    presenter.edit_controls(param, value)
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


@patch("RATapi.inputs.make_input")
@patch("rascal2.ui.presenter.RATRunner")
def test_run_and_interrupt(mock_runner, mock_inputs, presenter):
    """Test that the runner can be started and interrupted."""
    presenter.run()
    presenter.interrupt_terminal()

    mock_inputs.assert_called_once()
    presenter.runner.start.assert_called_once()
    presenter.runner.interrupt.assert_called_once()


@patch("RATapi.inputs.make_problem")
def test_handle_results(mock_problem_def, presenter):
    """Test that results are handed to the view correctly."""
    presenter.runner = MagicMock()
    presenter.runner.updated_problem = ProblemDefinition()
    presenter.runner.results = MagicMock()
    presenter.runner.results.calculationResults.sumChi = 0.04
    presenter.handle_results()

    presenter.view.handle_results.assert_called_once_with(presenter.runner.results)


def test_stop_run(presenter):
    """Test that log info is emitted and the run is stopped when stop_run is called."""
    presenter.runner = MagicMock()
    presenter.runner.error = None
    presenter.handle_interrupt()
    presenter.view.logging.info.assert_called_once_with("RAT run interrupted!")
    presenter.view.reset_widgets.assert_called_once()


def test_run_error(presenter):
    """Test that a critical log is emitted if stop_run is called with an error."""
    presenter.runner = MagicMock()
    presenter.runner.error = ValueError("Test error!")
    presenter.handle_interrupt()
    presenter.view.logging.error.assert_called_once_with("RAT run failed with exception:\nTest error!")


@pytest.mark.parametrize(
    ("procedure", "string"),
    [
        ("calculate", "Test message!"),
        ("simplex", "some stuff, 3443, 10.5, 9"),
        ("de", "things: 54, Best: 10.5, test... ... N: 65.3"),
    ],
)
def test_handle_message_chisquared(presenter, procedure, string):
    """Test that messages are handled correctly, including chi-squared data."""
    presenter.runner.events = [string]
    presenter.model.controls.procedure = procedure
    presenter.handle_event()
    presenter.view.terminal_widget.write.assert_called_with(string)
    if procedure in ["simplex", "de"]:
        presenter.view.controls_widget.chi_squared.setText.assert_called_with("10.5")
    else:
        presenter.view.controls_widget.chi_squared.setText.assert_not_called()


def test_handle_progress_event(presenter):
    """Test that progress events are handled correctly."""
    presenter.runner.events = [ProgressEventData()]
    presenter.handle_event()
    presenter.view.terminal_widget.update_progress.assert_called()


def test_handle_log_data(presenter):
    presenter.runner.events = [LogData(10, "Test log!")]
    presenter.handle_event()
    presenter.view.logging.log.assert_called_with(10, "Test log!")


@pytest.mark.parametrize("function", ["create_project", "load_project", "load_r1_project"])
def test_load_project(presenter, function):
    """All the project initialisation functions should run the corresponding model function and initialise UI."""
    presenter.initialise_ui = MagicMock()
    setattr(presenter.model, function, MagicMock())
    if function == "create_project":
        params = ("proj_name", "some_path/")
    else:
        presenter.model.project.name = "proj_name"
        params = ("some_path/",)

    getattr(presenter, function)(*params)

    presenter.initialise_ui.assert_called_once_with("proj_name", "some_path/")
    getattr(presenter.model, function).assert_called_once_with(*params)


@patch("rascal2.ui.presenter.update_recent_projects")
def test_save_project(recent_projects_mock, presenter):
    """Test that projects can be saved, optionally saved as a new folder."""
    presenter.model.save_project = MagicMock()
    presenter.save_project()
    presenter.model.save_project.assert_called_once()

    presenter.model.save_project.reset_mock()

    presenter.save_project(save_as=True)
    assert presenter.model.save_path == "new path/"
    presenter.model.save_project.assert_called_once()
    recent_projects_mock.assert_called_with("new path/")
