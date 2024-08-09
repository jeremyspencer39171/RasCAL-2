from PyQt6 import QtCore, QtGui, QtWidgets

from rascal2.config import path_for

from .presenter import MainWindowPresenter

MAIN_WINDOW_TITLE = "RasCAL-2"


class MainWindowView(QtWidgets.QMainWindow):
    """Creates the main view for the RasCAL app"""

    def __init__(self):
        super().__init__()
        self.presenter = MainWindowPresenter(self)
        window_icon = QtGui.QIcon(path_for("logo.png"))

        self.undo_stack = QtGui.QUndoStack(self)
        self.undo_view = QtWidgets.QUndoView(self.undo_stack)
        self.undo_view.setWindowTitle("Undo History")
        self.undo_view.setWindowIcon(window_icon)
        self.undo_view.setAttribute(QtCore.Qt.WidgetAttribute.WA_QuitOnClose, False)

        self.createActions()
        self.createMenus()
        self.createToolBar()
        self.createStatusBar()

        self.setWindowTitle(MAIN_WINDOW_TITLE)
        self.setMinimumSize(1024, 900)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)

    def createActions(self):
        """Creates the menu and toolbar actions"""
        self.new_project_action = QtGui.QAction("&New", self)
        self.new_project_action.setStatusTip("Create a new project")
        self.new_project_action.setIcon(QtGui.QIcon(path_for("file.png")))
        self.new_project_action.setShortcut(QtGui.QKeySequence.StandardKey.New)

        self.exit_action = QtGui.QAction("E&xit", self)
        self.exit_action.setStatusTip(f"Quit {MAIN_WINDOW_TITLE}")
        self.exit_action.setShortcut(QtGui.QKeySequence.StandardKey.Quit)
        self.exit_action.triggered.connect(self.close)

    def createMenus(self):
        """Creates the main menu and sub menus"""
        main_menu = self.menuBar()
        main_menu.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.PreventContextMenu)

        file_menu = main_menu.addMenu("&File")
        file_menu.addAction(self.new_project_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        # edit_menu = main_menu.addMenu("&Edit")
        # tools_menu = main_menu.addMenu("&Tools")
        # windows_menu = main_menu.addMenu("&Windows")
        # help_menu = main_menu.addMenu("&Help")

    def createToolBar(self):
        """Creates the toolbar"""
        toolbar = self.addToolBar("ToolBar")
        toolbar.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.PreventContextMenu)
        toolbar.setMovable(False)

        toolbar.addAction(self.new_project_action)

    def createStatusBar(self):
        """Creates the status bar"""
        sb = QtWidgets.QStatusBar()
        self.setStatusBar(sb)
