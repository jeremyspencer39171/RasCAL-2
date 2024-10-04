import RATapi as RAT
from PyQt6 import QtCore


class MainWindowModel(QtCore.QObject):
    """Manages project data and communicates to view via signals"""

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
