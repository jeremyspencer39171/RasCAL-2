import warnings
from typing import Any

from rascal2.core import commands

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
        self.undo_stack = self.view.undo_stack

    def create_project(self, name: str, save_path: str):
        """Creates a new RAT project and controls object then initialise UI.

        Parameters
        ----------
        name : str
            The name of the project.
        save_path : str
            The save path of the project.

        """

        self.view.setWindowTitle(self.title + " - " + name)
        self.model.create_project(name, save_path)
        # TODO if the view's central widget is the startup one then setup MDI else reset the widgets.
        # https://github.com/RascalSoftware/RasCAL-2/issues/15
        self.view.init_settings_and_log(save_path)
        self.view.setup_mdi()

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
            self.view.undo_stack.push(commands.EditControls(self.model.controls, setting, value))
            return True

    def interrupt_terminal(self):
        """Sends an interrupt signal to the terminal."""
        # TODO: stub for when issue #9 is resolved
        # https://github.com/RascalSoftware/RasCAL-2/issues/9
        pass
