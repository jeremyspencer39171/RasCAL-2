import logging
import pathlib
import platform
import sys
from os import PathLike

from rascal2.core import Settings, get_global_settings

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


def setup_logging(log_path: str | PathLike, terminal, level: int = logging.INFO) -> logging.Logger:
    """Set up logging for the project.

    The default logging path and level are defined in the settings.

    Parameters
    ----------
    log_path : str | PathLike
        The path to where the log file will be written.
    terminal : TerminalWidget
        The TerminalWidget instance which acts as an IO stream.
    level : int, default logging.INFO
        The debug level for the logger.

    """
    path = pathlib.Path(log_path)
    logger = logging.getLogger("rascal_log")
    logger.setLevel(level)
    logger.handlers.clear()

    log_filehandler = logging.FileHandler(path)
    file_formatting = logging.Formatter("%(asctime)s - %(threadName)s -  %(name)s - %(levelname)s - %(message)s")
    log_filehandler.setFormatter(file_formatting)
    logger.addHandler(log_filehandler)

    # handler that logs to terminal widget
    log_termhandler = logging.StreamHandler(stream=terminal)
    term_formatting = logging.Formatter("%(levelname)s - %(message)s")
    log_termhandler.setFormatter(term_formatting)
    logger.addHandler(log_termhandler)

    return logger


def get_logger():
    """Get the RasCAL logger, and set up a backup logger if it hasn't been set up yet."""
    logger = logging.getLogger("rascal_log")
    if not logger.handlers:
        # Backup in case the crash happens before the local logger setup
        path = pathlib.Path(get_global_settings().fileName()).parent
        path.mkdir(parents=True, exist_ok=True)
        logger.addHandler(logging.FileHandler(path / "rascal.log"))

    return logger


def log_uncaught_exceptions(exc_type, exc_value, exc_traceback):
    """Qt slots swallows exceptions but this ensures exceptions are logged"""
    logger = get_logger()
    logger.addHandler(logging.StreamHandler(stream=sys.stderr))  # print emergency crashes to terminal
    logger.critical("An unhandled exception occurred!", exc_info=(exc_type, exc_value, exc_traceback))
    logging.shutdown()
    sys.exit(1)
