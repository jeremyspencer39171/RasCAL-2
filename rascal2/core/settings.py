"""Global settings for RasCAL."""

import logging
from enum import IntEnum, StrEnum
from os import PathLike
from pathlib import PurePath
from typing import Any

from pydantic import BaseModel, Field
from PyQt6 import QtCore


# we do this statically rather than making it an attribute of Settings because all fields in a Pydantic model
# must be pickleable, so it's easier to keep this 'outside' the model
def get_global_settings() -> QtCore.QSettings:
    """Get the global settings QSettings object."""
    return QtCore.QSettings(
        QtCore.QSettings.Format.IniFormat,
        QtCore.QSettings.Scope.UserScope,
        "RasCAL-2",
        "RasCAL-2",
    )


class Styles(StrEnum):
    """Visual styles for RasCAL-2."""

    Light = "light"


class LogLevels(IntEnum):
    """Debug log-levels with human readable string names."""

    Debug = logging.DEBUG
    Info = logging.INFO
    Warning = logging.WARNING
    Error = logging.ERROR
    Critical = logging.CRITICAL

    def __str__(self):
        names = {
            LogLevels.Debug: "DEBUG",
            LogLevels.Info: "INFO",
            LogLevels.Warning: "WARNING",
            LogLevels.Error: "ERROR",
            LogLevels.Critical: "CRITICAL",
        }
        return names[self]

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            return cls(getattr(logging, value.upper()))
        raise ValueError("Not a known logging level.")


class Settings(BaseModel, validate_assignment=True, arbitrary_types_allowed=True):
    """Model for system settings.

    If a setting is not provided, it will fallback to the global default.

    Notes
    -----
    For each system setting, the model field `title` contains the setting group,
    and the model field `description` gives an English name for the setting.
    The model fields for a setting can be accessed via Settings.model_fields[setting].

    """

    # The Settings object's own model fields contain the within-project settings.
    # The global settings are read and written via this object using `set_global_settings`.
    style: Styles = Field(default=Styles.Light, title="general", description="Style")
    editor_fontsize: int = Field(default=12, title="general", description="Editor Font Size", gt=0)
    terminal_fontsize: int = Field(default=12, title="general", description="Terminal Font Size", gt=0)
    log_path: str = Field(default="logs/rascal.log", title="logging", description="Path to Log File")
    log_level: LogLevels = Field(default=LogLevels.Info, title="logging", description="Minimum Log Level")

    def model_post_init(self, __context: Any):
        global_settings = get_global_settings()
        unset_settings = [s for s in self.model_fields if s not in self.model_fields_set]
        for setting in unset_settings:
            if global_name(setting) in global_settings.allKeys():
                setattr(self, setting, global_settings.value(global_name(setting)))
                self.model_fields_set.remove(setting)  # we don't want global defaults to count as manually set!

    def save(self, path: str | PathLike):
        """Save settings to a JSON file in the given path.

        Parameters
        ----------
        path : str or PathLike
            The path to the folder where settings will be saved.

        """
        file = PurePath(path, "settings.json")
        with open(file, "w") as f:
            f.write(self.model_dump_json(exclude_unset=True))

    def set_global_settings(self):
        """Set manually-set local settings as global settings."""
        global_settings = get_global_settings()
        for setting in self.model_fields_set:
            global_settings.setValue(global_name(setting), getattr(self, setting))


def global_name(key: str) -> str:
    """Get the QSettings global name of a setting.

    Parameters
    ----------
    key : str
        The attribute name for the setting.

    Returns
    -------
    str
        The QSettings string for the setting.

    """
    group = Settings.model_fields[key].title
    if group:
        return f"{group}/{key}"
    return key
