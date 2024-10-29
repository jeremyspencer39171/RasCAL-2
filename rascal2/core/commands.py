"""File for Qt commands."""

from enum import IntEnum, unique

from PyQt6 import QtGui


@unique
class CommandID(IntEnum):
    """Unique ID for undoable commands"""

    EditControls = 1000


class EditControls(QtGui.QUndoCommand):
    """Command for editing the Controls object."""

    def __init__(self, attr, value, presenter):
        super().__init__()
        self.presenter = presenter
        self.attr = attr
        self.value = value
        self.old_value = getattr(self.presenter.model.controls, self.attr)
        self.setText(f"Set control {self.attr} to {self.value}")

    def undo(self):
        self.presenter.model.update_controls({self.attr: self.old_value})

    def redo(self):
        self.presenter.model.update_controls({self.attr: self.value})

    def mergeWith(self, command):
        """Merges consecutive Edit controls commands if the attributes are the
        same."""

        # We should think about if merging all Edit controls irrespective of
        # attribute is the way to go for UX
        if self.attr != command.attr:
            return False

        if self.old_value == command.value:
            self.setObsolete(True)

        self.value = command.value
        self.setText(f"Set control {self.attr} to {self.value}")
        return True

    def id(self):
        """Returns ID used for merging commands"""
        return CommandID.EditControls
