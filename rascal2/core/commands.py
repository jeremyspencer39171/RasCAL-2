"""File for Qt commands."""

from enum import IntEnum, unique
from typing import Callable

from PyQt6 import QtGui
from RATapi import ClassList


@unique
class CommandID(IntEnum):
    """Unique ID for undoable commands"""

    EditControls = 1000
    EditProject = 2000


class AbstractModelEdit(QtGui.QUndoCommand):
    """Command for editing an attribute of the model."""

    attribute = None

    def __init__(self, new_values: dict, presenter):
        super().__init__()
        self.presenter = presenter
        self.new_values = new_values
        if self.attribute is None:
            raise NotImplementedError("AbstractEditModel should not be instantiated directly.")
        else:
            self.model_class = getattr(self.presenter.model, self.attribute)
        self.old_values = {attr: getattr(self.model_class, attr) for attr in self.new_values}
        self.update_text()

    def update_text(self):
        """Update the undo command text."""
        if len(self.new_values) == 1:
            attr, value = list(self.new_values.items())[0]
            if isinstance(list(self.new_values.values())[0], ClassList):
                text = f"Changed values in {attr}"
            else:
                text = f"Set {self.attribute} {attr} to {value}"
        else:
            text = f"Save update to {self.attribute}"

        self.setText(text)

    @property
    def update_attribute(self) -> Callable:
        """Return the method used to update the attribute."""
        raise NotImplementedError

    def undo(self):
        self.update_attribute(self.old_values)

    def redo(self):
        self.update_attribute(self.new_values)

    def mergeWith(self, command):
        """Merges consecutive Edit controls commands if the attributes are the
        same."""

        # We should think about if merging all Edit controls irrespective of
        # attribute is the way to go for UX
        if list(self.new_values.keys()) != list(command.new_values.keys()):
            return False

        if list(self.old_values.values()) == list(command.new_values.values()):
            self.setObsolete(True)

        self.new_values = command.new_values
        self.update_text()
        return True

    def id(self):
        """Returns ID used for merging commands"""
        raise NotImplementedError


class EditControls(AbstractModelEdit):
    attribute = "controls"

    @property
    def update_attribute(self):
        return self.presenter.model.update_controls

    def id(self):
        return CommandID.EditControls


class EditProject(AbstractModelEdit):
    attribute = "project"

    @property
    def update_attribute(self):
        return self.presenter.model.update_project

    def id(self):
        return CommandID.EditProject
