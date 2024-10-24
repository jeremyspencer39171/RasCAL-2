from pathlib import Path

import RATapi as RAT
from PyQt6 import QtCore


class MainWindowModel(QtCore.QObject):
    """Manages project data and communicates to view via signals"""

    project_updated = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()

        self.project = None
        self.results = None
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

    def update_project(self, problem_definition: RAT.rat_core.ProblemDefinition):
        """Update the project given a set of results."""
        parameter_field = {
            "parameters": "params",
            "bulk_in": "bulkIn",
            "bulk_out": "bulkOut",
            "scalefactors": "scalefactors",
            "domain_ratios": "domainRatio",
            "background_parameters": "backgroundParams",
            "resolution_parameters": "resolutionParams",
        }

        for class_list in RAT.project.parameter_class_lists:
            for index, value in enumerate(getattr(problem_definition, parameter_field[class_list])):
                getattr(self.project, class_list)[index].value = value

    def save_project(self):
        """Save the project to the save path."""

        controls_file = Path(self.save_path, "controls.json")
        controls_file.write_text(self.controls.model_dump_json())

        # TODO add saving `Project` once this is possible
        # https://github.com/RascalSoftware/python-RAT/issues/76

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
            self.controls = RAT.Controls.model_validate_json(controls_file.read_text())
        except ValueError as err:
            raise ValueError(
                "The controls.json file for this project is not valid.\n"
                "It may contain invalid parameter values or be invalid JSON."
            ) from err

        # TODO add saving `Project` once this is possible
        # https://github.com/RascalSoftware/python-RAT/issues/76
        self.project = RAT.Project()
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

    def edit_project(self, updated_project) -> None:
        """Updates the project.

        Parameters
        ----------
        updated_project : RAT.Project
            The updated project.
        """
        self.project = updated_project
        self.project_updated.emit()
