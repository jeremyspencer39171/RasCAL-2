import pathlib
import platform
import sys

from PyQt6 import QtCore, QtWidgets

from rascal2.config import MATLAB_ARCH_FILE, MATLAB_HELPER


class MatlabSetupDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        """
        Dialog to adjust Matlab location settings.

        Parameters
        ----------
        parent : MainWindowView
            The view of the RasCAL-2 GUI
        """
        super().__init__(parent)
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(150)

        form_layout = QtWidgets.QGridLayout()
        form_layout.setVerticalSpacing(10)
        form_layout.setHorizontalSpacing(0)

        label_layout = QtWidgets.QHBoxLayout()
        label_layout.addWidget(QtWidgets.QLabel("Current Matlab Directory:"))
        label_layout.addStretch(1)
        self.matlab_path = QtWidgets.QLineEdit(self)
        self.matlab_path.setText(MATLAB_HELPER.get_matlab_path())
        self.matlab_path.setReadOnly(True)
        self.matlab_path.setPlaceholderText("Select MATLAB directory")
        self.matlab_path.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

        browse_button = QtWidgets.QPushButton("Browse", objectName="BrowseButton")
        browse_button.clicked.connect(self.open_folder_selector)
        form_layout.addWidget(self.matlab_path, 0, 0, 1, 4)
        form_layout.addWidget(browse_button, 0, 4, 1, 1)

        self.accept_button = QtWidgets.QPushButton("OK", self)
        self.accept_button.clicked.connect(self.accept)
        self.cancel_button = QtWidgets.QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.reject)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.accept_button)
        button_layout.addWidget(self.cancel_button)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(label_layout)
        main_layout.addLayout(form_layout)
        main_layout.addStretch(1)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self.setWindowTitle("Settings")
        self.changed = False

    def open_folder_selector(self) -> None:
        """Open folder selector."""
        folder_name = QtWidgets.QFileDialog.getExistingDirectory(self, "Select MATLAB Directory", ".")
        if folder_name:
            self.matlab_path.setText(folder_name)
            self.changed = True

    def set_matlab_paths(self):
        """Update MATLAB paths in arch file"""
        should_init = False
        with open(MATLAB_ARCH_FILE, "r+") as path_file:
            install_dir = pathlib.Path(self.matlab_path.text())
            if not getattr(sys, "frozen", False):
                return

            if len(path_file.readlines()) == 0:
                should_init = True

            path_file.truncate(0)

            arch = "win64" if platform.system() == "Windows" else "glnxa64"
            path_file.writelines(
                [
                    f"{arch}\n",
                    str(install_dir / f"bin/{arch}\n"),
                    str(install_dir / f"extern/engines/python/dist/matlab/engine/{arch}\n"),
                    str(install_dir / f"extern/bin/{arch}\n"),
                ]
            )
        if should_init:
            MATLAB_HELPER.async_start()

    def accept(self):
        if self.changed:
            self.set_matlab_paths()
        super().accept()
