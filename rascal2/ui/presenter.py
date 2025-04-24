import re
import warnings
from typing import Any

import RATapi as RAT

from rascal2.core import commands
from rascal2.core.runner import LogData, RATRunner
from rascal2.core.settings import update_recent_projects

from .model import MainWindowModel


class MainWindowPresenter:
    """Facilitates interaction between View and Model

    Parameters
    ----------
    view : MainWindow
        main window view instance.
    """

    def __init__(self, view):
        self.view = view
        self.model = MainWindowModel()
        self.title = self.view.windowTitle()

    def create_project(self, name: str, save_path: str):
        """Creates a new RAT project and controls object then initialise UI.

        Parameters
        ----------
        name : str
            The name of the project.
        save_path : str
            The save path of the project.

        """
        self.model.create_project(name, save_path)
        self.initialise_ui(name, save_path)

    def load_project(self, load_path: str):
        """Load an existing RAT project then initialise UI.

        Parameters
        ----------
        load_path : str
            The path from which to load the project.

        """
        try:
            self.model.load_project(load_path)
        except ValueError as err:
            self.view.logging.error(f"Failed to load project at path {load_path}:\n {err}")
            raise err  # so that it can be captured by the widget
        self.initialise_ui(self.model.project.name, load_path)

    def load_r1_project(self, load_path: str):
        """Load a RAT project from a RasCAL-1 project file.

        Parameters
        ----------
        load_path : str
            The path to the R1 file.

        """
        self.model.load_r1_project(load_path)
        self.initialise_ui(self.model.project.name, self.model.save_path)

    def initialise_ui(self, name: str, save_path: str):
        """Initialise UI for a project.

        Parameters
        ----------
        name : str
            The name of the project.
        save_path : str
            The save path of the project.

        """
        self.view.setWindowTitle(self.title + " - " + name)
        self.view.init_settings_and_log(save_path)
        self.view.setup_mdi()
        self.view.undo_stack.clear()
        self.view.enable_elements()

    def edit_controls(self, setting: str, value: Any):
        """Edit a setting in the Controls object.

        Parameters
        ----------
        setting : str
            Which setting in the Controls object should be changed.
        value : Any
            The value which the setting should be changed to.

        Raises
        ------
        ValidationError
            If the setting is changed to an invalid value.

        """
        # FIXME: without proper logging,
        # we have to check validation in advance because PyQt doesn't return
        # the exception, it just falls over in C++
        # also doing it this way stops bad changes being pushed onto the stack
        # https://github.com/RascalSoftware/RasCAL-2/issues/26
        # also suppress warnings (we get warning for setting params not matching
        # procedure on initialisation) to avoid clogging stdout
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.model.controls.model_validate({setting: value})
            self.view.undo_stack.push(commands.EditControls({setting: value}, self))

    def save_project(self, save_as: bool = False):
        """Save the model.

        Parameters
        ----------
        save_as : bool
            Whether we are saving to the existing save path or to a specified folder.

        """
        # we use this isinstance rather than `is not None`
        # because some PyQt signals will send bools and so on to this as a slot!
        if save_as:
            to_path = self.view.get_project_folder()
            if not to_path:
                return
            self.model.save_path = to_path

        self.model.save_project()
        update_recent_projects(self.model.save_path)

    def interrupt_terminal(self):
        """Sends an interrupt signal to the RAT runner."""
        self.runner.interrupt()

    def run(self, procedure: RAT.utils.enums.Procedures = None):
        """Run RAT.

        Parameters
        ----------
        procedure : Procedures, optional
            What procedure to run with. If None, will use the procedure
            from the model controls.

        """
        # reset terminal
        self.view.terminal_widget.progress_bar.setVisible(False)
        if self.view.settings.clear_terminal:
            self.view.terminal_widget.clear()

        # hide bayes plots button so users can't open plots during run
        self.view.plot_widget.bayes_plots_button.setVisible(False)

        # saving the old procedure, changing it, and setting it back at the end
        # is cheaper than copying controls if procedure is not None
        old_procedure = self.model.controls.procedure
        if procedure is not None:
            self.model.controls.procedure = procedure

        rat_inputs = RAT.inputs.make_input(self.model.project, self.model.controls)
        display_on = self.model.controls.display != RAT.utils.enums.Display.Off

        self.runner = RATRunner(rat_inputs, self.model.controls.procedure, display_on)
        self.runner.finished.connect(self.handle_results)
        self.runner.stopped.connect(self.handle_interrupt)
        self.runner.event_received.connect(self.handle_event)
        self.runner.start()

        self.model.controls.procedure = old_procedure

    def handle_results(self):
        """Handle a RAT run being finished."""
        self.view.undo_stack.push(
            commands.SaveCalculationOutputs(
                self.runner.updated_problem,
                self.runner.results,
                self.view.terminal_widget.text_area.toPlainText(),
                self,
            )
        )
        self.view.handle_results(self.runner.results)

    def handle_interrupt(self):
        """Handle a RAT run being interrupted."""
        if self.runner.error is None:
            self.view.logging.info("RAT run interrupted!")
        else:
            self.view.logging.error(f"RAT run failed with exception:\n{self.runner.error}")
        self.view.reset_widgets()

    def handle_event(self):
        """Handle event data produced by the RAT run."""
        event = self.runner.events.pop(0)
        match event:
            case str():
                self.view.terminal_widget.write(event)
                chi_squared = get_live_chi_squared(event, str(self.model.controls.procedure))
                if chi_squared is not None:
                    self.view.controls_widget.chi_squared.setText(chi_squared)
            case RAT.events.ProgressEventData():
                self.view.terminal_widget.update_progress(event)
            case RAT.events.PlotEventData():
                self.view.plot_widget.plot_event(event)
            case LogData():
                self.view.logging.log(event.level, event.msg)

    def edit_project(self, updated_project: dict) -> None:
        """Edit the Project with a dictionary of attributes.

        Parameters
        ----------
        updated_project : dict
            The updated project attributes.

        Raises
        ------
        ValidationError
            If the updated project attributes are not valid.

        """
        project_dict = self.model.project.model_dump()
        project_dict.update(updated_project)
        self.model.project.model_validate(project_dict)
        self.view.undo_stack.push(commands.EditProject(updated_project, self))


# '\d+\.\d+' is the regex for
# 'some integer, then a decimal point, then another integer'
# the parentheses () mean it is put in capture group 1,
# which is what we return as the chi-squared value
# we compile these regexes on import to make `get_live_chi_squared` basically instant
chi_squared_patterns = {
    "simplex": re.compile(r"(\d+\.\d+)"),
    "de": re.compile(r"Best: (\d+\.\d+)"),
}


def get_live_chi_squared(item: str, procedure: str) -> str | None:
    """Get the chi-squared value from iteration message data.

    Parameters
    ----------
    item : str
        The iteration message.
    procedure : str
        The procedure currently running.

    Returns
    -------
    str or None
        The chi-squared value from that procedure's message data in string form,
        or None if one has not been found.

    """
    if procedure not in chi_squared_patterns:
        return None
    # match returns None if no match found, so whether one is found can be checked via 'if match'
    return match.group(1) if (match := chi_squared_patterns[procedure].search(item)) else None
