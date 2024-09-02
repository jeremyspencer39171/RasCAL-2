"""Test the Settings model."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from rascal2.core import Settings


class MockGlobalSettings:
    """A mock of the global settings."""

    def __init__(self):
        self.settings = {"general/editor_fontsize": 15, "general/terminal_fontsize": 28}

    def value(self, key):
        return self.settings[key]

    def allKeys(self):
        return list(self.settings.keys())


def mock_get_global_settings():
    """Mock for `get_global_settings`."""
    return MockGlobalSettings()


@patch("rascal2.core.settings.get_global_settings", new=mock_get_global_settings)
def test_global_defaults():
    """Test that settings are overwritten by global settings only if not manually set."""
    default_set = Settings()
    assert default_set.editor_fontsize == 15
    assert default_set.terminal_fontsize == 28
    edit_set = Settings(editor_fontsize=12)
    assert edit_set.editor_fontsize == 12
    assert edit_set.terminal_fontsize == 28
    all_set = Settings(editor_fontsize=12, terminal_fontsize=15)
    assert all_set.editor_fontsize == 12
    assert all_set.terminal_fontsize == 15


@pytest.mark.parametrize("kwargs", [{}, {"style": "light", "editor_fontsize": 15}, {"terminal_fontsize": 8}])
@patch("rascal2.core.settings.get_global_settings", new=mock_get_global_settings)
def test_save(kwargs):
    """Tests that settings files can be saved and retrieved."""
    settings = Settings(**kwargs)
    with tempfile.TemporaryDirectory() as temp:
        settings.save(temp)
        json = Path(temp, "settings.json").read_text()

    for setting in kwargs:
        assert setting in json
        assert str(kwargs[setting]) in json

    loaded_settings = Settings.model_validate_json(json)

    assert settings == loaded_settings


@patch("rascal2.core.settings.QtCore.QSettings.setValue")
def test_set_global(mock):
    """Test that we can set manually-set project settings as global settings."""
    settings = Settings()
    settings.set_global_settings()
    assert not mock.called

    settings = Settings(editor_fontsize=9)
    settings.set_global_settings()
    mock.assert_called_once_with("general/editor_fontsize", 9)

    mock.reset_mock()
    settings = Settings(editor_fontsize=18, terminal_fontsize=3)
    settings.set_global_settings()
    print(mock.mock_calls)
    mock.assert_any_call("general/editor_fontsize", 18)
    mock.assert_any_call("general/terminal_fontsize", 3)
