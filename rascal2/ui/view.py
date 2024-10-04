import pathlib

from PyQt6 import QtCore, QtGui, QtWidgets

from rascal2.config import path_for, setup_logging, setup_settings
from rascal2.core.settings import MDIGeometries, Settings
from rascal2.dialogs.project_dialog import ProjectDialog
from rascal2.dialogs.settings_dialog import SettingsDialog
from rascal2.widgets import ControlsWidget, TerminalWidget
from rascal2.widgets.startup_widget import StartUpWidget

from .presenter import MainWindowPresenter

MAIN_WINDOW_TITLE = "RasCAL-2"


class MainWindowView(QtWidgets.QMainWindow):
    """Creates the main view for the RasCAL app"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(MAIN_WINDOW_TITLE)

        window_icon = QtGui.QIcon(path_for("logo.png"))

        self.undo_stack = QtGui.QUndoStack(self)
        self.undo_view = QtWidgets.QUndoView(self.undo_stack)
        self.undo_view.setWindowTitle("Undo History")
        self.undo_view.setWindowIcon(window_icon)
        self.undo_view.setAttribute(QtCore.Qt.WidgetAttribute.WA_QuitOnClose, False)

        self.presenter = MainWindowPresenter(self)
        self.mdi = QtWidgets.QMdiArea()
        # TODO replace the widgets below
        # plotting: NO ISSUE YET
        # https://github.com/RascalSoftware/RasCAL-2/issues/5
        # https://github.com/RascalSoftware/RasCAL-2/issues/7
        # project: NO ISSUE YET
        self.plotting_widget = QtWidgets.QWidget()
        self.terminal_widget = TerminalWidget(self)
        self.controls_widget = ControlsWidget(self)
        self.project_widget = QtWidgets.QWidget()

        self.disabled_elements = []

        self.create_actions()
        self.create_menus()
        self.create_toolbar()
        self.create_status_bar()

        self.setMinimumSize(1024, 900)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)

        self.settings = Settings()
        self.startup_dlg = StartUpWidget(self)
        self.project_dlg = ProjectDialog(self)

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

    def show_settings_dialog(self):
        """Shows the settings dialog to adjust program settings"""
        settings_dlg = SettingsDialog(self)
        settings_dlg.show()

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
        self.save_project_action.setEnabled(False)
        self.disabled_elements.append(self.save_project_action)

        self.undo_action = self.undo_stack.createUndoAction(self, "&Undo")
        self.undo_action.setStatusTip("Undo the last action")
        self.undo_action.setIcon(QtGui.QIcon(path_for("undo.png")))
        self.undo_action.setShortcut(QtGui.QKeySequence.StandardKey.Undo)
        self.undo_action.setEnabled(False)
        self.disabled_elements.append(self.undo_action)

        self.redo_action = self.undo_stack.createRedoAction(self, "&Redo")
        self.redo_action.setStatusTip("Redo the last undone action")
        self.redo_action.setIcon(QtGui.QIcon(path_for("redo.png")))
        self.redo_action.setShortcut(QtGui.QKeySequence.StandardKey.Redo)
        self.redo_action.setEnabled(False)
        self.disabled_elements.append(self.redo_action)

        self.undo_view_action = QtGui.QAction("Undo &History", self)
        self.undo_view_action.setStatusTip("View undo history")
        self.undo_view_action.triggered.connect(self.undo_view.show)
        self.undo_view_action.setEnabled(False)
        self.disabled_elements.append(self.undo_view_action)

        self.export_plots_action = QtGui.QAction("Export", self)
        self.export_plots_action.setStatusTip("Export Plots")
        self.export_plots_action.setIcon(QtGui.QIcon(path_for("export-plots.png")))
        self.export_plots_action.setEnabled(False)
        self.disabled_elements.append(self.export_plots_action)

        self.settings_action = QtGui.QAction("Settings", self)
        self.settings_action.setStatusTip("Settings")
        self.settings_action.setIcon(QtGui.QIcon(path_for("settings.png")))
        self.settings_action.triggered.connect(self.show_settings_dialog)
        self.settings_action.setEnabled(False)
        self.disabled_elements.append(self.settings_action)

        self.export_plots_action = QtGui.QAction("Export", self)
        self.export_plots_action.setStatusTip("Export Plots")
        self.export_plots_action.setIcon(QtGui.QIcon(path_for("export-plots.png")))
        self.export_plots_action.setEnabled(False)
        self.disabled_elements.append(self.export_plots_action)

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
        self.tile_windows_action.setStatusTip("Arrange windows in the default grid.")
        self.tile_windows_action.setIcon(QtGui.QIcon(path_for("tile.png")))
        self.tile_windows_action.triggered.connect(self.mdi.tileSubWindows)
        self.tile_windows_action.setEnabled(False)
        self.disabled_elements.append(self.tile_windows_action)

        self.reset_windows_action = QtGui.QAction("Reset to Default")
        self.reset_windows_action.setStatusTip("Reset the windows to their default arrangement.")
        self.reset_windows_action.triggered.connect(self.reset_mdi_layout)
        self.reset_windows_action.setEnabled(False)
        self.disabled_elements.append(self.reset_windows_action)

        self.save_default_windows_action = QtGui.QAction("Save Current Window Positions")
        self.save_default_windows_action.setStatusTip("Set the current window positions as default.")
        self.save_default_windows_action.triggered.connect(self.save_mdi_layout)
        self.save_default_windows_action.setEnabled(False)
        self.disabled_elements.append(self.save_default_windows_action)

        # Terminal menu actions
        self.clear_terminal_action = QtGui.QAction("Clear Terminal", self)
        self.clear_terminal_action.setStatusTip("Clear text in the terminal")
        self.clear_terminal_action.triggered.connect(self.terminal_widget.clear)

    def create_menus(self):
        """Creates the main menu and sub menus"""
        self.main_menu = self.menuBar()
        self.main_menu.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.PreventContextMenu)

        self.file_menu = self.main_menu.addMenu("&File")
        self.file_menu.addAction(self.new_project_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.settings_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_action)

        edit_menu = self.main_menu.addMenu("&Edit")
        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)
        edit_menu.addAction(self.undo_view_action)

        # tools_menu = main_menu.addMenu("&Tools")

        self.windows_menu = self.main_menu.addMenu("&Windows")
        self.windows_menu.addAction(self.tile_windows_action)
        self.windows_menu.addAction(self.reset_windows_action)
        self.windows_menu.addAction(self.save_default_windows_action)
        self.windows_menu.setEnabled(False)
        self.disabled_elements.append(self.windows_menu)

        terminal_menu = self.main_menu.addMenu("&Terminal")
        terminal_menu.addAction(self.clear_terminal_action)

        help_menu = self.main_menu.addMenu("&Help")
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

        self.toolbar.addAction(self.new_project_action)
        self.toolbar.addAction(self.open_project_action)
        self.toolbar.addAction(self.save_project_action)
        self.toolbar.addAction(self.undo_action)
        self.toolbar.addAction(self.redo_action)
        self.toolbar.addAction(self.export_plots_action)
        self.toolbar.addAction(self.settings_action)
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
        self.controls_widget.setup_controls()

        for title, widget in reversed(widgets.items()):
            widget.setWindowTitle(title)
            window = self.mdi.addSubWindow(
                widget, QtCore.Qt.WindowType.WindowMinMaxButtonsHint | QtCore.Qt.WindowType.WindowTitleHint
            )
            window.setWindowTitle(title)
        self.reset_mdi_layout()
        self.startup_dlg = self.takeCentralWidget()
        self.setCentralWidget(self.mdi)

    def reset_mdi_layout(self):
        """Reset MDI layout to the default."""
        if self.settings.mdi_defaults is None:
            for window in self.mdi.subWindowList():
                window.showNormal()
            self.mdi.tileSubWindows()
        else:
            for window in self.mdi.subWindowList():
                # get corresponding MDIGeometries entry for the widget
                widget_name = window.windowTitle().lower().split(" ")[-1]
                x, y, width, height, minimized = getattr(self.settings.mdi_defaults, widget_name)
                if minimized:
                    window.showMinimized()
                else:
                    window.showNormal()

                window.setGeometry(x, y, width, height)

    def save_mdi_layout(self):
        """Set current MDI geometries as the default."""
        geoms = {}
        for window in self.mdi.subWindowList():
            # get corresponding MDIGeometries entry for the widget
            widget_name = window.windowTitle().lower().split(" ")[-1]
            geom = window.geometry()
            geoms[widget_name] = (geom.x(), geom.y(), geom.width(), geom.height(), window.isMinimized())

        self.settings.mdi_defaults = MDIGeometries.model_validate(geoms)

    def init_settings_and_log(self, save_path: str):
        """Initialise settings and logging for the project.

        Parameters
        ----------
        save_path : str
            The save path for the project.

        """
        self.save_path = save_path
        proj_path = pathlib.Path(save_path)
        self.settings = setup_settings(proj_path)
        log_path = pathlib.Path(self.settings.log_path)
        if not log_path.is_absolute():
            log_path = proj_path / log_path

        log_path.parents[0].mkdir(parents=True, exist_ok=True)
        self.logging = setup_logging(log_path, self.terminal_widget, level=self.settings.log_level)

    def enable_elements(self):
        """Enable the elements that are disabled on startup."""
        for element in self.disabled_elements:
            element.setEnabled(True)
        self.disabled_elements = []

    def handle_results(self, results):
        """Handle the results of a RAT run."""
        self.reset_widgets()
        self.controls_widget.chi_squared.setText(f"{results.calculationResults.sumChi:.6g}")

    def reset_widgets(self):
        """Reset widgets after a run."""
        self.controls_widget.run_button.setChecked(False)
