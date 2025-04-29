"""Models and widgets for project fields."""

import contextlib
import re
from enum import Enum
from pathlib import Path

import pydantic
import RATapi
from PyQt6 import QtCore, QtGui, QtWidgets
from RATapi.utils.enums import Languages, Procedures, TypeOptions

import rascal2.widgets.delegates as delegates
from rascal2.config import path_for
from rascal2.dialogs.custom_file_editor import edit_file, edit_file_matlab


class ClassListTableModel(QtCore.QAbstractTableModel):
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

        self.classlist: RATapi.ClassList
        self.item_type: type
        self.headers: list[str]

        self.setup_classlist(classlist)
        self.edit_mode = False

    def setup_classlist(self, classlist: RATapi.ClassList):
        """Setup the ClassList, type and headers for the model."""
        self.classlist = classlist
        self.item_type = classlist._class_handle
        if not issubclass(self.item_type, pydantic.BaseModel):
            raise NotImplementedError("ClassListTableModel only works for classlists of Pydantic models!")
        self.headers = list(self.item_type.model_fields)

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
            if isinstance(data, list):
                return ", ".join(data)
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
                    with contextlib.suppress(UserWarning):
                        setattr(self.classlist[row], param, value)
                except pydantic.ValidationError:
                    return False
                if not self.edit_mode:
                    # recalculate plots if value was changed
                    recalculate = self.index_header(index) == "value"
                    self.parent.update_project(recalculate)
                self.dataChanged.emit(index, index)
                return True
        return False

    def headerData(self, section, orientation, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if (
            orientation == QtCore.Qt.Orientation.Horizontal
            and role == QtCore.Qt.ItemDataRole.DisplayRole
            and section != 0
        ):
            header = self.headers[section - 1]
            if "SLD" in header:
                header = header.replace("_", " ")
            else:
                header = header.replace("_", " ").title()
            return header
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

    classlist_model = ClassListTableModel

    # the model can change and disconnect, so we re-connect it
    # to a signal here on each change
    edited = QtCore.pyqtSignal()

    def __init__(self, field: str, parent):
        super().__init__(parent)
        self.field = field
        header = field.replace("_", " ").title()
        self.parent = parent
        self.project_widget = parent.parent
        self.table = QtWidgets.QTableView(parent)
        self.table.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.MinimumExpanding
        )
        self.table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

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
        self.model.dataChanged.connect(lambda: self.edited.emit())
        self.model.modelReset.connect(lambda: self.edited.emit())
        self.table.hideColumn(0)
        self.set_item_delegates()
        header = self.table.horizontalHeader()

        header.setSectionResizeMode(self.model.headers.index("name") + 1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

    def set_item_delegates(self):
        """Set item delegates and open persistent editors for the table."""
        for i, header in enumerate(self.model.headers):
            self.table.setItemDelegateForColumn(
                i + 1, delegates.ValidatedInputDelegate(self.model.item_type.model_fields[header], self.table)
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

    def update_project(self, recalculate: bool):
        """Update the field in the parent Project.

        Parameters
        ----------
        recalculate : bool
            Whether to recalculate the plots when the project updates.
        """
        presenter = self.parent.parent.parent.presenter
        presenter.edit_project({self.field: self.model.classlist})
        if recalculate and presenter.view.settings.live_recalculate:
            presenter.run("calculate")


class ParametersModel(ClassListTableModel):
    """Classlist model for Parameters."""

    def __init__(self, classlist: RATapi.ClassList, parent: QtWidgets.QWidget):
        super().__init__(classlist, parent)
        self.headers.insert(0, self.headers.pop(self.headers.index("fit")))
        self.headers.pop(self.headers.index("show_priors"))

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
                self.table.setItemDelegateForColumn(i + 1, delegates.ValueSpinBoxDelegate(header, self.table))
            else:
                self.table.setItemDelegateForColumn(
                    i + 1, delegates.ValidatedInputDelegate(self.model.item_type.model_fields[header], self.table)
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


class LayersModel(ClassListTableModel):
    """Classlist model for Layers."""

    def __init__(self, classlist: RATapi.ClassList, parent: QtWidgets.QWidget):
        super().__init__(classlist, parent)
        self.absorption = classlist._class_handle == RATapi.models.AbsorptionLayer
        self.SLD_imags = {}

    def flags(self, index):
        flags = super().flags(index)
        if self.edit_mode:
            flags |= QtCore.Qt.ItemFlag.ItemIsEditable
        return flags

    def append_item(self):
        kwargs = {"thickness": "", "SLD": "", "roughness": ""}
        if self.absorption:
            kwargs["SLD_imaginary"] = ""
        self.classlist.append(self.item_type(**kwargs))
        self.endResetModel()

    def set_absorption(self, absorption: bool):
        """Set whether the project is using absorption or not.

        Parameters
        ----------
        absorption : bool
            Whether the project is using absorption.

        """
        if self.absorption != absorption:
            self.beginResetModel()
            self.absorption = absorption
            if absorption:
                classlist = RATapi.ClassList(
                    [
                        RATapi.models.AbsorptionLayer(
                            **dict(layer),
                            SLD_imaginary=self.SLD_imags.get(layer.name, ""),
                        )
                        for layer in self.classlist
                    ]
                )
                # set handle manually for if classlist is empty
                classlist._class_handle = RATapi.models.AbsorptionLayer
            else:
                # we save the SLD_imaginary values so that they aren't lost if the
                # user accidentally toggles absorption off and on!
                self.SLD_imags = {layer.name: layer.SLD_imaginary for layer in self.classlist}
                classlist = RATapi.ClassList(
                    [
                        RATapi.models.Layer(
                            name=layer.name,
                            thickness=layer.thickness,
                            SLD=layer.SLD_real,
                            roughness=layer.roughness,
                            hydration=layer.hydration,
                            hydrate_with=layer.hydrate_with,
                        )
                        for layer in self.classlist
                    ]
                )
                classlist._class_handle = RATapi.models.Layer
            self.setup_classlist(classlist)
            self.parent.parent.parent.update_draft_project({"layers": classlist})
            self.endResetModel()


class LayerFieldWidget(ProjectFieldWidget):
    """Project field widget for Layer objects."""

    classlist_model = LayersModel

    def set_item_delegates(self):
        for i in range(1, self.model.columnCount()):
            if i in [1, self.model.columnCount() - 1]:
                header = self.model.headers[i - 1]
                self.table.setItemDelegateForColumn(
                    i, delegates.ValidatedInputDelegate(self.model.item_type.model_fields[header], self.table)
                )
            else:
                blank_option = self.model.headers[i - 1] == "hydration"
                self.table.setItemDelegateForColumn(
                    i, delegates.ProjectFieldDelegate(self.project_widget, "parameters", self.table, blank_option)
                )

    def set_absorption(self, absorption: bool):
        """Set whether the classlist uses AbsorptionLayers.

        Parameters
        ----------
        absorption : bool
            Whether the classlist should use AbsorptionLayers.

        """
        self.model.set_absorption(absorption)
        if self.model.edit_mode:
            self.edit()


class DomainsModel(ClassListTableModel):
    """Classlist model for domain contrasts."""

    def flags(self, index):
        flags = super().flags(index)
        if self.edit_mode:
            flags |= QtCore.Qt.ItemFlag.ItemIsEditable
        return flags


class DomainContrastWidget(ProjectFieldWidget):
    """Subclass of field widgets for domain contrasts."""

    classlist_model = DomainsModel

    def __init__(self, field, parent):
        super().__init__(field, parent)
        self.project_widget = parent.parent

    def update_model(self, classlist):
        super().update_model(classlist)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Stretch)

    def set_item_delegates(self):
        self.table.setItemDelegateForColumn(
            1, delegates.ValidatedInputDelegate(self.model.item_type.model_fields["name"], self.table)
        )
        self.table.setItemDelegateForColumn(2, delegates.MultiSelectLayerDelegate(self.project_widget, self.table))


class CustomFileModel(ClassListTableModel):
    """Classlist model for custom files."""

    def __init__(self, classlist: RATapi.ClassList, parent: QtWidgets.QWidget):
        super().__init__(classlist, parent)
        self.func_names = {}
        self.headers.remove("path")

    def columnCount(self, parent=None) -> int:
        return super().columnCount() + 1

    def headerData(self, section, orientation, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if section == self.columnCount() - 1:
            return None
        return super().headerData(section, orientation, role)

    def flags(self, index):
        flags = super().flags(index)
        if index.column() in [0, self.columnCount() - 1]:
            return QtCore.Qt.ItemFlag.NoItemFlags
        if self.edit_mode:
            flags |= QtCore.Qt.ItemFlag.ItemIsEditable
        return flags

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        data = super().data(index, role)
        if role == QtCore.Qt.ItemDataRole.DisplayRole and self.index_header(index) == "filename" and self.edit_mode:
            if data == "":
                return "Browse..."
            return str(self.classlist[index.row()].path / data)

        return data

    def setData(self, index, value, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if self.index_header(index) == "filename":
            file_path = Path(value)
            row = index.row()
            self.classlist[row].path = file_path.parent
            self.classlist[row].filename = str(file_path.name)

            # auto-set language from file extension if possible
            # & get file names for dropdown on Python
            extension = file_path.suffix
            match extension:
                case ".py":
                    language = Languages.Python
                    # the regex:
                    # (?:^|\n) means 'match start of the string (i.e. the file) or a newline'
                    # (\S+) means 'capture one or more non-whitespace characters'
                    # so the regex captures a word between 'def ' and '(', i.e. a function name
                    func_names = re.findall(r"(?:^|\n)def (\S+)\(", file_path.read_text())
                case ".m":
                    language = Languages.Matlab
                    func_names = None
                case ".dll" | ".so" | ".dylib":
                    language = Languages.Cpp
                    func_names = None
                case _:
                    language = None
                    func_names = None
            self.func_names[value] = func_names
            if func_names:
                self.classlist[row].function_name = func_names[0]
            if language is not None:
                self.classlist[row].language = language

            self.dataChanged.emit(index, index)
            return True

        return super().setData(index, value, role)

    def append_item(self):
        """Append an item to the ClassList."""
        self.classlist.append(self.item_type(filename="", path="/"))
        self.endResetModel()

    def index_header(self, index):
        if index.column() == self.columnCount() - 1:
            return None
        return super().index_header(index)


class CustomFileWidget(ProjectFieldWidget):
    classlist_model = CustomFileModel

    def update_model(self, classlist):
        super().update_model(classlist)
        self.table.hideColumn(self.model.columnCount() - 1)

    def edit(self):
        super().edit()
        edit_file_column = self.model.columnCount() - 1
        self.table.showColumn(edit_file_column)
        # disconnect from old table's buttons so they don't create dangling references
        # if no connections currently exist (i.e. table empty), disconnect() raises a TypeError
        with contextlib.suppress(TypeError):
            self.model.dataChanged.disconnect()
        for i in range(0, self.model.rowCount()):
            self.table.setIndexWidget(self.model.index(i, edit_file_column), self.make_edit_button(i))

    def make_edit_button(self, index):
        button = QtWidgets.QPushButton("Edit File", self.table)
        q_scintilla_action = QtGui.QAction("Edit in RasCAL-2...", self.table)
        q_scintilla_action.triggered.connect(
            lambda: edit_file(
                self.model.classlist[index].path / self.model.classlist[index].filename,
                self.model.classlist[index].language,
                self,
            )
        )
        matlab_action = QtGui.QAction("Edit in MATLAB...", self.table)
        matlab_action.triggered.connect(
            lambda: edit_file_matlab(self.model.classlist[index].path / self.model.classlist[index].filename)
        )
        menu = QtWidgets.QMenu(self.table)
        menu.addActions([q_scintilla_action, matlab_action])

        def setup_button():
            """Check whether the button should be editable and set it up for the right language."""
            language = self.model.data(self.model.index(index, self.model.headers.index("language") + 1))
            with contextlib.suppress(TypeError):
                button.pressed.disconnect()
            if language == Languages.Matlab:
                button.setMenu(menu)
                button.pressed.connect(button.showMenu)
            else:
                button.setMenu(None)
                button.pressed.connect(
                    lambda: edit_file(
                        self.model.classlist[index].path / self.model.classlist[index].filename,
                        self.model.classlist[index].language,
                        self,
                    )
                )

            editable = (language in [Languages.Matlab, Languages.Python]) and (
                self.model.data(self.model.index(index, self.model.headers.index("filename") + 1)) != "Browse..."
            )
            button.setEnabled(editable)

        setup_button()
        self.model.dataChanged.connect(lambda: setup_button())

        return button

    def set_item_delegates(self):
        super().set_item_delegates()
        filename_index = self.model.headers.index("filename") + 1
        function_index = self.model.headers.index("function_name") + 1
        self.table.setItemDelegateForColumn(
            filename_index, delegates.ValidatedInputDelegate(self.model.item_type.model_fields["path"], self.table)
        )
        self.table.setItemDelegateForColumn(function_index, delegates.CustomFileFunctionDelegate(self))


class AbstractSignalModel(ClassListTableModel):
    """Model for Signal objects (backgrounds and resolutions)."""

    def flags(self, index):
        flags = super().flags(index)
        if self.edit_mode:
            flags |= QtCore.Qt.ItemFlag.ItemIsEditable
        match self.classlist[index.row()].type:  # disable unused value fields
            case TypeOptions.Constant:
                disable_from_col = self.num_valid_values[0]
            case TypeOptions.Data:
                disable_from_col = self.num_valid_values[1]
            case TypeOptions.Function:
                disable_from_col = self.num_valid_values[2]
        if index.column() > disable_from_col + 3:  # +3 offset for name, type, source
            flags = QtCore.Qt.ItemFlag.NoItemFlags
        return flags

    @property
    def num_valid_values(self) -> tuple[int]:
        """The number of valid value fields for each type.

        Returns
        -------
        Tuple[int]
            The number of valid values for constant, data, and function signals respectively.

        """
        raise NotImplementedError


class BackgroundsModel(AbstractSignalModel):
    """Model for classlists of Backgrounds."""

    @property
    def num_valid_values(self) -> tuple[int]:
        return (0, 1, 5)


class ResolutionsModel(AbstractSignalModel):
    """Model for classlists of Resolutions."""

    @property
    def num_valid_values(self) -> tuple[int]:
        return (0, -1, 5)  # -1 to remove 'source' field for data resolutions


class AbstractSignalFieldWidget(ProjectFieldWidget):
    """Project field widget for 'signal' objects (backgrounds and resolutions)."""

    def set_item_delegates(self):
        super().set_item_delegates()
        source_index = self.model.headers.index("source") + 1
        self.table.setItemDelegateForColumn(
            source_index, delegates.SignalSourceDelegate(self.project_widget, self.parameter_field, self.table)
        )
        for column in range(source_index + 1, self.model.columnCount()):
            self.table.setItemDelegateForColumn(
                column, delegates.ProjectFieldDelegate(self.project_widget, self.parameter_field, self.table)
            )

    @property
    def parameter_field(self) -> str:
        """The relevant parameter field for the object.

        Returns
        -------
        str
            The name of the relevant parameter field for the object.

        """
        raise NotImplementedError


class BackgroundsFieldWidget(AbstractSignalFieldWidget):
    """Project field widget for backgrounds."""

    classlist_model = BackgroundsModel

    @property
    def parameter_field(self) -> str:
        return "background_parameters"


class ResolutionsFieldWidget(AbstractSignalFieldWidget):
    """Project field widget for resolutions."""

    classlist_model = ResolutionsModel

    def set_item_delegates(self):
        super().set_item_delegates()
        # workaround to remove function resolution option
        type_index = self.model.headers.index("type") + 1
        self.table.setItemDelegateForColumn(
            type_index,
            delegates.ValidatedInputDelegate(self.model.item_type.model_fields["type"], self.table, remove_items=[2]),
        )
        # hide unused value_2 through value_5
        for column in range(4, 9):
            self.table.setColumnHidden(column, True)

    @property
    def parameter_field(self) -> str:
        return "resolution_parameters"
