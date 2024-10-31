"""Widgets for validated user inputs."""

from enum import Enum
from math import floor, log10
from typing import Callable

from pydantic.fields import FieldInfo
from PyQt6 import QtCore, QtGui, QtWidgets


def get_validated_input(field_info: FieldInfo) -> QtWidgets.QWidget:
    """Get a validated input widget from Pydantic field info.

    Parameters
    ----------
    field_info : FieldInfo
        The Pydantic field info for the field.

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
    }

    for input_type, widget in class_widgets.items():
        if issubclass(field_info.annotation, input_type):
            return widget(field_info)

    return BaseInputWidget(field_info)


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
        layout.addWidget(self.editor)
        layout.setContentsMargins(5, 0, 0, 0)

        self.setLayout(layout)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)

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
        if isinstance(field_info.default, (int, float)) and field_info.default > 0:
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


class AdaptiveDoubleSpinBox(QtWidgets.QDoubleSpinBox):
    """A double spinbox which adapts to given numbers of decimals."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStepType(self.StepType.AdaptiveDecimalStepType)
        self.setKeyboardTracking(False)

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
        return f"{round(value, self.decimals()):.{self.decimals()}g}"

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
        if "e" in input_text:
            try:
                self.setDecimals(-int(input_text.split("e")[-1]))
                return (QtGui.QValidator.State.Acceptable, input_text, pos)
            except ValueError:
                return (QtGui.QValidator.State.Intermediate, input_text, pos)
        if "." in input_text and len(input_text.split(".")[-1]) != self.decimals():
            self.setDecimals(len(input_text.split(".")[-1]))
            return (QtGui.QValidator.State.Acceptable, input_text, pos)
        return super().validate(input_text, pos)
