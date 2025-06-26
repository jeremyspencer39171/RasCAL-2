"""Widgets for validated user inputs."""

from collections.abc import Iterable
from enum import Enum
from math import floor, log10
from pathlib import Path
from typing import Callable

from pydantic.fields import FieldInfo
from PyQt6 import QtCore, QtGui, QtWidgets


def get_validated_input(field_info: FieldInfo, parent=None) -> QtWidgets.QWidget:
    """Get a validated input widget from Pydantic field info.

    Parameters
    ----------
    field_info : FieldInfo
        The Pydantic field info for the field.
    parent : QWidget or None, default None
        The parent widget of this widget.

    Returns
    -------
    QtWidgets.QWidget
        The validated input widget for the field.

    """
    class_widgets = {
        bool: BoolInputWidget,
        int: IntInputWidget,
        float: FloatInputWidget,
        Enum: EnumInputWidget,
        Path: PathInputWidget,
    }

    for input_type, widget in class_widgets.items():
        if issubclass(field_info.annotation, input_type):
            return widget(field_info, parent)

    return BaseInputWidget(field_info, parent)


class BaseInputWidget(QtWidgets.QWidget):
    """Base class for input generated from Pydantic field info.

    This base class is used for unrecognised types.

    Parameters
    ----------
    field_info : FieldInfo
        The Pydantic field info for the input.
    parent : QWidget or None, default None
        The parent widget of this widget.

    """

    data_getter = "text"
    data_setter = "setText"
    edit_signal = "textChanged"

    def __init__(self, field_info: FieldInfo, parent=None):
        super().__init__(parent=parent)

        self.editor: QtWidgets.QWidget = self.create_editor(field_info)
        self.get_data: Callable = getattr(self.editor, self.data_getter)
        self.set_data: Callable = getattr(self.editor, self.data_setter)
        self.edited_signal: QtCore.pyqtSignal = getattr(self.editor, self.edit_signal)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.editor)
        self.setLayout(layout)

    def create_editor(self, field_info: FieldInfo) -> QtWidgets.QWidget:
        """Create the relevant editor for the field information.

        Parameters
        ----------
        field_info : FieldInfo
            The Pydantic field information for the input.

        Returns
        -------
        QtWidgets.QWidget
            A widget which allows restricted input based on the field information.

        """
        return QtWidgets.QLineEdit(self)


class IntInputWidget(BaseInputWidget):
    """Input widget for integer data with optional minimum and maximum values."""

    data_getter = "value"
    data_setter = "setValue"
    edit_signal = "editingFinished"

    def create_editor(self, field_info: FieldInfo) -> QtWidgets.QWidget:
        editor = QtWidgets.QSpinBox(self)
        # default max and min are 99 and 0
        # there is no 'integer infinity' so we just set them to biggest possible numbers
        editor.setMaximum(2**31 - 1)
        editor.setMinimum(-(2**31))
        for item in field_info.metadata:
            if hasattr(item, "ge"):
                editor.setMinimum(item.ge)
            if hasattr(item, "gt"):
                editor.setMinimum(item.gt + 1)
            if hasattr(item, "le"):
                editor.setMaximum(item.le)
            if hasattr(item, "lt"):
                editor.setMaximum(item.lt - 1)

        return editor


class FloatInputWidget(BaseInputWidget):
    """Input widget for float data with optional minimum and maximum values."""

    data_getter = "value"
    data_setter = "setValue"
    edit_signal = "editingFinished"

    def create_editor(self, field_info: FieldInfo) -> QtWidgets.QWidget:
        editor = AdaptiveDoubleSpinBox(self)
        for item in field_info.metadata:
            for attr in ["ge", "gt"]:
                if hasattr(item, attr):
                    editor.setMinimum(getattr(item, attr))
            for attr in ["le", "lt"]:
                if hasattr(item, attr):
                    editor.setMaximum(getattr(item, attr))
        # if no default exists, field_info.default is PydanticUndefined not a nonexistent attribute
        if isinstance(field_info.default, (int, float)) and 0 < field_info.default < float("inf"):
            # set default decimals to order of magnitude of default value
            editor.setDecimals(-floor(log10(abs(field_info.default))))

        return editor


class BoolInputWidget(BaseInputWidget):
    """Input widget for boolean data."""

    data_getter = "isChecked"
    data_setter = "setChecked"
    edit_signal = "checkStateChanged"

    def create_editor(self, field_info: FieldInfo) -> QtWidgets.QWidget:
        return QtWidgets.QCheckBox(self)


class EnumInputWidget(BaseInputWidget):
    """Input widget for Enums."""

    data_getter = "currentData"
    data_setter = "setCurrentText"
    edit_signal = "currentTextChanged"

    def create_editor(self, field_info: FieldInfo) -> QtWidgets.QWidget:
        editor = QtWidgets.QComboBox(self)
        for e in field_info.annotation:
            editor.addItem(str(e), e)

        return editor


