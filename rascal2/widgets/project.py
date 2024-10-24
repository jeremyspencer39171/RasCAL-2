from PyQt6 import QtCore, QtGui, QtWidgets
from RATapi.utils.enums import Calculations, Geometries, LayerModels

from rascal2.config import path_for


class ProjectWidget(QtWidgets.QWidget):
    """
    The Project MDI Widget
    """

    def __init__(self, parent):
        """
        Initialize widget.

        Parameters
        ----------
        parent: MainWindowView
                An instance of the MainWindowView
        """
        super().__init__(parent)
        self.parent = parent
        self.presenter = self.parent.presenter
        self.model = self.parent.presenter.model

        self.presenter.model.project_updated.connect(self.update_project_view)

        self.create_project_view()
        self.create_edit_view()

        self.stacked_widget = QtWidgets.QStackedWidget()
        self.stacked_widget.addWidget(self.project_widget)
        self.stacked_widget.addWidget(self.edit_project_widget)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

    def update_project_view(self) -> None:
        """Updates the project view."""
        self.modified_project = self.presenter.model.project.model_copy(deep=True)

        self.calculation_type.setText(self.model.project.calculation)
        self.model_type.setText(self.model.project.model)
        self.geometry_type.setText(self.model.project.geometry)

        self.calculation_combobox.setCurrentText(self.model.project.calculation)
        self.model_combobox.setCurrentText(self.model.project.model)
        self.geometry_combobox.setCurrentText(self.model.project.geometry)

        self.handle_domains_tab()

    def create_project_view(self) -> None:
        """Creates the project (non-edit) veiw"""
        self.project_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QGridLayout()
        main_layout.setVerticalSpacing(20)

        self.edit_project_button = QtWidgets.QPushButton(
            " Edit Project", self, objectName="bluebutton", icon=QtGui.QIcon(path_for("edit.png"))
        )
        self.edit_project_button.clicked.connect(self.show_edit_view)
        main_layout.addWidget(self.edit_project_button, 0, 5)

        self.calculation_label = QtWidgets.QLabel("Calculation:", self, objectName="boldlabel")

        self.calculation_type = QtWidgets.QLineEdit(self)
        self.calculation_type.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.calculation_type.setReadOnly(True)

        main_layout.addWidget(self.calculation_label, 1, 0, 1, 1)
        main_layout.addWidget(self.calculation_type, 1, 1, 1, 1)

        self.model_type_label = QtWidgets.QLabel("Model Type:", self, objectName="boldlabel")

        self.model_type = QtWidgets.QLineEdit(self)
        self.model_type.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.model_type.setReadOnly(True)

        main_layout.addWidget(self.model_type_label, 1, 2, 1, 1)
        main_layout.addWidget(self.model_type, 1, 3, 1, 1)

        self.geometry_label = QtWidgets.QLabel("Geometry:", self, objectName="boldlabel")

        self.geometry_type = QtWidgets.QLineEdit(self)
        self.geometry_type.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.geometry_type.setReadOnly(True)

        main_layout.addWidget(self.geometry_label, 1, 4, 1, 1)
        main_layout.addWidget(self.geometry_type, 1, 5, 1, 1)

        self.project_tab = QtWidgets.QTabWidget()

        # Replace QtWidgets.QWidget() with methods to create
        # the tabs in project view.
        self.project_tab.addTab(QtWidgets.QWidget(), "Parameters")
        self.project_tab.addTab(QtWidgets.QWidget(), "Backgrounds")
        self.project_tab.addTab(QtWidgets.QWidget(), "Experimental Parameters")
        self.project_tab.addTab(QtWidgets.QWidget(), "Layers")
        self.project_tab.addTab(QtWidgets.QWidget(), "Data")
        self.project_tab.addTab(QtWidgets.QWidget(), "Contrasts")

        main_layout.addWidget(self.project_tab, 2, 0, 1, 6)
        self.project_widget.setLayout(main_layout)

    def create_edit_view(self) -> None:
        """Creates the project edit veiw"""

        self.edit_project_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setSpacing(20)

        self.save_project_button = QtWidgets.QPushButton(" Save Project", self, objectName="greybutton")
        self.save_project_button.setIcon(QtGui.QIcon(path_for("save-project.png")))
        self.save_project_button.clicked.connect(self.save_changes)

        self.cancel_button = QtWidgets.QPushButton(" Cancel", self, objectName="redbutton")
        self.cancel_button.setIcon(QtGui.QIcon(path_for("cancel-dark.png")))
        self.cancel_button.clicked.connect(self.cancel_changes)

        layout = QtWidgets.QHBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.save_project_button)
        layout.addWidget(self.cancel_button)
        main_layout.addLayout(layout)

        self.edit_calculation_label = QtWidgets.QLabel("Calculation:", self, objectName="boldlabel")

        self.calculation_combobox = QtWidgets.QComboBox(self)
        self.calculation_combobox.addItems([calc for calc in Calculations])

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.edit_calculation_label)
        layout.addWidget(self.calculation_combobox)

        self.edit_model_type_label = QtWidgets.QLabel("Model Type:", self, objectName="boldlabel")

        self.model_combobox = QtWidgets.QComboBox(self)
        self.model_combobox.addItems([model for model in LayerModels])

        layout.addWidget(self.edit_model_type_label)
        layout.addWidget(self.model_combobox)

        self.edit_geometry_label = QtWidgets.QLabel("Geometry:", self, objectName="boldlabel")

        self.geometry_combobox = QtWidgets.QComboBox(self)
        self.geometry_combobox.addItems([geo for geo in Geometries])

        self.calculation_combobox.currentTextChanged.connect(lambda s: self.process_combobox_update("calculation", s))
        self.model_combobox.currentTextChanged.connect(lambda s: self.process_combobox_update("model", s))
        self.geometry_combobox.currentTextChanged.connect(lambda s: self.process_combobox_update("geometry", s))

        layout.addWidget(self.edit_geometry_label)
        layout.addWidget(self.geometry_combobox)
        main_layout.addLayout(layout)

        self.edit_project_tab = QtWidgets.QTabWidget()

        # Replace QtWidgets.QWidget() with methods to create
        # the tabs in edit view.
        self.edit_project_tab.addTab(QtWidgets.QWidget(), "Parameters")
        self.edit_project_tab.addTab(QtWidgets.QWidget(), "Backgrounds")
        self.edit_project_tab.addTab(QtWidgets.QWidget(), "Experimental Parameters")
        self.edit_project_tab.addTab(QtWidgets.QWidget(), "Layers")
        self.edit_project_tab.addTab(QtWidgets.QWidget(), "Data")
        self.edit_project_tab.addTab(QtWidgets.QWidget(), "Contrasts")

        main_layout.addWidget(self.edit_project_tab)

        self.edit_project_widget.setLayout(main_layout)

    def process_combobox_update(self, attr_name: str, selected_value: str) -> None:
        """
        Updates the copy of the project.

        Parameters
        ----------
        attr_name: str
                The attr that needs to be updated.
        selected_value: str
                The new selected value from the combobox.
        """
        setattr(self.modified_project, attr_name, selected_value)

    def handle_domains_tab(self) -> None:
        """Displays or hides the domains tab"""
        domain_tab_ix = 6
        if (
            self.calculation_type.text() == Calculations.Domains
            and self.project_tab.tabText(domain_tab_ix) != "Domains"
            and self.edit_project_tab.tabText(domain_tab_ix) != "Domains"
        ):
            # Replace QtWidgets.QWidget() with methods to create
            # the domains tab in project and edit view.
            self.project_tab.insertTab(domain_tab_ix, QtWidgets.QWidget(), "Domains")
            self.edit_project_tab.insertTab(domain_tab_ix, QtWidgets.QWidget(), "Domains")
        elif self.calculation_type.text() != Calculations.Domains:
            self.project_tab.removeTab(domain_tab_ix)
            self.edit_project_tab.removeTab(domain_tab_ix)

    def show_project_view(self) -> None:
        """Show project view"""
        self.setWindowTitle("Project")
        self.stacked_widget.setCurrentIndex(0)

    def show_edit_view(self) -> None:
        """Show edit view"""
        self.setWindowTitle("Edit Project")
        self.stacked_widget.setCurrentIndex(1)

    def save_changes(self) -> None:
        """Save changes to the project."""
        self.presenter.edit_project(self.modified_project)
        self.show_project_view()

    def cancel_changes(self) -> None:
        """Cancel changes to the project."""
        self.update_project_view()
        self.show_project_view()
