"""Dialogs for editing custom files."""

import logging
from pathlib import Path

from PyQt6 import Qsci, QtGui, QtWidgets
from ratapi.utils.enums import Languages

from rascal2.config import MATLAB_HELPER


def edit_file(filename: str, language: Languages, parent: QtWidgets.QWidget):
    """Edit a file in the file editor.

    Parameters
    ----------
    filename : str
        The name of the file to edit.
    language : Languages
        The language for dialog highlighting.
    parent : QtWidgets.QWidget
        The parent of this widget.

    """
    file = Path(filename)
    if not file.is_file():
        logger = logging.getLogger("rascal_log")
        logger.error("Attempted to edit a custom file which does not exist!")
        return

    dialog = CustomFileEditorDialog(file, language, parent)
    dialog.exec()


def edit_file_matlab(filename: str):
    """Open a file in MATLAB."""
    try:
        engine = MATLAB_HELPER.get_local_engine()
    except Exception as ex:
        logger = logging.getLogger("rascal_log")
        logger.error("Attempted to edit a file in MATLAB engine" + repr(ex))
        return

    engine.edit(str(filename))


class CustomFileEditorDialog(QtWidgets.QDialog):
    """Dialog for editing custom files.

    Parameters
    ----------
    file : pathlib.Path
        The file to edit.
    language : Languages
        The language for dialog highlighting.
    parent : QtWidgets.QWidget
        The parent of this widget.

    """

    def __init__(self, file, language, parent):
        super().__init__(parent)

        self.file = file

        self.editor = Qsci.QsciScintilla()
        self.editor.setBraceMatching(Qsci.QsciScintilla.BraceMatch.SloppyBraceMatch)
        self.editor.setCaretLineVisible(True)
        self.editor.setCaretLineBackgroundColor(QtGui.QColor("#cccccc"))
        self.editor.setScrollWidth(1)
        self.editor.setEolMode(Qsci.QsciScintilla.EolMode.EolUnix)
        self.editor.setScrollWidthTracking(True)
        self.editor.setFolding(Qsci.QsciScintilla.FoldStyle.PlainFoldStyle)
        self.editor.setIndentationsUseTabs(False)
        self.editor.setIndentationGuides(True)
        self.editor.setAutoIndent(True)
        self.editor.setTabWidth(4)

        match language:
            case Languages.Python:
                self.editor.setLexer(Qsci.QsciLexerPython(self.editor))
            case Languages.Matlab:
                self.editor.setLexer(Qsci.QsciLexerMatlab(self.editor))
            case _:
                self.editor.setLexer(None)

        # Set the default font
        font = QtGui.QFont("Courier", 10)
        font.setFixedPitch(True)
        self.editor.setFont(font)

        # Margin 0 is used for line numbers
        font_metrics = QtGui.QFontMetrics(font)
        self.editor.setMarginsFont(font)
        self.editor.setMarginWidth(0, font_metrics.horizontalAdvance("00000") + 6)
        self.editor.setMarginLineNumbers(0, True)
        self.editor.setMarginsBackgroundColor(QtGui.QColor("#cccccc"))

        if self.editor.lexer() is not None:
            self.editor.lexer().setFont(font)
        self.editor.setText(self.file.read_text())

        save_button = QtWidgets.QPushButton("Save", self)
        save_button.clicked.connect(self.save_file)
        cancel_button = QtWidgets.QPushButton("Cancel", self)
        cancel_button.clicked.connect(self.reject)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.editor)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setWindowTitle(f"Edit {str(file)}")

    def save_file(self):
        """Save and close the file."""
        self.file.write_text(self.editor.text())
        self.accept()
