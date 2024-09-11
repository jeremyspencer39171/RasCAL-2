"""Tests for the Controls widget."""

from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel, Field
from PyQt6 import QtWidgets
from RATapi.controls import Controls, fields

from rascal2.widgets.controls import ControlsWidget, FitSettingsWidget


class MockWindowView(QtWidgets.QMainWindow):
    """A mock MainWindowView class."""

    def __init__(self):
        super().__init__()
        self.presenter = MagicMock()
        self.presenter.model = MagicMock()
        self.presenter.model.controls = Controls()


view = MockWindowView()


@pytest.fixture
def controls_widget() -> ControlsWidget:
    def _widget():
        widget = ControlsWidget(view)
        widget.setup_controls()
        return widget

    return _widget


class MockControls(BaseModel, validate_assignment=True):
    """A mock Pydantic model with validation."""

    set_1: bool = True
    set_2: float = Field(default=3.0, gt=0)
    set_3: str = Field(default="eggs", max_length=6)


class MockPresenter:
    """A mock Presenter for accessing MockControls."""

    def __init__(self):
        self.model = MagicMock()
        self.model.controls = MockControls()
        self.terminal_interrupted = False

    def edit_controls(self, setting, value):
        setattr(self.model.controls, setting, value)

    def interrupt_terminal(self):
        self.terminal_interrupted = True


def test_toggle_fit(controls_widget):
    """Test that fit settings are hidden when the button is toggled."""
    wg = controls_widget()
    assert wg.fit_settings.isVisibleTo(wg)
    wg.fit_settings_button.toggle()
    assert not wg.fit_settings.isVisibleTo(wg)
    wg.fit_settings_button.toggle()
    assert wg.fit_settings.isVisibleTo(wg)


def test_toggle_run_disables(controls_widget):
    """Assert that Controls settings are disabled and Stop button enabled when the run button is pressed."""
    wg = controls_widget()
    assert wg.fit_settings.isEnabled()
    assert wg.procedure_dropdown.isEnabled()
    assert not wg.stop_button.isEnabled()
    wg.run_button.toggle()
    assert not wg.fit_settings.isEnabled()
    assert not wg.procedure_dropdown.isEnabled()
    assert wg.stop_button.isEnabled()
    wg.run_button.toggle()
    assert wg.fit_settings.isEnabled()
    assert wg.procedure_dropdown.isEnabled()
    assert not wg.stop_button.isEnabled()


def test_stop_button_interrupts(controls_widget):
    """Test that an interrupt signal is sent to the presenter when Stop is pressed."""
    wg = controls_widget()
    wg.run_button.toggle()
    wg.stop_button.click()
    assert wg.presenter.terminal_interrupted


@pytest.mark.parametrize("procedure", ["calculate", "simplex", "de", "ns", "dream"])
def test_procedure_select(controls_widget, procedure):
    """Test that the procedure selector correctly changes the widget."""
    wg = controls_widget()
    wg.procedure_dropdown.setCurrentText(procedure)
    current_fit_set = wg.fit_settings_layout.currentWidget()
    for setting in fields[procedure]:
        if setting not in ["procedure"]:
            assert setting in list(current_fit_set.rows.keys())


@pytest.mark.parametrize("settings", (["set_1", "set_2", "set_3"], ["set_1", "set_3"], ["set_2"]))
def test_create_fit_settings(settings):
    """Test that fit settings are correctly created from the model's dataset."""
    wg = FitSettingsWidget(None, settings, MockPresenter())
    grid = wg.layout().itemAt(0).widget().widget().layout()
    for i, setting in enumerate(settings):
        assert grid.itemAtPosition(2 * i, 0).widget().text() == setting
        assert grid.itemAtPosition(2 * i, 1).widget().get_data() == getattr(wg.presenter.model.controls, setting)


def test_get_controls_data():
    """Test that the Controls data is correctly retrieved."""
    wg = FitSettingsWidget(None, ["set_1", "set_2", "set_3"], MockPresenter())
    fields = wg.get_controls_attribute("model_fields").keys()
    values = [getattr(wg.presenter.model.controls, field) for field in fields]
    assert [wg.get_controls_attribute(field) for field in fields] == values


@pytest.mark.parametrize(
    ("fit_setting", "bad_input", "error"),
    (("set_2", 0, "greater than 0"), ("set_3", "longstring", "at most 6 characters")),
)
def test_invalid_input(fit_setting, bad_input, error):
    """Test that invalid inputs are propagated correctly."""
    wg = FitSettingsWidget(None, [fit_setting], MockPresenter())
    grid = wg.layout().itemAt(0).widget().widget().layout()
    entry = grid.itemAtPosition(0, 1).widget()

    entry.set_data(bad_input)
    entry.editor.editingFinished.emit()

    validation_box = grid.itemAtPosition(1, 1).widget()
    assert error in validation_box.text()


@pytest.mark.parametrize("bad_settings", [["set_2"], ["set_3"], ["set_2", "set_3"]])
def test_invalid_data_run(controls_widget, bad_settings):
    """Tests that the widget refuses to run if values have invalid data."""
    wg = controls_widget()
    fit_tab = FitSettingsWidget(None, ["set_1", "set_2", "set_3"], MockPresenter())
    fit_lay = QtWidgets.QStackedLayout()
    fit_lay.addWidget(fit_tab)
    fit_wg = QtWidgets.QWidget()
    fit_wg.setLayout(fit_lay)

    wg.fit_settings_layout = fit_lay
    wg.fit_settings = fit_wg
    # index and bad value of settings
    bad_settings_data = {"set_2": (2, 0), "set_3": (4, "longstring")}

    fit_tab.presenter.allow_setting = False
    grid = fit_tab.layout().itemAt(0).widget().widget().layout()
    for setting in bad_settings:
        index, val = bad_settings_data[setting]
        entry = grid.itemAtPosition(index, 1).widget()
        entry.set_data(val)
        entry.editor.editingFinished.emit()

    for setting in bad_settings:
        assert setting in fit_tab.get_invalid_inputs()

    wg.run_button.toggle()
    assert not wg.stop_button.isEnabled()  # to assert run hasn't started
    for setting in bad_settings:
        assert setting in wg.validation_label.text()
