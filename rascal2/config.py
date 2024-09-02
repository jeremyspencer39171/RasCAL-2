import logging
import pathlib
import platform
from os import PathLike

from rascal2.core import Settings

SOURCE_PATH = pathlib.Path(__file__).parent
STATIC_PATH = SOURCE_PATH / "static"
IMAGES_PATH = STATIC_PATH / "images"


def handle_scaling():
    """Changes settings to handle UI scaling"""
    if platform.system() == "Windows":
        from ctypes import windll

        windll.user32.SetProcessDPIAware()


def path_for(filename: str):
    """Gets full path for the given image file.

    Parameters
    ----------
    filename : str
        basename and extension of image.

    Returns
    -------
    full path : str
        full path of the image.
    """
    return (IMAGES_PATH / filename).as_posix()


def setup_settings(project_path: str | PathLike) -> Settings:
    """Set up the Settings object for the project.

    Parameters
    ----------
    project_path : str or PathLike
        The path to the current RasCAL-2 project.

    Returns
    -------
    Settings
        If a settings.json file already exists in the
        RasCAL-2 project, returns a Settings object with
        the settings defined there. Otherwise, returns a
        (global) default Settings object.

    """
    filepath: pathlib.Path = pathlib.Path(project_path, "settings.json")
    if filepath.is_file():
        json = filepath.read_text()
        return Settings.model_validate_json(json)
    return Settings()


def setup_logging(log_path: str | PathLike, level: int = logging.INFO) -> logging.Logger:
    """Set up logging for the project.

    The default logging path and level are defined in the settings.

    Parameters
    ----------
    log_path : str | PathLike
        The path to where the log file will be written.
    level : int, default logging.INFO
        The debug level for the logger.

    """
    path = pathlib.Path(log_path)
    logger = logging.getLogger(path.stem)
    logger.setLevel(level)

    # TODO add console print handler when console is added
    log_filehandler = logging.FileHandler(path)
    logger.addHandler(log_filehandler)

    return logger
