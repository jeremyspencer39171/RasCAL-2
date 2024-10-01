"""Widget for validated user inputs."""

from enum import Enum
from math import floor, log10
from typing import Callable

from pydantic.fields import FieldInfo
from PyQt6 import QtCore, QtGui, QtWidgets


class ValidatedInputWidget(QtWidgets.QWidget):
    """Value input generated from Pydantic field info.

    Parameters
    ----------
    field_info: FieldInfo
        The Pydantic field info for the input.
    parent: QWidget or None, default None
        The parent widget of this widget.

    """

    def __init__(self, field_info: FieldInfo, parent=None):
        super().__init__(parent=parent)
        layout = QtWidgets.QVBoxLayout()
        # editor_data and change_editor_data are set to the getter and setter
        # methods for the actual editor inside the widget
        self.get_data: Callable
        self.set_data: Callable
        self.edited_signal: QtCore.pyqtSignal

        # widget, getter, setter and change signal for different datatypes
        editor_types = {
            int: (QtWidgets.QSpinBox, "value", "setValue", "editingFinished"),
            float: (AdaptiveDoubleSpinBox, "value", "setValue", "editingFinished"),
            bool: (QtWidgets.QCheckBox, "isChecked", "setChecked", "checkStateChanged"),
        }
        defaults = (QtWidgets.QLineEdit, "text", "setText", "textChanged")

        if issubclass(field_info.annotation, Enum):
            self.editor = QtWidgets.QComboBox(self)
            self.editor.addItems(str(e.value) for e in field_info.annotation)
            self.get_data = self.editor.currentText
            self.set_data = self.editor.setCurrentText
            self.edited_signal = self.editor.currentTextChanged
        else:
            editor, getter, setter, signal = editor_types.get(field_info.annotation, defaults)
            self.editor = editor(self)
            self.get_data = getattr(self.editor, getter)
            self.set_data = getattr(self.editor, setter)
            self.edited_signal = getattr(self.editor, signal)
        if isinstance(self.editor, QtWidgets.QSpinBox):
            for item in field_info.metadata:
                if hasattr(item, "ge"):
                    self.editor.setMinimum(item.ge)
                if hasattr(item, "gt"):
                    self.editor.setMinimum(item.gt + 1)
                if hasattr(item, "le"):
                    self.editor.setMaximum(item.le)
                if hasattr(item, "lt"):
                    self.editor.setMaximum(item.lt - 1)
        elif isinstance(self.editor, AdaptiveDoubleSpinBox):
            for item in field_info.metadata:
                for attr in ["ge", "gt"]:
                    if hasattr(item, attr):
                        self.editor.setMinimum(getattr(item, attr))
                for attr in ["le", "lt"]:
                    if hasattr(item, attr):
                        self.editor.setMaximum(getattr(item, attr))
            # if no default exists, field_info.default is PydanticUndefined not a nonexistent attribute
            if isinstance(field_info.default, (int, float)) and field_info.default > 0:
                # set default decimals to order of magnitude of default value
                self.editor.setDecimals(-floor(log10(abs(field_info.default))))

        layout.addWidget(self.editor)
        layout.setContentsMargins(5, 0, 0, 0)

        self.setLayout(layout)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)


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

    def validate(self, input, pos) -> tuple[QtGui.QValidator.State, str, int]:
        """Validate a string written into the spinbox.

        Override of QtWidgets.QDoubleSpinBox.validate.

        Parameters
        ----------
        input : str
            The string written into the spinbox.
        pos : int
            The current cursor position.

        Returns
        -------
        tuple[QtGui.QValidator.State, str, int]
            The validation state of the input, the input string, and position.

        """
        if "e" in input:
            try:
                self.setDecimals(-int(input.split("e")[-1]))
                return (QtGui.QValidator.State.Acceptable, input, pos)
            except ValueError:
                return (QtGui.QValidator.State.Intermediate, input, pos)
        if "." in input and len(input.split(".")[-1]) != self.decimals():
            self.setDecimals(len(input.split(".")[-1]))
            return (QtGui.QValidator.State.Acceptable, input, pos)
        return super().validate(input, pos)
