"""Test the Settings model."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from rascal2.core.settings import Settings, delete_local_settings, update_recent_projects


class MockGlobalSettings:
    """A mock of the global settings."""

    def __init__(self):
        self.settings = {"General/editor_fontsize": 15, "Terminal/terminal_fontsize": 28}

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


def test_delete_local_settings():
    """Test that the local settings file "settings.json" can be safely removed."""
    with tempfile.TemporaryDirectory() as temp:
        temp_settings_file = Path(temp, "settings.json")
        assert not temp_settings_file.exists()
        temp_settings_file.touch()
        assert temp_settings_file.exists()
        delete_local_settings(temp)
        assert not temp_settings_file.exists()
        # Delete does not raise an error if the settings file is not present
        delete_local_settings(temp)


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
    mock.assert_called_once_with("General/editor_fontsize", 9)

    mock.reset_mock()
    settings = Settings(editor_fontsize=18, terminal_fontsize=3)
    settings.set_global_settings()
    mock.assert_any_call("General/editor_fontsize", 18)
    mock.assert_any_call("Terminal/terminal_fontsize", 3)


@pytest.mark.parametrize(
    "recent_projects, path, expected",
    (
        (["proj1", "proj2", "proj3"], None, ["proj1", "proj2", "proj3"]),
        (["proj1", "proj2", "DELETED"], None, ["proj1", "proj2"]),
        (["proj1", "proj2", "proj3"], "proj2", ["proj2", "proj1", "proj3"]),
    ),
)
@patch("rascal2.core.settings.QtCore.QSettings.setValue")
def test_update_recent_projects(set_val_mock, recent_projects, path, expected):
    """The recent projects should be updated to be newest to oldest with no deleted projects."""
    with tempfile.TemporaryDirectory() as temp:
        for proj in ["proj1", "proj2", "proj3"]:
            Path(temp, proj).touch()

        recent_projects = [str(Path(temp, proj)) for proj in recent_projects]
        expected = [str(Path(temp, proj)) for proj in expected]

        with patch("rascal2.core.settings.QtCore.QSettings.value", return_value=recent_projects):
            if path is not None:
                assert expected == update_recent_projects(str(Path(temp, path)))
            else:
                assert expected == update_recent_projects()
