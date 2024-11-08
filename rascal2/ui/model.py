from json import JSONDecodeError
from pathlib import Path
from typing import Union

import RATapi as RAT
import RATapi.outputs
from PyQt6 import QtCore


class MainWindowModel(QtCore.QObject):
    """Manages project data and communicates to view via signals

    Emits
    -----
    project_updated
        A signal that indicates the project has been updated.
    controls_updated
        A signal that indicates the control has been updated.
    results_updated
        A signal that indicates the project and results have been updated.

    """

    project_updated = QtCore.pyqtSignal()
    controls_updated = QtCore.pyqtSignal()
    results_updated = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()

        self.project = None
        self.results = None
        self.result_log = ""
        self.controls = None

        self.save_path = ""

    def create_project(self, name: str, save_path: str):
        """Creates a new RAT project and controls object.

        Parameters
        ----------
        name : str
            The name of the project.
        save_path : str
            The save path of the project.
        """
        self.project = RAT.Project(name=name)
        self.controls = RAT.Controls()
        self.save_path = save_path

    def update_results(self, results: Union[RATapi.outputs.Results, RATapi.outputs.BayesResults]):
        """Update the project given a set of results.

        Parameters
        ----------
        results : Union[RATapi.outputs.Results, RATapi.outputs.BayesResults]
            The calculation results.
        """
        self.results = results
        self.results_updated.emit()

    def update_project(self, new_values: dict) -> None:
        """Replaces the project with a new project.

        Parameters
        ----------
        new_values : dict
            New values to set in the project.

        """
        vars(self.project).update(new_values)
        self.project_updated.emit()

    def save_project(self):
        """Save the project to the save path."""

        controls_file = Path(self.save_path, "controls.json")
        controls_file.write_text(self.controls.model_dump_json())

        project_file = Path(self.save_path, "project.json")
        project_file.write_text(RAT.utils.convert.project_to_json(self.project))

    def load_project(self, load_path: str):
        """Load a project from a project folder.

        Parameters
        ----------
        load_path : str
            The path to the project folder.

        Raises
        ------
        ValueError
            If the project files are not in a valid format.

        """
        controls_file = Path(load_path, "controls.json")
        try:
            controls = RAT.Controls.model_validate_json(controls_file.read_text())
        except ValueError as err:
            raise ValueError(
                "The controls.json file for this project is not valid.\n"
                "It may contain invalid parameter values or be invalid JSON."
            ) from err

        project_file = Path(load_path, "project.json")
        try:
            project = RAT.utils.convert.project_from_json(project_file.read_text())
        except JSONDecodeError as err:
            raise ValueError("The project.json file for this project contains invalid JSON.") from err
        except (KeyError, ValueError) as err:
            raise ValueError("The project.json file for this project is not valid.") from err

        self.controls = controls
        self.project = project
        self.save_path = load_path

    def load_r1_project(self, load_path: str):
        """Load a project from a RasCAL-1 file.

        Parameters
        ----------
        load_path : str
            The path to the RasCAL-1 file.

        """
        self.project = RAT.utils.convert.r1_to_project_class(load_path)
        self.controls = RAT.Controls()
        self.save_path = str(Path(load_path).parent)

    def update_controls(self, new_values: dict):
        """Update the control attributes.

        Parameters
        ----------
        new_values: dict
            The attribute name-value pair to updated on the controls.
        """
        vars(self.controls).update(new_values)
        self.controls_updated.emit()
