import pytest
from PyQt6.QtWidgets import QApplication

APP = QApplication([])


@pytest.fixture
def qt_application():
    return APP