class PathInputWidget(BaseInputWidget):
    """Input widget for paths."""

    edit_signal = "pressed"

    def create_editor(self, field_info: FieldInfo) -> QtWidgets.QWidget:
        file_dialog = QtWidgets.QFileDialog(parent=self)

        def open_file():
            file = file_dialog.getOpenFileName()[0]
            if file:
                browse_button.setText(file)

        browse_button = QtWidgets.QPushButton("Browse...", self)
        browse_button.clicked.connect(lambda: open_file())

        return browse_button


class AdaptiveDoubleSpinBox(QtWidgets.QDoubleSpinBox):
    """A double spinbox which adapts to given numbers of decimals."""

    MIN_DECIMALS = 2

    def __init__(self, parent=None):
        super().__init__(parent)

        # default max and min are 99.99 and 0.0
        self.setMaximum(float("inf"))
        self.setMinimum(-float("inf"))

        self.setStepType(self.StepType.AdaptiveDecimalStepType)
        self.setKeyboardTracking(False)

        self.setDecimals(12)

    def textFromValue(self, value):
        """Set the display text for the spinbox from the value stored in the widget.

        Override of QtWidgets.QDoubleSpinBox.textFromValue.

        Parameters
        ----------
        value : float
            The float value stored in the widget.

        Returns
        -------
        str
            The string displayed on the spinbox.

        """
        if value == float("inf"):
            return "inf"
        if value == -float("inf"):
            return "-inf"
        return f"{round(value, 12):.12g}"

    def valueFromText(self, text: str) -> float:
        """Set the underlying value of the spinbox from the text input."""
        if text == "inf":
            return float("inf")
        if text == "-inf":
            return -float("inf")
        return float(text)

    def setValue(self, value: float):
        """Hook into setValue that sets the decimals when the value is manually set.

        Parameters
        ----------
        value : float
            The value to set the spinbox to.
        """
        state, text, _ = self.validate(str(value), 0)
        if state == QtGui.QValidator.State.Acceptable:
            value = float(text)
            super().setValue(value)

    def stepBy(self, steps: int):
        """Step the value up or down by some amount.

        Override of QtWidgets.QDoubleSpinBox.stepBy to handle infs.

        Parameters
        ----------
        steps : int
            The number of linesteps to step by.

        """
        if self.value() == float("inf") and steps < 0:
            self.setValue(1e12)  # largest possible float that doesn't look ugly in the box
        if self.value() == -float("inf") and steps > 0:
            self.setValue(1e-12)  # smallest possible float that pyqt doesn't round to 0
        else:
            super().stepBy(steps)

    def validate(self, input_text, pos) -> tuple[QtGui.QValidator.State, str, int]:
        """Validate a string written into the spinbox.

        Override of QtWidgets.QDoubleSpinBox.validate.

        Parameters
        ----------
        input_text : str
            The string written into the spinbox.
        pos : int
            The current cursor position.

        Returns
        -------
        tuple[QtGui.QValidator.State, str, int]
            The validation state of the input, the input string, and position.

        """
        if input_text in "inf" or input_text in "-inf":
            if input_text in ["inf", "-inf"]:
                return (QtGui.QValidator.State.Acceptable, input_text, pos)
            else:
                return (QtGui.QValidator.State.Intermediate, input_text, pos)
        elif "e" in input_text or "E" in input_text:
            try:
                _ = float(input_text)  # to ensure that we actually have a number before we accept
                return (QtGui.QValidator.State.Acceptable, input_text, pos)
            except ValueError:
                return (QtGui.QValidator.State.Intermediate, input_text, pos)
        elif "." in input_text:
            # don't accept multiple decimal points
            if len(input_text.split(".")) > 2:
                return (QtGui.QValidator.State.Intermediate, input_text, pos)
            return (QtGui.QValidator.State.Acceptable, input_text, pos)
        else:
            try:
                _ = float(input_text)  # ensure we have a number
                return (QtGui.QValidator.State.Acceptable, input_text, pos)
            except ValueError:
                return (QtGui.QValidator.State.Intermediate, input_text, pos)


class RangeWidget(QtWidgets.QWidget):
    """A widget to choose a minimum and maximum float, e.g. for a range."""

    data_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.min_box = AdaptiveDoubleSpinBox()
        self.max_box = AdaptiveDoubleSpinBox()

        self.min_box.valueChanged.connect(lambda: self.data_changed.emit())
        self.max_box.valueChanged.connect(lambda: self.data_changed.emit())

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.min_box)
        layout.addWidget(self.max_box)

        self.setLayout(layout)

    def set_data(self, data: Iterable[float]):
        """Set data for the widget.

        Parameters
        ----------
        data : Iterable[float]
            A two-item iterable giving a maximum and minimum value.

        """
        self.min_box.setValue(data[0])
        self.max_box.setValue(data[1])

    def get_data(self) -> list[float]:
        """Get the data from the widget as a list of two values.

        Returns
        -------
        list[float]
            A two-item list of the minimum and maximum respectively.

        """
        return [self.min_box.value(), self.max_box.value()]

    def set_outer_limit(self, limit: Iterable[float]):
        """Set an outer limit for the range.

        Parameters
        ----------
        data : Iterable[float]
            A two-item iterable giving a maximum and minimum value that the range can be.

        """
        self.min_box.setMinimum(limit[0])
        self.max_box.setMaximum(limit[1])

    def set_inner_limit(self, limit: Iterable[float]):
        """Set an inner limit for the range.

        Parameters
        ----------
        data : Iterable[float]
            A two-item iterable giving values that the range must be larger than.

        """
        self.min_box.setMaximum(limit[0])
        self.max_box.setMinimum(limit[1])


