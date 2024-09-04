import os

from PyQt6 import QtCore, QtGui, QtWidgets

from rascal2.config import path_for


class ProjectDialog(QtWidgets.QDialog):
    """
    The Project dialog
    """

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

        self.create_buttons()
        self.create_form()
        self.add_widgets_to_layout()

    def add_widgets_to_layout(self) -> None:
        """
        Add widgets to the layout.
        """
        self.main_layout = QtWidgets.QVBoxLayout()

        self.main_layout.setSpacing(20)

        # Add project name widgets
        layout = QtWidgets.QGridLayout()
        layout.setVerticalSpacing(2)
        layout.addWidget(self.project_name_label, 0, 0, 1, 1)
        layout.addWidget(self.project_name, 0, 1, 1, 5)
        layout.addWidget(self.project_name_error, 1, 1, 1, 5)
        self.main_layout.addLayout(layout)

        # Add project folder widgets
        layout = QtWidgets.QGridLayout()
        layout.setVerticalSpacing(2)
        layout.addWidget(self.project_folder_label, 0, 0, 1, 1)
        layout.addWidget(self.project_folder, 0, 1, 1, 4)
        layout.addWidget(self.browse_button, 0, 5, 1, 1)
        layout.addWidget(self.project_folder_error, 1, 1, 1, 4)
        self.main_layout.addLayout(layout)

        # Add the create and cancel buttons
        layout = QtWidgets.QHBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.create_button)
        layout.addWidget(self.cancel_button)
        self.main_layout.addStretch(1)
        self.main_layout.addLayout(layout)

        self.setLayout(self.main_layout)

    def create_form(self) -> None:
        """
        Create form widgets.
        """
        # Project name widgets
        self.project_name_label = QtWidgets.QLabel("Project Name:", self)
        self.project_name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.project_name_label.setStyleSheet(self._label_style)

        self.project_name = QtWidgets.QLineEdit(self)
        self.project_name.setPlaceholderText("Enter project name")

        self.project_name_error = QtWidgets.QLabel("Project name needs to be specified.", self)
        self.project_name_error.setStyleSheet(self._error_style)
        self.project_name_error.hide()

        # Project folder widgets
        self.project_folder_label = QtWidgets.QLabel("Project Folder:", self)
        self.project_folder_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.project_folder_label.setStyleSheet(self._label_style)

        self.project_folder = QtWidgets.QLineEdit(self)
        self.project_folder.setReadOnly(True)
        self.project_folder.setPlaceholderText("Select project folder")

        self.project_folder_error = QtWidgets.QLabel("An empty project folder needs to be selected.", self)
        self.project_folder_error.setStyleSheet(self._error_style)
        self.project_folder_error.hide()

    def create_buttons(self) -> None:
        """
        Create buttons.
        """
        self.browse_button = QtWidgets.QPushButton(" Browse", self)
        self.browse_button.setIcon(QtGui.QIcon(path_for("browse-light.png")))
        self.browse_button.clicked.connect(self.open_folder_selector)
        self.browse_button.setStyleSheet(self._button_style.format("#403F3F"))

        self.create_button = QtWidgets.QPushButton(" Create", self)
        self.create_button.setIcon(QtGui.QIcon(path_for("create.png")))
        self.create_button.clicked.connect(self.create_project)
        self.create_button.setStyleSheet(self._button_style.format("#0D69BB"))

        self.cancel_button = QtWidgets.QPushButton(" Cancel", self)
        self.cancel_button.setIcon(QtGui.QIcon(path_for("cancel.png")))
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet(self._button_style.format("#E34234"))

    def open_folder_selector(self) -> None:
        """
        Open folder selector.
        """
        self.folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
        if self.folder_path:
            self.verify_folder()

    def verify_folder(self) -> None:
        """
        Verify the project folder.
        """
        error = False
        if self.folder_path:
            files_in_folder = [file for file in os.listdir(self.folder_path) if not file.startswith(".")]
            if files_in_folder:
                error = True
        elif self.project_folder.text() == "":
            error = True

        if error:
            self.project_folder.setStyleSheet(self._line_edit_error_style)
            self.project_folder_error.show()
            self.project_folder.setText("")
        else:
            self.project_folder.setStyleSheet("")
            self.project_folder_error.hide()
            self.project_folder.setText(self.folder_path)

    def verify_name(self) -> None:
        """
        Verify the project name.
        """
        if self.project_name.text() == "":
            self.project_name.setStyleSheet(self._line_edit_error_style)
            self.project_name_error.show()
        else:
            self.project_name.setStyleSheet("")
            self.project_name_error.hide()

    def create_project(self) -> None:
        """
        Create project if inputs verified.
        """
        self.verify_name()
        self.verify_folder()
        if self.project_name_error.isHidden() and self.project_folder_error.isHidden():
            self.parent().presenter.create_project(self.project_name.text(), self.project_folder.text())
            if not self.parent().toolbar.isEnabled():
                self.parent().toolbar.setEnabled(True)
            self.accept()
