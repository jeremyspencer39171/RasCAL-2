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

    def createProject(self, name: str, save_path: str):
        """Creates a new RAT project and controls object then initialise UI.

        Parameters
        ----------
        name : str
            The name of the project.
        save_path : str
            The save path of the project.
        """

        self.model.createProject(name, save_path)
        self.view.setWindowTitle(self.title + " - " + name)
        # TODO if the view's central widget is the startup one then setup MDI else reset the widgets.
        self.view.init_settings_and_log(save_path)
        self.view.setupMDI()
