"""Tests for the custom file editor."""

import logging
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PyQt6 import Qsci, QtWidgets
from RATapi.utils.enums import Languages

from rascal2.dialogs.custom_file_editor import CustomFileEditorDialog, edit_file, edit_file_matlab

parent = QtWidgets.QMainWindow()


@pytest.fixture
def custom_file_dialog():
    """Fixture for a custom file dialog."""

    def _dialog(language, tmpdir):
        file = Path(tmpdir, "test_file")
        file.write_text("Test text for a test dialog!")
        dlg = CustomFileEditorDialog(file, language, parent)

        return dlg

    return _dialog


@patch("rascal2.dialogs.custom_file_editor.CustomFileEditorDialog.exec")
def test_edit_file(exec_mock):
    """Test that the dialog is executed when edit_file() is called on a valid file"""

    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp, "testfile.py")
        file.touch()
        edit_file(file, Languages.Python, parent)

        exec_mock.assert_called_once()


@pytest.mark.parametrize("filepath", ["dir/", "not_there.m"])
@patch("rascal2.dialogs.custom_file_editor.CustomFileEditorDialog")
def test_edit_incorrect_file(dialog_mock, filepath, caplog):
    """A logger error should be emitted if a directory or nonexistent file is given to the editor."""

    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp, filepath)
        edit_file(file, Languages.Python, parent)

    errors = [record for record in caplog.get_records("call") if record.levelno == logging.ERROR]
    assert len(errors) == 1
    assert "Attempted to edit a custom file which does not exist!" in caplog.text


def test_edit_file_matlab():
    """Assert that a file is passed to the engine when the MATLAB editor is called."""
    mock_engine = MagicMock()
    mock_engine.edit = MagicMock()
    mock_loader = MagicMock()
    mock_loader.result = MagicMock(return_value=mock_engine)
    with patch("rascal2.dialogs.custom_file_editor.start_matlab", return_value=mock_loader) as mock_start:
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp, "testfile.m")
            file.touch()
            edit_file_matlab(file)

        mock_start.assert_called_once()
        mock_loader.result.assert_called_once()
        mock_engine.edit.assert_called_once_with(str(file))


def test_edit_no_matlab_engine(caplog):
    """A logging error should be produced if a user tries to edit a file in MATLAB with no engine available."""
    with patch("rascal2.dialogs.custom_file_editor.start_matlab", return_value=None) as mock_loader:
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp, "testfile.m")
            file.touch()
            edit_file_matlab(file)
        mock_loader.assert_called_once()

    errors = [record for record in caplog.get_records("call") if record.levelno == logging.ERROR]
    assert len(errors) == 1
    assert "Attempted to edit a file in MATLAB engine, but `matlabengine` is not available." in caplog.text


@pytest.mark.parametrize(
    "language, expected_lexer",
    [(Languages.Python, Qsci.QsciLexerPython), (Languages.Matlab, Qsci.QsciLexerMatlab), (None, type(None))],
)
def test_dialog_init(custom_file_dialog, language, expected_lexer):
    """Ensure the custom file editor is set up correctly."""

    with tempfile.TemporaryDirectory() as tmp:
        dialog = custom_file_dialog(language, tmp)

    assert isinstance(dialog.editor.lexer(), expected_lexer)
    assert dialog.editor.text() == "Test text for a test dialog!"


def test_dialog_save(custom_file_dialog):
    """Text changes to the editor are saved to the file when save_file is called."""
    with tempfile.TemporaryDirectory() as tmp:
        dialog = custom_file_dialog(Languages.Python, tmp)

        dialog.editor.setText("New test text...")
        dialog.save_file()

        assert Path(tmp, "test_file").read_text() == "New test text..."
