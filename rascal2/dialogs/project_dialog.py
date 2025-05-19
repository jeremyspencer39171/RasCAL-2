import os
from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets

from rascal2.config import path_for
from rascal2.core.settings import update_recent_projects

# global variable for required project files
PROJECT_FILES = ["controls.json", "project.json"]


class StartupDialog(QtWidgets.QDialog):
    """Base class for startup dialogs."""

    _button_style = """background-color: {};
                       color: #F2F1E8;
                       padding-top: 0.3em;
                       padding-left: 1em;
                       padding-right: 1em;
                       padding-bottom: 0.3em;
                       font-weight: bold;
                       border-radius: 0.5em"""
    _label_style = "font-weight: bold"
    _error_style = "color: #E34234"
    _line_edit_error_style = "border: 1px solid #E34234"
    folder_selector = QtWidgets.QFileDialog.getExistingDirectory

    def __init__(self, parent):
        """
        Initialize dialog.

        Parameters
        ----------
        parent: MainWindowView
                An instance of the MainWindowView
        """
        super().__init__(parent)

        self.setModal(True)
        self.setMinimumWidth(700)

        self.folder_path = ""

        self.compose_layout()

    def compose_layout(self):
        """Add widgets and layouts to the dialog's main layout."""
        main_layout = QtWidgets.QVBoxLayout()

        main_layout.setSpacing(20)

        widgets = self.create_form()
        for item in widgets:
            if isinstance(item, QtWidgets.QWidget):
                main_layout.addWidget(item)
            elif isinstance(item, QtWidgets.QLayout):
                main_layout.addLayout(item)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        buttons = self.create_buttons()
        for button in buttons:
            button_layout.addWidget(button)
        main_layout.addStretch(1)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def create_buttons(self) -> list[QtWidgets.QWidget]:
        """Create buttons for the bottom of the dialog.

        This is kept as a separate method so that it can be reimplemented by subclasses.

        Returns
        -------
        list[QtWidgets.QWidget]
            A list of the widgets to be added to the bottom of the dialog, from left to right.
        """
        cancel_button = QtWidgets.QPushButton(" Cancel", self)
        cancel_button.setIcon(QtGui.QIcon(path_for("cancel-light.png")))
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet(self._button_style.format("#E34234"))

        return [cancel_button]

    def create_form(self) -> list[QtWidgets.QWidget | QtWidgets.QLayout]:
        """Create the widgets and layout for the dialog form.

        This is kept as a separate method so that it can be reimplemented by subclasses.

        Returns
        -------
        list[QtWidgets.QWidget, QtWidgets.QLayout]
            A list of widgets and layouts to add to the form, ordered top to bottom.

        """
        self.project_folder_label = QtWidgets.QLabel("Project Folder:", self)
        self.project_folder_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.project_folder_label.setStyleSheet(self._label_style)

        self.project_folder = QtWidgets.QLineEdit(self)
        self.project_folder.setReadOnly(True)
        self.project_folder.setPlaceholderText("Select project folder")

        browse_button = QtWidgets.QPushButton(" Browse", self)
        browse_button.setIcon(QtGui.QIcon(path_for("browse-light.png")))
        browse_button.clicked.connect(self.open_folder_selector)
        browse_button.setStyleSheet(self._button_style.format("#403F3F"))

        self.project_folder_error = QtWidgets.QLabel("", self)
        self.project_folder_error.setStyleSheet(self._error_style)
        self.project_folder_error.hide()

        project_folder_layout = QtWidgets.QGridLayout()
        project_folder_layout.setVerticalSpacing(2)
        project_folder_layout.addWidget(self.project_folder_label, 0, 0, 1, 1)
        project_folder_layout.addWidget(self.project_folder, 0, 1, 1, 4)
        project_folder_layout.addWidget(browse_button, 0, 5, 1, 1)
        project_folder_layout.addWidget(self.project_folder_error, 1, 1, 1, 4)

        return [project_folder_layout]

    def open_folder_selector(self) -> None:
        """
        Open folder selector.
        """
        folder_path = self.folder_selector(self, "Select Folder")
        if folder_path:
            try:
                self.verify_folder(folder_path)
            except ValueError as err:
                self.set_folder_error(str(err))
                self.project_folder.setText("")
            else:
                self.set_folder_error("")
                self.project_folder.setText(folder_path)

    def set_folder_error(self, msg: str):
        """Show or remove an error on the project folder dialog.

        Parameters
        ----------
        msg : str
            The message to show as the error. If blank, will remove the error.

        """
        if msg:
            self.project_folder.setStyleSheet(self._line_edit_error_style)
            self.project_folder_error.show()
            self.project_folder_error.setText(msg)
        else:
            self.project_folder.setStyleSheet("")
            self.project_folder_error.hide()

    @staticmethod
    def verify_folder(folder_path: str):
        """Verify that the path is valid for the current dialog, and raise an error otherwise.

        This is an empty method to be reimplemented by subclasses.

        Raises
        ------
        ValueError
            If the folder path is not valid for the current operation.

        """
        pass


