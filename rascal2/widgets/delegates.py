"""Delegates for items in Qt tables."""

from PyQt6 import QtCore, QtGui, QtWidgets


class EnumDelegate(QtWidgets.QStyledItemDelegate):
    """Item delegate for Enums."""

    def __init__(self, parent, enum):
        super().__init__(parent)
        self.enum = enum

    def createEditor(self, parent, option, index):
        combobox = QtWidgets.QComboBox(parent)
        combobox.addItems(str(e.value) for e in self.enum)
        return combobox

    def setEditorData(self, editor: QtWidgets.QCheckBox, index):
        data = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        editor.setCurrentText(data)


class BoolDelegate(QtWidgets.QStyledItemDelegate):
    """Item delegate for bools."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def createEditor(self, parent, option, index):
        checkbox = QtWidgets.QCheckBox(parent)
        # fill in background as otherwise you can see the original View text underneath
        checkbox.setAutoFillBackground(True)
        checkbox.setBackgroundRole(QtGui.QPalette.ColorRole.Base)
        return checkbox

    def setEditorData(self, editor: QtWidgets.QCheckBox, index):
        data = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        data = data == "True"  # data from model is given as a string
        editor.setChecked(data)