class MultiSelectComboBox(QtWidgets.QComboBox):
    """
    A custom combo box widget that allows for multi-select functionality.

    This widget provides the ability to select multiple items from a
    dropdown list and display them in a comma-separated format in the
    combo box's line edit area.

    This is a simplified version of the combobox in
    https://github.com/user0706/pyqt6-multiselect-combobox (MIT License)

    """

    selection_changed = QtCore.pyqtSignal()

    class Delegate(QtWidgets.QStyledItemDelegate):
        def sizeHint(self, option, index):
            size = super().sizeHint(option, index)
            size.setHeight(20)
            return size

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.setEditable(True)
        self.lineEdit().setReadOnly(True)

        self.setItemDelegate(MultiSelectComboBox.Delegate())

        self.model().dataChanged.connect(self.update_text)
        self.lineEdit().installEventFilter(self)
        self.view().viewport().installEventFilter(self)

    def resizeEvent(self, event) -> None:
        """Resize event handler.

        Parameters
        ----------
        event
            The resize event.

        """
        self.update_text()
        super().resizeEvent(event)

    def eventFilter(self, obj, event) -> bool:
        """Event filter to handle mouse button release events.

        Parameters
        ----------
        obj
            The object emitting the event.
        event
            The event being emitted.

        Returns
        -------
        bool
            True if the event was handled, False otherwise.

        """
        if obj == self.view().viewport() and event.type() == QtCore.QEvent.Type.MouseButtonRelease:
            index = self.view().indexAt(event.position().toPoint())
            item = self.model().itemFromIndex(index)
            if item.checkState() == QtCore.Qt.CheckState.Checked:
                item.setCheckState(QtCore.Qt.CheckState.Unchecked)
            else:
                item.setCheckState(QtCore.Qt.CheckState.Checked)
            self.selection_changed.emit()
            return True
        return False

    def update_text(self) -> None:
        """Update the displayed text based on selected items."""
        items = self.selected_items()

        if items:
            text = ", ".join([str(i) for i in items])
        else:
            text = ""

        metrics = QtGui.QFontMetrics(self.lineEdit().font())
        elided_text = metrics.elidedText(text, QtCore.Qt.TextElideMode.ElideRight, self.lineEdit().width())
        self.lineEdit().setText(elided_text)

    def addItem(self, text: str, data: str = None) -> None:
        """Add an item to the combo box.

        Parameters
        ----------
        text : str
            The text to display.
        data : str
            The associated data. Default is None.

        """
        item = QtGui.QStandardItem()
        item.setText(text)
        item.setData(data or text)
        item.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
        item.setData(QtCore.Qt.CheckState.Unchecked, QtCore.Qt.ItemDataRole.CheckStateRole)
        self.model().appendRow(item)

    def addItems(self, texts: list, data_list: list = None) -> None:
        """Add multiple items to the combo box.

        Parameters
        ----------
        texts : list
            A list of items to add.
        data_list : list
            A list of associated data. Default is None.

        """
        data_list = data_list or [None] * len(texts)
        for text, data in zip(texts, data_list):
            self.addItem(text, data)

    def clear(self):
        """Clear all items from the combobox."""
        self.model().removeRows(0, self.model().rowCount())
        self.selection_changed.emit()

    def selected_items(self) -> list:
        """Get the currently selected data.

        Returns
        -------
        list
            A list of currently selected data.

        """
        return [
            self.model().item(i).data()
            for i in range(self.model().rowCount())
            if self.model().item(i).checkState() == QtCore.Qt.CheckState.Checked
        ]

    def select_indices(self, indices: list) -> None:
        """Set the selected items based on the provided indices.

        Parameters
        ----------
        indexes : list
            A list of indexes to select.

        """
        for i in range(self.model().rowCount()):
            self.model().item(i).setCheckState(
                QtCore.Qt.CheckState.Checked if i in indices else QtCore.Qt.CheckState.Unchecked
            )
        self.update_text()
        self.selection_changed.emit()

    def select_items(self, items: list) -> None:
        """Set the selected items based on the provided names.

        If a name is not found in the list of items, it will be ignored.

        Parameters
        ----------
        items : list
            A list of item data to be selected.

        """
        all_items = [self.model().item(i).data() for i in range(self.model().rowCount())]
        indices = []
        for item in items:
            try:
                index = all_items.index(item)
            except ValueError:
                continue
            else:
                indices.append(index)

        self.select_indices(indices)

    def showEvent(self, event) -> None:
        """Show event handler.

        Parameters
        ----------
        event
            The show event.

        """
        super().showEvent(event)
        self.update_text()