class NewProjectDialog(StartupDialog):
    """The dialog to create a new project."""

    def create_form(self) -> list[QtWidgets.QWidget | QtWidgets.QLayout]:
        self.setWindowTitle("New Project")

        # Project name widgets
        self.project_name_label = QtWidgets.QLabel("Project Name:", self)
        self.project_name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.project_name_label.setStyleSheet(self._label_style)

        self.project_name = QtWidgets.QLineEdit(self)
        self.project_name.setPlaceholderText("Enter project name")
        self.project_name.textChanged.connect(self.verify_name)

        self.project_name_error = QtWidgets.QLabel("Project name needs to be specified.", self)
        self.project_name_error.setStyleSheet(self._error_style)
        self.project_name_error.hide()

        project_name_layout = QtWidgets.QGridLayout()
        project_name_layout.setVerticalSpacing(2)
        project_name_layout.addWidget(self.project_name_label, 0, 0, 1, 1)
        project_name_layout.addWidget(self.project_name, 0, 1, 1, 5)
        project_name_layout.addWidget(self.project_name_error, 1, 1, 1, 5)

        return [project_name_layout] + super().create_form()

    def create_buttons(self) -> list[QtWidgets.QWidget]:
        create_button = QtWidgets.QPushButton(" Create", self)
        create_button.setIcon(QtGui.QIcon(path_for("create.png")))
        create_button.clicked.connect(self.create_project)
        create_button.setStyleSheet(self._button_style.format("#0D69BB"))

        return [create_button] + super().create_buttons()

    @staticmethod
    def verify_folder(folder_path: str) -> None:
        if not os.access(folder_path, os.W_OK) and os.access(folder_path, os.R_OK):
            raise ValueError("You do not have permission to access this folder.")
        if any(Path(folder_path, file).exists() for file in PROJECT_FILES):
            raise ValueError("Folder already contains a project.")

    def verify_name(self) -> None:
        if self.project_name.text() == "":
            self.project_name.setStyleSheet(self._line_edit_error_style)
            self.project_name_error.show()
        else:
            self.project_name.setStyleSheet("")
            self.project_name_error.hide()

    def create_project(self) -> None:
        """Create project if inputs are valid."""
        self.verify_name()
        if self.project_folder.text() == "":
            self.set_folder_error("Please specify a project folder.")
        if self.project_name_error.isHidden() and self.project_folder_error.isHidden():
            self.parent().presenter.create_project(self.project_name.text(), self.project_folder.text())
            self.accept()


