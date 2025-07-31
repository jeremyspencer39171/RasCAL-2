import logging
import os

os.environ["DELAY_MATLAB_START"] = "1"
import multiprocessing as mp
import pathlib
import platform
import site
import sys

from rascal2.settings import Settings, get_global_settings

if getattr(sys, "frozen", False):
    # we are running in a bundle
    SOURCE_PATH = pathlib.Path(sys.executable).parent.parent
else:
    SOURCE_PATH = pathlib.Path(__file__).parent
STATIC_PATH = SOURCE_PATH / "static"
IMAGES_PATH = STATIC_PATH / "images"

if not getattr(sys, "frozen", False):
    site_path = site.getsitepackages()[-1]
else:
    site_path = SOURCE_PATH / "bin/_internal"
MATLAB_ARCH_FILE = pathlib.Path(site_path) / "matlab/engine/_arch.txt"


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


def setup_settings(project_path: str | os.PathLike) -> Settings:
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


def setup_logging(log_path: str | os.PathLike, terminal, level: int = logging.INFO) -> logging.Logger:
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


def run_matlab(ready_event, close_event, engine_output):
    """Start a new matlab engine instance and waits until closed

    Parameters
    ----------
    ready_event : multiprocessing.Event
        An event to inform listeners that MATLAB is ready.
    close_event : multiprocessing.Event
        An event to inform this function that MATLAB should be closed.
    engine_output : multiprocessing.Manager.list
        A list to output the name of MATLAB engine instance or an exception.

    """
    try:
        import matlab.engine

        eng = matlab.engine.start_matlab()
        eng.matlab.engine.shareEngine(nargout=0)
        engine_output.append(eng.matlab.engine.engineName(nargout=1).encode("utf-8"))
    except Exception as ex:
        engine_output.append(ex)
        raise ex
    ready_event.set()
    close_event.wait()

    eng.fclose("all", nargout=0)
    eng.close("all", nargout=0)
    eng.quit()


def get_matlab_engine(engine_ready, engine_output, is_local=False):
    """Get a MATLAB engine from the MatlabHelper or exception if no engine is available

    Parameters
    ----------
    engine_ready : multiprocessing.Event
        An event to inform listeners that MATLAB is ready.
    engine_output :  multiprocessing.Manager.list
        A list with the name of MATLAB engine instance or an exception from the MatlabHelper.
    is_local : bool, default False
        Indicates a local engine should be created other connect ratapi.

    Returns
    -------
    output : Union[matlab.engine.futureresult.FutureResult, Exception]
        MATLAB engine future or Exception from MatlabHelper
    """
    if not engine_output:
        engine_ready.wait(timeout=60)

    if engine_output:
        if isinstance(engine_output[0], bytes):
            engine_name = engine_output[0].decode("utf-8")
            if is_local:
                import matlab.engine

                engine_future = matlab.engine.connect_matlab(engine_name, background=True)
            else:
                import ratapi

                engine_future = ratapi.wrappers.use_shared_matlab(
                    engine_name,
                    "Error occurred when connecting to MATLAB, please ensure MATLAB is installed and set up properly.",
                )

            return engine_future
        elif isinstance(engine_output[0], Exception):
            return engine_output[0]
    else:
        return Exception("Matlab could not be started!")


class MatlabHelper:
    """Helper to start MATLAB on another process"""

    def __init__(self):
        self.error = ""
        self.ready_event = mp.Event()
        self.close_event = mp.Event()
        self.engine_output = None

        self.__engine = None

    def async_start(self):
        """Start MATLAB on a new process"""
        if not self.get_matlab_path():
            return
        self.manager = mp.Manager()
        self.engine_output = self.manager.list()
        self.process = mp.Process(
            target=run_matlab,
            args=(
                self.ready_event,
                self.close_event,
                self.engine_output,
            ),
        )
        self.process.daemon = False
        self.process.start()

    def shutdown(self):
        """Set close event to the MATLAB run function"""
        if not self.engine_output:
            self.ready_event.wait(timeout=60)
        self.close_event.set()

    def get_local_engine(self):
        """Get an instance of MATLAB engine for use on the main process.

        Returns
        -------
        matlab.engine.MatlabEngine
            MATLAB engine instance
        """
        if self.__engine is not None:
            return self.__engine

        result = get_matlab_engine(self.ready_event, self.engine_output, True)
        if isinstance(result, Exception):
            raise result

        self.__engine = result.result()
        return self.__engine

    def get_matlab_path(self):
        """Get MATLAB install directory

        Returns
        -------
        str
            Return MATLAB install directory.
        """
        install_dir = ""
        self.error = ""
        try:
            with open(MATLAB_ARCH_FILE) as path_file:
                lines = path_file.readlines()
                if len(lines) == 4:
                    install_dir = pathlib.Path(lines[1]).parent.parent
                elif len(lines) != 0:
                    self.error = "Matlab not found, use 'Tools > Setup Matlab' to specify MATLAB location "
        except FileNotFoundError:
            self.error = "Matlab engine could not be found, ensure it is installed properly"
        if self.error:
            logger = logging.getLogger("rascal_log")
            logger.error(f"{self.error}. Attempt to read MATLAB _arch file failed {MATLAB_ARCH_FILE}.")
        return str(install_dir)


mp.set_start_method("spawn", force=True)
MATLAB_HELPER = MatlabHelper()
