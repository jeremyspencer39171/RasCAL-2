from rascal2.ui.model import MainWindowModel


def test_create_project():
    model = MainWindowModel()
    assert model.project is None
    assert model.controls is None
    assert model.results is None
    assert model.save_path == ""

    model.create_project("Test", "C:/test")

    assert model.project.name == "Test"
    assert model.controls is not None
    assert model.results is None
    assert model.save_path == "C:/test"
