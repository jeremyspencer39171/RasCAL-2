from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest
from RATapi import Controls

from rascal2.ui.model import MainWindowModel


def test_create_project():
    """The project should be set up with the desired name and default objets when a new project is created."""
    model = MainWindowModel()
    assert model.project is None
    assert model.controls is None
    assert model.results is None
    assert model.save_path == ""

    model.create_project("Test", "C:/test")

    assert model.project.name == "Test"
    assert model.controls == Controls()
    assert model.results is None
    assert model.save_path == "C:/test"


def test_save_project():
    model = MainWindowModel()
    model.controls = Controls(procedure="dream", resampleMinAngle=0.5)
    with TemporaryDirectory() as tmpdir:
        model.save_path = tmpdir
        model.save_project()

        controls = Path(tmpdir, "controls.json").read_text()

    assert '"resampleMinAngle":0.5' in controls
    assert '"procedure":"dream"' in controls


def test_load_project():
    """The load function should load the correct controls object from JSON."""
    model = MainWindowModel()

    with TemporaryDirectory() as tmpdir:
        Path(tmpdir, "controls.json").write_text('{"procedure":"dream","resampleMinAngle":0.5}')
        model.load_project(tmpdir)

    assert model.controls == Controls(procedure="dream", resampleMinAngle=0.5)


@patch("RATapi.utils.convert.r1_to_project_class")
def test_load_r1_project(mock_r1_class):
    """load_r1_project should call the conversion function and set the path correctly."""
    model = MainWindowModel()
    model.load_r1_project("test_path/r1project.mat")

    mock_r1_class.assert_called_once()
    assert model.save_path == "test_path"


@pytest.mark.parametrize("bad_json", ['{"field1":3', '{"procedure":"fry eggs"}'])
def test_load_project_error(bad_json):
    """The project load function should raise an error if the controls JSON is invalid or the parameters are invalid."""
    model = MainWindowModel()

    with pytest.raises(  # noqa (for nested with's: pytest.raises breaks if not by itself)
        ValueError,
        match="The controls.json file for this project is not valid.\n"
        "It may contain invalid parameter values or be invalid JSON.",
    ):
        with TemporaryDirectory() as tmpdir:
            Path(tmpdir, "controls.json").write_text(bad_json)
            model.load_project(tmpdir)
