import pathlib

from PyQt6 import QtCore, QtGui, QtWidgets

from rascal2.config import path_for, setup_logging, setup_settings
from rascal2.dialogs.project_dialog import ProjectDialog
from rascal2.widgets.startup_widget import StartUpWidget

from .presenter import MainWindowPresenter

MAIN_WINDOW_TITLE = "RasCAL-2"


class MainWindowView(QtWidgets.QMainWindow):
    """Creates the main view for the RasCAL app"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(MAIN_WINDOW_TITLE)

        self.presenter = MainWindowPresenter(self)
        window_icon = QtGui.QIcon(path_for("logo.png"))

        self.undo_stack = QtGui.QUndoStack(self)
        self.undo_view = QtWidgets.QUndoView(self.undo_stack)
        self.undo_view.setWindowTitle("Undo History")
        self.undo_view.setWindowIcon(window_icon)
        self.undo_view.setAttribute(QtCore.Qt.WidgetAttribute.WA_QuitOnClose, False)

        self.mdi = QtWidgets.QMdiArea()
        # TODO replace the widgets below
        # plotting: NO ISSUE YET
        # https://github.com/RascalSoftware/RasCAL-2/issues/5
        # https://github.com/RascalSoftware/RasCAL-2/issues/7
        # project: NO ISSUE YET
        self.plotting_widget = QtWidgets.QWidget()
        self.terminal_widget = QtWidgets.QWidget()
        self.controls_widget = QtWidgets.QWidget()
        self.project_widget = QtWidgets.QWidget()

        self.create_actions()
        self.create_menus()
        self.create_toolbar()
        self.create_status_bar()

        self.setMinimumSize(1024, 900)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)

        self.startup_dlg, self.project_dlg = StartUpWidget(self), ProjectDialog(self)

        self.setCentralWidget(self.startup_dlg)

    def show_project_dialog(self):
        """Shows the project dialog to create a new project"""
        if self.startup_dlg.isVisible():
            self.startup_dlg.hide()
        self.project_dlg = ProjectDialog(self)
        if (
            self.project_dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted
            and self.centralWidget() is self.startup_dlg
        ):
            self.startup_dlg.show()

    def create_actions(self):
        """Creates the menu and toolbar actions"""

        self.new_project_action = QtGui.QAction("&New", self)
        self.new_project_action.setStatusTip("Create a new project")
        self.new_project_action.setIcon(QtGui.QIcon(path_for("new-project.png")))
        self.new_project_action.triggered.connect(self.show_project_dialog)
        self.new_project_action.setShortcut(QtGui.QKeySequence.StandardKey.New)

        self.open_project_action = QtGui.QAction("&Open", self)
        self.open_project_action.setStatusTip("Open an existing project")
        self.open_project_action.setIcon(QtGui.QIcon(path_for("browse-dark.png")))
        self.open_project_action.setShortcut(QtGui.QKeySequence.StandardKey.Open)

        self.save_project_action = QtGui.QAction("&Save", self)
        self.save_project_action.setStatusTip("Save project")
        self.save_project_action.setIcon(QtGui.QIcon(path_for("save-project.png")))
        self.save_project_action.setShortcut(QtGui.QKeySequence.StandardKey.Save)

        self.undo_action = QtGui.QAction("&Undo", self)
        self.undo_action.setStatusTip("Undo")
        self.undo_action.setIcon(QtGui.QIcon(path_for("undo.png")))
        self.undo_action.setShortcut(QtGui.QKeySequence.StandardKey.Undo)

        self.redo_action = QtGui.QAction("&Redo", self)
        self.redo_action.setStatusTip("Redo")
        self.redo_action.setIcon(QtGui.QIcon(path_for("redo.png")))
        self.redo_action.setShortcut(QtGui.QKeySequence.StandardKey.Redo)

        self.export_plots_action = QtGui.QAction("Export", self)
        self.export_plots_action.setStatusTip("Export Plots")
        self.export_plots_action.setIcon(QtGui.QIcon(path_for("export-plots.png")))

        self.open_help_action = QtGui.QAction("&Help", self)
        self.open_help_action.setStatusTip("Open Documentation")
        self.open_help_action.setIcon(QtGui.QIcon(path_for("help.png")))
        self.open_help_action.triggered.connect(self.open_docs)

        self.exit_action = QtGui.QAction("E&xit", self)
        self.exit_action.setStatusTip(f"Quit {MAIN_WINDOW_TITLE}")
        self.exit_action.setShortcut(QtGui.QKeySequence.StandardKey.Quit)
        self.exit_action.triggered.connect(self.close)

        # Window menu actions
        self.tile_windows_action = QtGui.QAction("Tile Windows", self)
        self.tile_windows_action.setStatusTip("Arrange windows in the default grid")
        self.tile_windows_action.setIcon(QtGui.QIcon(path_for("tile.png")))
        self.tile_windows_action.triggered.connect(self.mdi.tileSubWindows)

    def create_menus(self):
        """Creates the main menu and sub menus"""
        main_menu = self.menuBar()
        main_menu.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.PreventContextMenu)

        file_menu = main_menu.addMenu("&File")
        file_menu.addAction(self.new_project_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        # edit_menu = main_menu.addMenu("&Edit")

        tools_menu = main_menu.addMenu("&Tools")
        tools_menu.addAction(self.undo_action)
        tools_menu.addAction(self.redo_action)

        windows_menu = main_menu.addMenu("&Windows")
        windows_menu.addAction(self.tile_windows_action)

        help_menu = main_menu.addMenu("&Help")
        help_menu.addAction(self.open_help_action)

    def open_docs(self):
        """Opens the documentation"""
        url = QtCore.QUrl("https://rascalsoftware.github.io/RAT-Docs/dev/index.html")
        QtGui.QDesktopServices.openUrl(url)

    def create_toolbar(self):
        """Creates the toolbar"""
        self.toolbar = self.addToolBar("ToolBar")
        self.toolbar.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.PreventContextMenu)
        self.toolbar.setMovable(False)
        self.toolbar.setEnabled(False)

        self.toolbar.addAction(self.new_project_action)
        self.toolbar.addAction(self.open_project_action)
        self.toolbar.addAction(self.save_project_action)
        self.toolbar.addAction(self.undo_action)
        self.toolbar.addAction(self.redo_action)
        self.toolbar.addAction(self.export_plots_action)
        self.toolbar.addAction(self.open_help_action)

    def create_status_bar(self):
        """Creates the status bar"""
        sb = QtWidgets.QStatusBar()
        self.setStatusBar(sb)

    def setup_mdi(self):
        """Creates the multi-document interface"""
        widgets = {
            "Plots": self.plotting_widget,
            "Project": self.project_widget,
            "Terminal": self.terminal_widget,
            "Fitting Controls": self.controls_widget,
        }

        for title, widget in reversed(widgets.items()):
            widget.setWindowTitle(title)
            window = self.mdi.addSubWindow(
                widget, QtCore.Qt.WindowType.WindowMinMaxButtonsHint | QtCore.Qt.WindowType.WindowTitleHint
            )
            window.setWindowTitle(title)
        # TODO implement user save for layouts, this should default to use saved layout and fallback to tile
        # https://github.com/RascalSoftware/RasCAL-2/issues/15
        self.mdi.tileSubWindows()
        self.startup_dlg = self.takeCentralWidget()
        self.setCentralWidget(self.mdi)

    def init_settings_and_log(self, save_path: str):
        """Initialise settings and logging for the project.

        Parameters
        ----------
        save_path : str
            The save path for the project.

        """
        proj_path = pathlib.Path(save_path)
        self.settings = setup_settings(proj_path)
        log_path = pathlib.Path(self.settings.log_path)
        if not log_path.is_absolute():
            log_path = proj_path / log_path

        log_path.parents[0].mkdir(parents=True, exist_ok=True)
        self.logging = setup_logging(log_path, level=self.settings.log_level)
