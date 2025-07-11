import multiprocessing
import re
import sys
from contextlib import suppress

from PyQt6 import QtGui, QtWidgets

from rascal2.config import IMAGES_PATH, MATLAB_HELPER, STATIC_PATH, handle_scaling, log_uncaught_exceptions, path_for
from rascal2.ui.view import MainWindowView


def ui_execute():
    """Creates main window and executes GUI event loop

    Returns
    -------
    exit code : int
        QApplication exit code
    """
    handle_scaling()
    QtWidgets.QApplication.setStyle("Fusion")
    app = QtWidgets.QApplication(sys.argv[:1])
    app.setWindowIcon(QtGui.QIcon(path_for("logo.png")))
    with suppress(FileNotFoundError), open(STATIC_PATH / "style.css") as stylesheet:
        palette = app.palette()
        replacements = {
            "@Path": IMAGES_PATH.as_posix(),
            "@Base": palette.base().color().name(),
            "@Window": palette.window().color().name(),
            "@Accent": palette.accent().color().name(),
            "@Midlight": palette.midlight().color().name(),
            "@Text": palette.text().color().name(),
        }
        style = re.sub("|".join(replacements), lambda x: replacements[x.group(0)], stylesheet.read())
        app.setStyleSheet(style)

    window = MainWindowView()
    window.show()
    return app.exec()


def main():
    multiprocessing.freeze_support()
    sys.excepthook = log_uncaught_exceptions
    MATLAB_HELPER.async_start()
    exit_code = ui_execute()
    MATLAB_HELPER.shutdown()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
