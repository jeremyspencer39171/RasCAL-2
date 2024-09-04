"""File for Qt commands."""

from PyQt6 import QtGui


class EditControls(QtGui.QUndoCommand):
    """Command for editing the Controls object."""

    def __init__(self, controls, attr, value):
        super().__init__()
        self.controls = controls
        self.attr = attr
        self.value = value

    def undo(self):
        setattr(self.controls, self.attr, self.value)

    def redo(self):
        # FIXME: when C++ exceptions can be handled properly,
        # run try/except for validation error here and
        # mark as obsolete if one occurs
        # https://github.com/RascalSoftware/RasCAL-2/issues/26
        setattr(self.controls, self.attr, self.value)

    def text(self):
        return f"Set control {self.attr} to {self.value}"
