"""QObject for running rat."""

from dataclasses import dataclass
from logging import INFO
from multiprocessing import Process, Queue

import ratapi as rat
from PyQt6 import QtCore
from ratapi.utils.enums import Procedures

from rascal2.config import MATLAB_HELPER, get_matlab_engine


class RATRunner(QtCore.QObject):
    """Class for running rat."""

    event_received = QtCore.pyqtSignal()
    finished = QtCore.pyqtSignal()
    stopped = QtCore.pyqtSignal()

    def __init__(self, rat_inputs, procedure: Procedures, display_on: bool):
        super().__init__()
        self.timer = QtCore.QTimer()
        self.timer.setInterval(1)
        self.timer.timeout.connect(self.check_queue)

        # this queue handles both event data and results
        self.queue = Queue()
        self.process = Process(
            target=run,
            args=(
                self.queue,
                rat_inputs,
                procedure,
                display_on,
                MATLAB_HELPER.ready_event,
                MATLAB_HELPER.engine_output,
            ),
        )

        self.updated_problem = None
        self.results = None
        self.error = None
        self.events = []

    def start(self):
        """Start the calculation."""
        self.process.start()
        self.timer.start()

    def interrupt(self):
        """Interrupt the running process."""
        self.timer.stop()
        self.process.kill()
        self.stopped.emit()

    def check_queue(self):
        """Check for new data in the queue."""
        if not self.process.is_alive():
            self.timer.stop()
        self.queue.put(None)
        for item in iter(self.queue.get, None):
            if isinstance(item, tuple):
                self.updated_problem, self.results = item
                self.finished.emit()
            elif isinstance(item, Exception):
                self.error = item
                self.stopped.emit()
            else:  # else, assume item is an event
                self.events.append(item)
                self.event_received.emit()


def run(queue, rat_inputs: tuple, procedure: str, display: bool, engine_ready, engine_output):
    """Run RAT and put the result into the queue.

    Parameters
    ----------
    queue : Queue
        The interprocess queue for the RATRunner.
    rat_inputs : tuple
        The C++ inputs for rat.
    procedure : str
        The optimisation procedure.
    display : bool
        Whether to display events.

    """
    problem_definition, cpp_controls = rat_inputs

    engine_future = None
    if any([file["language"] == "matlab" for file in problem_definition.customFiles.files]):
        result = get_matlab_engine(engine_ready, engine_output)
        if isinstance(result, Exception):
            queue.put(result)
            return
        else:
            engine_future = result

    if display:
        rat.events.register(rat.events.EventTypes.Message, queue.put)
        rat.events.register(rat.events.EventTypes.Progress, queue.put)
        rat.events.register(rat.events.EventTypes.Plot, queue.put)
        queue.put(LogData(INFO, "Starting RAT"))

    try:
        problem_definition, output_results, bayes_results = rat.rat_core.RATMain(problem_definition, cpp_controls)
        results = rat.outputs.make_results(procedure, output_results, bayes_results)
        if engine_future is not None:
            engine_future.result().exit()
    except Exception as err:
        queue.put(err)
        return

    if display:
        queue.put(LogData(INFO, "Finished RAT"))
        rat.events.clear()

    queue.put((problem_definition, results))


@dataclass
class LogData:
    """Dataclass for logging data."""

    level: int
    msg: str