class LoadDialog(StartupDialog):
    """Dialog to load an existing project."""

    def create_form(self) -> list[QtWidgets.QWidget | QtWidgets.QLayout]:
        self.setWindowTitle("Load Project")

        recent_projects = update_recent_projects()
        recent_projects = recent_projects[:3]

        if not recent_projects:
            return super().create_form()

        recent_projects_layout = QtWidgets.QVBoxLayout()
        recent_projects_title = QtWidgets.QLabel("Recent projects:")
        recent_projects_title.setStyleSheet(self._label_style)
        recent_projects_layout.addWidget(recent_projects_title)

        for project in recent_projects:
            button = QtWidgets.QPushButton(f"  {project}")
            button.setStyleSheet(
                """
            font: bold italic underline;
            text-align: left;
            """
                + self._button_style.format("#403F3F")
            )
            button.pressed.connect(self.load_recent_project(project))
            recent_projects_layout.addWidget(button)

        return super().create_form() + [recent_projects_layout]

    def load_recent_project(self, path: str):
        # use internal function so we can use it as a parameter-free slot
        def _load():
            self.project_folder_error.hide()
            self.project_folder.setText(path)
            self.load_project()

        return _load

    def create_buttons(self) -> list[QtWidgets.QWidget]:
        load_button = QtWidgets.QPushButton(" Load", self)
        load_button.setIcon(QtGui.QIcon(path_for("load-light.png")))
        load_button.clicked.connect(self.load_project)
        load_button.setStyleSheet(self._button_style.format("#0D69BB"))

        return [load_button] + super().create_buttons()

    @staticmethod
    def verify_folder(folder_path: str):
        if not os.access(folder_path, os.W_OK) and os.access(folder_path, os.R_OK):
            raise ValueError("You do not have permission to access this folder.")
        if not all(Path(folder_path, file).exists() for file in PROJECT_FILES):
            raise ValueError("No project found in this folder.")

    def load_project(self):
        """Load the project if inputs are valid."""
        if self.project_folder.text() == "":
            self.set_folder_error("Please specify a project folder.")
        if self.project_folder_error.isHidden():
            try:
                self.parent().presenter.load_project(self.project_folder.text())
            except ValueError as err:
                self.set_folder_error(str(err))
            else:
                if not self.parent().toolbar.isEnabled():
                    self.parent().toolbar.setEnabled(True)
                self.accept()


class LoadR1Dialog(StartupDialog):
    """Dialog to load a RasCAL-1 project."""

    def __init__(self, parent):
        # our 'folder selector' is actually a .mat file selector in this case
        self.folder_selector = lambda p, _: QtWidgets.QFileDialog.getOpenFileName(
            p, "Select RasCAL-1 File", filter="*.mat"
        )[0]
        super().__init__(parent)

    def create_form(self):
        self.setWindowTitle("Load RasCAL-1 Project")

        form = super().create_form()
        self.project_folder_label.setText("RasCAL-1 file:")
        self.project_folder.setPlaceholderText("Select RasCAL-1 file")

        return form

    def create_buttons(self):
        load_button = QtWidgets.QPushButton(" Load", self)
        load_button.setIcon(QtGui.QIcon(path_for("load-light.png")))
        load_button.clicked.connect(self.load_project)
        load_button.setStyleSheet(self._button_style.format("#0D69BB"))

        return [load_button] + super().create_buttons()

    @staticmethod
    def verify_folder(file_path: str):
        if not os.access(file_path, os.R_OK):
            raise ValueError("You do not have permission to read this RasCAL-1 project.")
        if not os.access(Path(file_path).parent, os.W_OK):
            raise ValueError("You do not have permission to create a project in this folder.")

    def load_project(self):
        """Load the project if inputs are valid."""
        if self.project_folder.text() == "":
            self.set_folder_error("Please specify a project file.")
        if self.project_folder_error.isHidden():
            self.parent().presenter.load_r1_project(self.project_folder.text())
            if not self.parent().toolbar.isEnabled():
                self.parent().toolbar.setEnabled(True)
            self.accept()
