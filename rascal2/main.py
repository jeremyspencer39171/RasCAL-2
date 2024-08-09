import multiprocessing
import sys

from PyQt6 import QtGui, QtWidgets

from rascal2.config import handle_scaling, path_for
from rascal2.ui.view import MainWindowView


def ui_execute():
    """Creates main window and executes GUI event loop

    Returns
    -------
    exit code : int
        QApplication exit code
    """
    handle_scaling()
    # TODO: Setup stylesheets
    app = QtWidgets.QApplication(sys.argv[:1])
    app.setWindowIcon(QtGui.QIcon(path_for("logo.png")))

    window = MainWindowView()
    window.show()
    return app.exec()


def main():
    multiprocessing.freeze_support()
    # TODO: Initialise Logging
    exit_code = ui_execute()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
