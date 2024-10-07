from PyQt6 import QtCore, QtGui, QtWidgets

from rascal2.config import path_for
from rascal2.dialogs.project_dialog import LoadDialog, LoadR1Dialog, NewProjectDialog


class StartUpWidget(QtWidgets.QWidget):
    """
    The Start Up widget
    """

    _button_style = """background-color: #0D69BB;
                       icon-size: 4em;
                       border-radius : 0.5em;
                       padding: 0.5em;
                       margin-left: 5em;
                       margin-right: 5em;"""

    _label_style = "font-weight: bold; font-size: 1em;"

    def __init__(self, parent):
        """
        Initialize widget.

        Parameters
        ----------
        parent: MainWindowView
                An instance of the MainWindowView
        """
        super().__init__(parent)

        self.create_banner_and_footer()
        self.create_buttons()
        self.create_labels()

        self.add_widgets_to_layout()

    def add_widgets_to_layout(self) -> None:
        """
        Add widgets to layout.
        """
        startup_layout = QtWidgets.QVBoxLayout()

        startup_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        startup_layout.setSpacing(50)

        # Add banner
        startup_layout.addStretch(1)
        startup_layout.addWidget(self.banner_label)

        # Add buttons and labels
        for widget in ["button", "label"]:
            layout = QtWidgets.QHBoxLayout()
            for name in ["new_project_", "import_project_", "import_r1_"]:
                layout.addWidget(getattr(self, name + widget))
            startup_layout.addLayout(layout)

        # Add footer
        startup_layout.addWidget(self.footer_label)
        startup_layout.addStretch(1)

        self.setLayout(startup_layout)

    def create_banner_and_footer(self) -> None:
        """
        Create banner and footer.
        """
        self.banner_label = QtWidgets.QLabel(self)
        self.banner_label.setPixmap(QtGui.QPixmap(path_for("banner.png")))
        self.banner_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.footer_label = QtWidgets.QLabel(self)
        self.footer_label.setPixmap(QtGui.QPixmap(path_for("footer.png")))
        self.footer_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

    def create_buttons(self) -> None:
        """
        Create buttons.
        """
        self.new_project_button = QtWidgets.QPushButton(self)
        self.new_project_button.setIcon(QtGui.QIcon(path_for("create.png")))
        self.new_project_button.clicked.connect(lambda: self.parent().show_project_dialog(NewProjectDialog))
        self.new_project_button.setStyleSheet(self._button_style)

        self.import_project_button = QtWidgets.QPushButton(self)
        self.import_project_button.setIcon(QtGui.QIcon(path_for("browse-light.png")))
        self.import_project_button.clicked.connect(lambda: self.parent().show_project_dialog(LoadDialog))
        self.import_project_button.setStyleSheet(self._button_style)

        self.import_r1_button = QtWidgets.QPushButton(self)
        self.import_r1_button.setIcon(QtGui.QIcon(path_for("import-r1.png")))
        self.import_r1_button.clicked.connect(lambda: self.parent().show_project_dialog(LoadR1Dialog))
        self.import_r1_button.setStyleSheet(self._button_style)

    def create_labels(self) -> None:
        """
        Create labels.
        """
        self.new_project_label = QtWidgets.QLabel("New\nProject", self)
        self.new_project_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.new_project_label.setStyleSheet(self._label_style)

        self.import_project_label = QtWidgets.QLabel("Import Existing\nProject", self)
        self.import_project_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.import_project_label.setStyleSheet(self._label_style)

        self.import_r1_label = QtWidgets.QLabel("Import RasCAL-1\nProject", self)
        self.import_r1_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.import_r1_label.setStyleSheet(self._label_style)
