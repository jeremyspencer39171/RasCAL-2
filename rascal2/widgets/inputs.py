"""Widgets for validated user inputs."""

from enum import Enum
from math import floor, log10
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
        layout.addWidget(self.editor)
        layout.setContentsMargins(0, 0, 0, 0)

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
        return f"{round(value, 12):.4g}"

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
        if "e" in input_text or "E" in input_text:
            components = input_text.lower().split("e")
            significand = components[0]
            significand_decimals = len(significand.split(".")[-1])
            exponent = components[1]
            try:
                exponent_order = int(exponent)
                self.setDecimals(max(significand_decimals - exponent_order, 0))
                return (QtGui.QValidator.State.Acceptable, input_text, pos)
            except ValueError:
                return (QtGui.QValidator.State.Intermediate, input_text, pos)
        if "." in input_text and len(input_text.split(".")[-1]) != self.decimals():
            self.setDecimals(len(input_text.split(".")[-1]))
            return (QtGui.QValidator.State.Acceptable, input_text, pos)
        return super().validate(input_text, pos)
