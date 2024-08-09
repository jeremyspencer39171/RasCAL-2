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

    def createProject(self, name: str, save_path: str):
        self.model.createProject(name, save_path)
        # Do nice GUI stuff after creation
        # self.view.doStuff()
