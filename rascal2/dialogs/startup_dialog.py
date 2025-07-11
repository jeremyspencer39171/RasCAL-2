import os
from pathlib import Path

from PyQt6 import QtCore, QtWidgets

from rascal2.settings import update_recent_projects

# global variable for required project files
PROJECT_FILES = ["controls.json", "project.json"]


class StartupDialog(QtWidgets.QDialog):
    """Base class for startup dialogs."""

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

        form_layout = QtWidgets.QGridLayout()
        form_layout.setVerticalSpacing(10)
        form_layout.setHorizontalSpacing(0)
        main_layout.addLayout(form_layout)
        self.create_form(form_layout)

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
        self.cancel_button = QtWidgets.QPushButton("Cancel", objectName="CancelButton")
        self.cancel_button.clicked.connect(self.reject)

        return [self.cancel_button]

    def create_form(self, form_layout):
        """Create the widgets and layout for the dialog form.

        This is kept as a separate method so that it can be reimplemented by subclasses.

        Parameters
        ----------
        form_layout : QtWidgets.QGridLayout
            A layout to add the form to.
        """
        self.project_folder_label = QtWidgets.QLabel("Project Folder:")
        self.project_folder_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

        self.project_folder = QtWidgets.QLineEdit(self)
        self.project_folder.setReadOnly(True)
        self.project_folder.setPlaceholderText("Select project folder")
        self.project_folder.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

        browse_button = QtWidgets.QPushButton("Browse", objectName="BrowseButton")
        browse_button.clicked.connect(self.open_folder_selector)

        self.project_folder_error = QtWidgets.QLabel("", objectName="ErrorLabel")
        self.project_folder_error.hide()

        num_rows = form_layout.rowCount()
        form_layout.addWidget(self.project_folder_label, num_rows, 0, 1, 1, QtCore.Qt.AlignmentFlag.AlignVCenter)
        form_layout.addWidget(self.project_folder, num_rows, 1, 1, 4)
        form_layout.addWidget(browse_button, num_rows, 5, 1, 1)
        form_layout.addWidget(self.project_folder_error, num_rows + 1, 1, 1, 4)

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
            self.project_folder_error.show()
            self.project_folder_error.setText(msg)
            self.project_folder.setProperty("error", True)
        else:
            self.project_folder_error.hide()
            self.project_folder.setProperty("error", False)
        self.project_folder.style().unpolish(self.project_folder)
        self.project_folder.style().polish(self.project_folder)

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

    def showEvent(self, event):
        super().showEvent(event)
        self.cancel_button.setFocus()


class NewProjectDialog(StartupDialog):
    """The dialog to create a new project."""

    def create_form(self, form_layout):
        self.setWindowTitle("New Project")

        # Project name widgets
        self.project_name_label = QtWidgets.QLabel("Project Name:")
        self.project_name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

        self.project_name = QtWidgets.QLineEdit(self)
        self.project_name.setPlaceholderText("Enter project name")
        self.project_name.textChanged.connect(self.verify_name)

        self.project_name_error = QtWidgets.QLabel("Project name needs to be specified.", objectName="ErrorLabel")
        self.project_name_error.hide()

        num_rows = form_layout.rowCount()
        form_layout.addWidget(self.project_name_label, num_rows, 0, 1, 1)
        form_layout.addWidget(self.project_name, num_rows, 1, 1, 5)
        form_layout.addWidget(self.project_name_error, num_rows + 1, 1, 1, 5)
        super().create_form(form_layout)

    def create_buttons(self) -> list[QtWidgets.QWidget]:
        create_button = QtWidgets.QPushButton("Create", objectName="CreateButton")
        create_button.clicked.connect(self.create_project)

        return [create_button] + super().create_buttons()

    @staticmethod
    def verify_folder(folder_path: str) -> None:
        if not os.access(folder_path, os.W_OK) and os.access(folder_path, os.R_OK):
            raise ValueError("You do not have permission to access this folder.")
        if any(Path(folder_path, file).exists() for file in PROJECT_FILES):
            raise ValueError("Folder already contains a project.")

    def verify_name(self) -> None:
        if self.project_name.text() == "":
            self.project_name_error.show()
            self.project_name.setProperty("error", True)
        else:
            self.project_name_error.hide()
            self.project_name.setProperty("error", False)
        self.project_name.style().unpolish(self.project_name)
        self.project_name.style().polish(self.project_name)

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

    def create_form(self, form_layout):
        self.setWindowTitle("Load Project")

        recent_projects = update_recent_projects()
        recent_projects = recent_projects[:3]

        super().create_form(form_layout)

        if recent_projects:
            recent_projects_layout = QtWidgets.QVBoxLayout()
            recent_projects_title = QtWidgets.QLabel("Recent projects:")

            for project in recent_projects:
                button = QtWidgets.QPushButton(f"{project}", objectName="PreviousProjectButton")

                button.pressed.connect(self.load_recent_project(project))
                recent_projects_layout.addWidget(button)

            num_rows = form_layout.rowCount()
            form_layout.addWidget(recent_projects_title, num_rows, 0, 1, 1, QtCore.Qt.AlignmentFlag.AlignTop)
            form_layout.addLayout(recent_projects_layout, num_rows, 1, 1, -1)

    def load_recent_project(self, path: str):
        # use internal function so we can use it as a parameter-free slot
        def _load():
            self.project_folder_error.hide()
            self.project_folder.setText(path)
            self.load_project()

        return _load

    def create_buttons(self) -> list[QtWidgets.QWidget]:
        load_button = QtWidgets.QPushButton("Load", objectName="LoadButton")
        load_button.clicked.connect(self.load_project)

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

    def create_form(self, form_layout):
        self.setWindowTitle("Load RasCAL-1 Project")

        super().create_form(form_layout)
        self.project_folder_label.setText("RasCAL-1 file:")
        self.project_folder.setPlaceholderText("Select RasCAL-1 file")

    def create_buttons(self):
        load_button = QtWidgets.QPushButton("Load", objectName="LoadButton")
        load_button.clicked.connect(self.load_project)

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
