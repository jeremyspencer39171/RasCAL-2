"""Test input widgets."""

from enum import StrEnum

import pytest
from pydantic.fields import FieldInfo
from PyQt6 import QtWidgets

from rascal2.widgets import AdaptiveDoubleSpinBox, get_validated_input


class MyEnum(StrEnum):
    VALUE_1 = "value 1"
    VALUE_2 = "value 2"
    VALUE_3 = "value 3"


@pytest.mark.parametrize(
    ("field_info", "expected_type", "example_data"),
    [
        (FieldInfo(annotation=bool), QtWidgets.QCheckBox, True),
        (FieldInfo(annotation=float), AdaptiveDoubleSpinBox, 11.5),
        (FieldInfo(annotation=int), QtWidgets.QSpinBox, 15),
        (FieldInfo(annotation=MyEnum), QtWidgets.QComboBox, "value 2"),
        (FieldInfo(annotation=str), QtWidgets.QLineEdit, "Test string"),
    ],
)
def test_editor_type(field_info, expected_type, example_data):
    """Test that the editor type is as expected, and can be read and written."""

    widget = get_validated_input(field_info)
    assert isinstance(widget.editor, expected_type)
    widget.set_data(example_data)
    assert widget.get_data() == example_data


@pytest.mark.parametrize(("value", "decimals"), [("10.", 0), ("1e-5", 5), ("0.01144661", 8)])
def test_adaptive_spinbox(value, decimals):
    spinbox = AdaptiveDoubleSpinBox()
    spinbox.validate(value, 0)
    assert spinbox.decimals() == decimals
