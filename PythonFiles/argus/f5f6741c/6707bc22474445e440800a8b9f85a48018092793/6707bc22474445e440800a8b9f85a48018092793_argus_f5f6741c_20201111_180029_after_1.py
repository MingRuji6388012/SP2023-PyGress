"""Events, State and Engine in the current file are highly inspired by
pytorch-ignite (https://github.com/pytorch/ignite).
"""

import logging
from enum import Enum
from collections import defaultdict
from typing import Callable, Optional, Iterable, Dict, Any


class EventEnum(Enum):
    """Base class for engine events. User defined custom events should also
    inherit this class. Example of creating custom events you can find
    `here <https://github.com/lRomul/argus/blob/master/examples/custom_events.py>`_.
    """
    pass


class Events(EventEnum):
    """Events that are fired by the :class:`argus.engine.Engine` during running.

    Built-in events:

    - START : trigger callback method ``start`` on start of engine's run.
    - COMPLETE : trigger callback method ``complete`` on end of engine's run.
    - EPOCH_START : trigger callback method ``epoch_start`` on start of the epoch.
    - EPOCH_COMPLETE : trigger callback method ``epoch_complete`` on end of the epoch.
    - ITERATION_START : trigger callback method ``iteration_start`` on start of the iteration.
    - ITERATION_COMPLETE : trigger callback method ``iteration_complete`` on end of the iteration.
    - CATCH_EXCEPTION : trigger callback method ``catch_exception`` on catching of exception.
    """

    START = "start"
    COMPLETE = "complete"
    EPOCH_START = "epoch_start"
    EPOCH_COMPLETE = "epoch_complete"
    ITERATION_START = "iteration_start"
    ITERATION_COMPLETE = "iteration_complete"
    CATCH_EXCEPTION = "catch_exception"


class State:
    """A state used to store internal and user-defined variables during a run
    of :class:`argus.engine.Engine`. The class is highly inspired by State from
    `pytorch-ignite <https://github.com/pytorch/ignite>`_.

    By default, the state contains the following attributes.

    Attributes:
        iteration (int, optional): Iteration, the first iteration is 0.
        epoch (int, optional): Epoch, the first iteration is 0.
        model (:class:`argus.Model`): :class:`argus.Model` that uses
            :attr:`argus.engine.State.engine` and this object of state.
        data_loader (Iterable, optional): A data passed to the
            :class:`argus.engine.Engine`.
        logger (logging.Logger, optional): Logger.
        exception (BaseException, optional): Catched exception.
        engine (Engine, optional): :class:`argus.engine.Engine` that uses this
            object of state.
        phase (str): A phase of training ``{"", "train", "test"}`` this state
            was created for.
        batch (Any): Batch took from a data loader on the current iteration.
        step_output (Any): Current output from `step_function` on current
            iteration.
        metrics (Dict[str, float]): Dictionary with metrics values.
        stopped (bool): Boolean indicates :class:`argus.engine.Engine` is
            stopped or not.

    """

    def __init__(self, **kwargs):
        """
        Args:
            **kwargs: Init attributes using kwargs.
        """
        self.iteration: Optional[int] = None
        self.epoch: Optional[int] = None
        self.model: Optional['argus.model.Model'] = None
        self.data_loader: Optional[Iterable] = None
        self.logger: Optional[logging.Logger] = None
        self.exception: Optional[BaseException] = None
        self.engine: Optional[Engine] = None
        self.phase: str = ""

        self.batch: Any = None
        self.step_output: Any = None

        self.metrics: Dict[str, float] = dict()
        self.stopped: bool = True

        self.update(**kwargs)

    def update(self, **kwargs):
        """
        Args:
            **kwargs: Update attributes using kwargs
        """
        for key, value in kwargs.items():
            setattr(self, key, value)


class Engine:
    def __init__(self, step_function: Callable, **kwargs):
        self.event_handlers = defaultdict(list)
        self.step_function = step_function
        self.state = State(
            step_function=step_function,
            engine=self,
            **kwargs
        )

    def add_event_handler(self, event: EventEnum, handler: Callable, *args, **kwargs):
        if not isinstance(event, EventEnum):
            raise TypeError(f"Event should be 'argus.engine.EventEnum' enum")

        self.event_handlers[event].append((handler, args, kwargs))

    def raise_event(self, event: EventEnum):
        if not isinstance(event, EventEnum):
            raise TypeError(f"Event should be 'argus.engine.EventEnum' enum")

        if event in self.event_handlers:
            for handler, args, kwargs in self.event_handlers[event]:
                handler(self.state, *args, **kwargs)

    def run(self, data_loader: Iterable, start_epoch=0, end_epoch=1) -> State:
        self.state.update(data_loader=data_loader,
                          epoch=start_epoch,
                          iteration=0,
                          stopped=False)

        try:
            self.raise_event(Events.START)
            while self.state.epoch < end_epoch and not self.state.stopped:
                self.state.iteration = 0
                self.state.metrics = dict()
                self.raise_event(Events.EPOCH_START)

                for batch in data_loader:
                    self.state.batch = batch
                    self.raise_event(Events.ITERATION_START)
                    self.state.step_output = self.step_function(batch, self.state)
                    self.raise_event(Events.ITERATION_COMPLETE)
                    self.state.step_output = None
                    if self.state.stopped:
                        break
                    self.state.iteration += 1

                self.raise_event(Events.EPOCH_COMPLETE)
                self.state.epoch += 1

            self.raise_event(Events.COMPLETE)

        except BaseException as exception:
            if self.state.logger is not None:
                self.state.logger.exception(exception)

            self.state.exception = exception
            self.raise_event(Events.CATCH_EXCEPTION)
            raise exception
        finally:
            self.state.stopped = True

        return self.state