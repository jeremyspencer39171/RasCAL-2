"""File for Qt commands."""

import copy
from enum import IntEnum, unique
from typing import Callable, Union

import ratapi
from PyQt6 import QtGui
from ratapi import ClassList


@unique
class CommandID(IntEnum):
    """Unique ID for undoable commands"""

    EditControls = 1000
    EditProject = 2000


class AbstractModelEdit(QtGui.QUndoCommand):
    """Command for editing an attribute of the model."""

    attribute = None

    def __init__(self, new_values: dict, presenter):
        super().__init__()
        self.presenter = presenter
        self.new_values = new_values
        if self.attribute is None:
            raise NotImplementedError("AbstractEditModel should not be instantiated directly.")
        else:
            self.model_class = getattr(self.presenter.model, self.attribute)
        self.old_values = {attr: getattr(self.model_class, attr) for attr in self.new_values}
        self.update_text()

    def update_text(self):
        """Update the undo command text."""
        if len(self.new_values) == 1:
            attr, value = list(self.new_values.items())[0]
            if isinstance(list(self.new_values.values())[0], ClassList):
                text = f"Changed values in {attr}"
            else:
                text = f"Set {self.attribute} {attr} to {value}"
        else:
            text = f"Save update to {self.attribute}"

        self.setText(text)

    @property
    def update_attribute(self) -> Callable:
        """Return the method used to update the attribute."""
        raise NotImplementedError

    def undo(self):
        self.update_attribute(self.old_values)

    def redo(self):
        self.update_attribute(self.new_values)

    def mergeWith(self, command):
        """Merges consecutive Edit controls commands if the attributes are the
        same."""

        # We should think about if merging all Edit controls irrespective of
        # attribute is the way to go for UX
        if list(self.new_values.keys()) != list(command.new_values.keys()):
            return False

        if list(self.old_values.values()) == list(command.new_values.values()):
            self.setObsolete(True)

        self.new_values = command.new_values
        self.update_text()
        return True

    def id(self):
        """Returns ID used for merging commands"""
        raise NotImplementedError


class EditControls(AbstractModelEdit):
    attribute = "controls"

    @property
    def update_attribute(self):
        return self.presenter.model.update_controls

    def id(self):
        return CommandID.EditControls


class EditProject(AbstractModelEdit):
    attribute = "project"

    @property
    def update_attribute(self):
        return self.presenter.model.update_project

    def id(self):
        return CommandID.EditProject


class SaveCalculationOutputs(QtGui.QUndoCommand):
    """Command for saving the updated problem, results, and log text from a calculation run.

    Parameters
    ----------
    problem : ratapi.rat_core.ProblemDefinition
        The updated parameter values from a RAT run
    results : Union[ratapi.outputs.Results, ratapi.outputs.BayesResults]
        The calculation results.
    log : str
        log text from the given calculation.
    presenter : MainWindowPresenter
        The RasCAL main window presenter
    """

    def __init__(
        self,
        problem: ratapi.rat_core.ProblemDefinition,
        results: Union[ratapi.outputs.Results, ratapi.outputs.BayesResults],
        log: str,
        presenter,
    ):
        super().__init__()
        self.presenter = presenter
        self.results = results
        self.log = log
        self.problem = self.get_parameter_values(problem)
        self.old_problem = self.get_parameter_values(ratapi.inputs.make_problem(self.presenter.model.project))
        self.old_results = copy.deepcopy(self.presenter.model.results)
        self.old_log = self.presenter.model.result_log
        self.setText("Save calculation results")

    def get_parameter_values(self, problem: ratapi.rat_core.ProblemDefinition):
        """Gets updated parameter values from problem definition.

        Parameters
        ----------
        problem : ratapi.rat_core.ProblemDefinition
            The updated parameter values from a RAT run.

        Returns
        -------
        values : dict
            A dict with updated parameter values from a RAT run.
        """
        parameter_field = {
            "parameters": "params",
            "bulk_in": "bulkIns",
            "bulk_out": "bulkOuts",
            "scalefactors": "scalefactors",
            "domain_ratios": "domainRatios",
            "background_parameters": "backgroundParams",
            "resolution_parameters": "resolutionParams",
        }

        values = {}
        for class_list in ratapi.project.parameter_class_lists:
            entry = values.setdefault(class_list, [])
            entry.extend(getattr(problem, parameter_field[class_list]))
        return values

    def set_parameter_values(self, values: dict):
        """Updates the parameter values of the project in the main window model.

        Parameters
        ----------
        values : dict
            A dict with updated parameter values from a RAT run
        """
        for key, value in values.items():
            for index in range(len(value)):
                getattr(self.presenter.model.project, key)[index].value = value[index]

    def undo(self):
        self.update_calculation_outputs(self.old_problem, self.old_results, self.old_log)

    def redo(self):
        self.update_calculation_outputs(self.problem, self.results, self.log)

    def update_calculation_outputs(
        self,
        problem: ratapi.rat_core.ProblemDefinition,
        results: Union[ratapi.outputs.Results, ratapi.outputs.BayesResults],
        log: str,
    ):
        """Updates the project, results and log in the main window model

        Parameters
        ----------
        problem : ratapi.rat_core.ProblemDefinition
            The updated parameter values from a RAT run
        results : Union[ratapi.outputs.Results, ratapi.outputs.BayesResults]
            The calculation results.
        log : str
            log text from the given calculation.
        """
        self.set_parameter_values(problem)
        self.presenter.model.update_results(copy.deepcopy(results))
        self.presenter.model.result_log = log
        chi_text = "" if results is None else f"{results.calculationResults.sumChi:.6g}"
        self.presenter.view.controls_widget.chi_squared.setText(chi_text)
        self.presenter.view.terminal_widget.clear()
        self.presenter.view.terminal_widget.write(log)
        self.presenter.view.project_widget.update_project_view()
