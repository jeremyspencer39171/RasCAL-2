"""Models and widgets for project fields."""

from enum import Enum

import pydantic
import RATapi
from PyQt6 import QtCore, QtGui, QtWidgets
from RATapi.utils.enums import Procedures

from rascal2.config import path_for
from rascal2.widgets.delegates import ValidatedInputDelegate, ValueSpinBoxDelegate


class ClassListModel(QtCore.QAbstractTableModel):
    """Table model for a project ClassList field.

    Parameters
    ----------
    classlist : ClassList
        The initial classlist to represent in this model.
    field : str
        The name of the field represented by this model.
    parent : QtWidgets.QWidget
        The parent widget for the model.

    """

    def __init__(self, classlist: RATapi.ClassList, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.parent = parent
        self.classlist = classlist
        self.item_type = classlist._class_handle
        if not issubclass(self.item_type, pydantic.BaseModel):
            raise NotImplementedError("ClassListModel only works for classlists of Pydantic models!")
        self.headers = list(self.item_type.model_fields)
        self.edit_mode = False

    def rowCount(self, parent=None) -> int:
        return len(self.classlist)

    def columnCount(self, parent=None) -> int:
        return len(self.headers) + 1

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        param = self.index_header(index)

        if param is None:
            return None

        data = getattr(self.classlist[index.row()], param)

        if role == QtCore.Qt.ItemDataRole.DisplayRole and self.index_header(index) != "fit":
            data = getattr(self.classlist[index.row()], param)
            # pyqt can't automatically coerce enums to strings...
            if isinstance(data, Enum):
                return str(data)
            return data
        elif role == QtCore.Qt.ItemDataRole.CheckStateRole and self.index_header(index) == "fit":
            return QtCore.Qt.CheckState.Checked if data else QtCore.Qt.CheckState.Unchecked

    def setData(self, index, value, role=QtCore.Qt.ItemDataRole.EditRole) -> bool:
        if role == QtCore.Qt.ItemDataRole.EditRole or role == QtCore.Qt.ItemDataRole.CheckStateRole:
            row = index.row()
            param = self.index_header(index)
            if self.index_header(index) == "fit":
                value = QtCore.Qt.CheckState(value) == QtCore.Qt.CheckState.Checked
            if param is not None:
                try:
                    setattr(self.classlist[row], param, value)
                except pydantic.ValidationError:
                    return False
                if not self.edit_mode:
                    self.parent.update_project()
                return True
        return False

    def headerData(self, section, orientation, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if (
            orientation == QtCore.Qt.Orientation.Horizontal
            and role == QtCore.Qt.ItemDataRole.DisplayRole
            and section != 0
        ):
            return self.headers[section - 1].replace("_", " ").title()
        return None

    def append_item(self):
        """Append an item to the ClassList."""
        self.classlist.append(self.item_type())
        self.endResetModel()

    def delete_item(self, row: int):
        """Delete an item in the ClassList.

        Parameters
        ----------
        row : int
            The row containing the item to delete.

        """
        self.classlist.pop(row)
        self.endResetModel()

    def index_header(self, index):
        """Get the header for an index.

        Parameters:
        -----------
        index : QModelIndex
            The model index for the header.

        Returns
        -------
        str or None
            Either the name of the header, or None if none exists.

        """
        col = index.column()
        if col == 0:
            return None
        return self.headers[col - 1]


class ProjectFieldWidget(QtWidgets.QWidget):
    """Widget to show a project ClassList.

    Parameters
    ----------
    field : str
        The field of the project represented by this widget.
    parent : ProjectTabWidget
        The tab this field belongs to.

    """

    classlist_model = ClassListModel

    def __init__(self, field: str, parent):
        super().__init__(parent)
        self.field = field
        header = field.replace("_", " ").title()
        self.parent = parent
        self.table = QtWidgets.QTableView(parent)
        self.table.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.MinimumExpanding
        )

        layout = QtWidgets.QVBoxLayout()
        topbar = QtWidgets.QHBoxLayout()
        topbar.addWidget(QtWidgets.QLabel(header))
        # change to icon: remember to mention that plus.png in the icons is wonky
        self.add_button = QtWidgets.QPushButton(f"+ Add new {header[:-1] if header[-1] == 's' else header}")
        self.add_button.setHidden(True)
        self.add_button.pressed.connect(self.append_item)
        topbar.addWidget(self.add_button)

        layout.addLayout(topbar)
        layout.addWidget(self.table)
        self.setLayout(layout)

    def update_model(self, classlist):
        """Update the table model to synchronise with the project field."""
        self.model = self.classlist_model(classlist, self)

        self.table.setModel(self.model)
        self.table.hideColumn(0)
        self.set_item_delegates()
        header = self.table.horizontalHeader()

        header.setSectionResizeMode(self.model.headers.index("name") + 1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

    def set_item_delegates(self):
        """Set item delegates and open persistent editors for the table."""
        for i, header in enumerate(self.model.headers):
            self.table.setItemDelegateForColumn(
                i + 1, ValidatedInputDelegate(self.model.item_type.model_fields[header], self.table)
            )

    def append_item(self):
        """Append an item to the model if the model exists."""
        if self.model is not None:
            self.model.append_item()

        # call edit again to recreate delete buttons
        self.edit()

    def delete_item(self, index):
        """Delete an item at the index if the model exists.

        Parameters
        ----------
        index : int
            The row to be deleted.

        """
        if self.model is not None:
            self.model.delete_item(index)

        # call edit again to recreate delete buttons
        self.edit()

    def edit(self):
        """Change the widget to be in edit mode."""
        self.model.edit_mode = True
        self.add_button.setHidden(False)
        self.table.showColumn(0)
        self.set_item_delegates()
        for i in range(0, self.model.rowCount()):
            self.table.setIndexWidget(self.model.index(i, 0), self.make_delete_button(i))

    def make_delete_button(self, index):
        """Make a button that deletes index `index` from the list."""
        button = QtWidgets.QPushButton(icon=QtGui.QIcon(path_for("delete.png")))
        button.resize(button.sizeHint().width(), button.sizeHint().width())
        button.pressed.connect(lambda: self.delete_item(index))

        return button

    def update_project(self):
        """Update the field in the parent Project."""
        presenter = self.parent.parent.parent.presenter
        presenter.edit_project({self.field: self.model.classlist})


class ParametersModel(ClassListModel):
    """Classlist model for Parameters."""

    def __init__(self, classlist: RATapi.ClassList, parent: QtWidgets.QWidget):
        super().__init__(classlist, parent)
        self.headers.insert(0, self.headers.pop(self.headers.index("fit")))

        self.protected_indices = []
        if self.item_type is RATapi.models.Parameter:
            for i, item in enumerate(classlist):
                if isinstance(item, RATapi.models.ProtectedParameter):
                    self.protected_indices.append(i)

    def flags(self, index):
        flags = super().flags(index)
        header = self.index_header(index)
        # disable editing on the delete widget column
        # and disable mu, sigma if prior type is not Gaussian
        if (index.column() == 0) or (
            self.classlist[index.row()].prior_type != "gaussian" and header in ["mu", "sigma"]
        ):
            return QtCore.Qt.ItemFlag.NoItemFlags
        # never allow name editing for protected parameters, allow everything else to be edited by default
        if header == "fit":
            flags |= QtCore.Qt.ItemFlag.ItemIsUserCheckable
        elif header != "name" or (self.edit_mode and index.row() not in self.protected_indices):
            flags |= QtCore.Qt.ItemFlag.ItemIsEditable

        return flags


class ParameterFieldWidget(ProjectFieldWidget):
    """Subclass of field widgets for parameters."""

    classlist_model = ParametersModel

    def set_item_delegates(self):
        for i, header in enumerate(self.model.headers):
            if header in ["min", "value", "max"]:
                self.table.setItemDelegateForColumn(i + 1, ValueSpinBoxDelegate(header, self.table))
            else:
                self.table.setItemDelegateForColumn(
                    i + 1, ValidatedInputDelegate(self.model.item_type.model_fields[header], self.table)
                )

    def update_model(self, classlist):
        super().update_model(classlist)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(
            self.model.headers.index("fit") + 1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )

    def handle_bayesian_columns(self, procedure: Procedures):
        """Hide or show Bayes-related columns based on procedure.

        Parameters
        ----------
        procedure : Procedure
            The procedure in Controls.
        """
        is_bayesian = procedure in ["ns", "dream"]
        bayesian_columns = ["prior_type", "mu", "sigma"]
        for item in bayesian_columns:
            index = self.model.headers.index(item)
            if is_bayesian:
                self.table.showColumn(index + 1)
            else:
                self.table.hideColumn(index + 1)

    def edit(self):
        super().edit()
        for i in range(0, self.model.rowCount()):
            if i in self.model.protected_indices:
                self.table.setIndexWidget(self.model.index(i, 0), None)
