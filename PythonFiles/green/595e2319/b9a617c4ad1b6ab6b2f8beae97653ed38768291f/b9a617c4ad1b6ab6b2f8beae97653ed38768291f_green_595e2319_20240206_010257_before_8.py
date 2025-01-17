from __future__ import annotations

import argparse
import multiprocessing
from sys import modules
from typing import TYPE_CHECKING
from unittest.signals import registerResult, installHandler, removeResult
import warnings

from green.exceptions import InitializerOrFinalizerError
from green.loader import toParallelTargets
from green.output import debug, GreenStream
from green.process import LoggingDaemonlessPool, poolRunner
from green.result import GreenTestResult, ProtoTestResult

if TYPE_CHECKING:
    from multiprocessing.managers import SyncManager
    from queue import Queue


class InitializerOrFinalizer:
    """
    I represent a command that will be run as either the initializer or the
    finalizer for a worker process.  The only reason I'm a class instead of a
    function is so that I can be instantiated at the creation time of the Pool
    (with the user's customized command to run), but actually run at the
    appropriate time.
    """

    def __init__(self, dotted_function):
        self.module_part = ".".join(dotted_function.split(".")[:-1])
        self.function_part = ".".join(dotted_function.split(".")[-1:])

    def __call__(self, *args):
        if not self.module_part:
            return
        try:
            __import__(self.module_part)
            loaded_function = getattr(
                modules[self.module_part], self.function_part, None
            )
        except Exception as e:
            raise InitializerOrFinalizerError(
                f"Couldn't load '{self.function_part}' - got: {str(e)}"
            )
        if not loaded_function:
            raise InitializerOrFinalizerError(
                "Loaded module '{}', but couldn't find function '{}'".format(
                    self.module_part, self.function_part
                )
            )
        try:
            loaded_function()
        except Exception as e:
            raise InitializerOrFinalizerError(
                f"Error running '{self.function_part}' - got: {str(e)}"
            )


def run(
    suite, stream, args: argparse.Namespace, testing: bool = False
) -> GreenTestResult:
    """
    Run the given test case or test suite with the specified arguments.

    Any args.stream passed in will be wrapped in a GreenStream
    """
    if not issubclass(GreenStream, type(stream)):
        stream = GreenStream(
            stream,
            disable_windows=args.disable_windows,
            disable_unidecode=args.disable_unidecode,
        )
    result = GreenTestResult(args, stream)

    # Note: Catching SIGINT isn't supported by Python on windows (python
    # "WONTFIX" issue 18040)
    installHandler()
    # Ignore the type mismatch until we make GreenTestResult a subclass of unittest.TestResult.
    registerResult(result)  # type: ignore

    with warnings.catch_warnings():
        if args.warnings:  # pragma: no cover
            # if args.warnings is set, use it to filter all the warnings
            warnings.simplefilter(args.warnings)
            # if the filter is 'default' or 'always', special-case the
            # warnings from the deprecated unittest methods to show them
            # no more than once per module, because they can be fairly
            # noisy.  The -Wd and -Wa flags can be used to bypass this
            # only when args.warnings is None.
            if args.warnings in ["default", "always"]:
                warnings.filterwarnings(
                    "module",
                    category=DeprecationWarning,
                    message=r"Please use assert\w+ instead.",
                )

        result.startTestRun()

        # The call to toParallelTargets needs to happen before pool stuff so we can crash if there
        # are, for example, syntax errors in the code to be loaded.
        parallel_targets = toParallelTargets(suite, args.targets)
        pool = LoggingDaemonlessPool(
            processes=args.processes or None,
            initializer=InitializerOrFinalizer(args.initializer),
            finalizer=InitializerOrFinalizer(args.finalizer),
            maxtasksperchild=args.maxtasksperchild,
        )
        manager: SyncManager = multiprocessing.Manager()
        targets: list[tuple[str, Queue]] = [
            (target, manager.Queue()) for target in parallel_targets
        ]
        if targets:
            for index, (target, queue) in enumerate(targets):
                if args.run_coverage:
                    coverage_number = index + 1
                else:
                    coverage_number = None
                debug(f"Sending {target} to poolRunner {poolRunner}")
                pool.apply_async(
                    poolRunner,
                    (
                        target,
                        queue,
                        coverage_number,
                        args.omit_patterns,
                        args.cov_config_file,
                    ),
                )
            pool.close()
            for target, queue in targets:
                abort = False

                while True:
                    msg = queue.get()

                    # Sentinel value, we're done
                    if not msg:
                        debug("runner.run(): received sentinal, breaking.", 3)
                        break
                    else:
                        debug(f"runner.run(): start test: {msg}")
                        # Result guaranteed after this message, we're
                        # currently waiting on this test, so print out
                        # the white 'processing...' version of the output
                        result.startTest(msg)
                        proto_test_result: ProtoTestResult = queue.get()
                        debug(
                            "runner.run(): received proto test result: {}".format(
                                str(proto_test_result)
                            ),
                            3,
                        )
                        result.addProtoTestResult(proto_test_result)

                    if result.shouldStop:
                        debug("runner.run(): shouldStop encountered, breaking", 3)
                        abort = True
                        break

                if abort:
                    break

        pool.close()
        pool.join()

        result.stopTestRun()

    # Ignore the type mismatch untile we make GreenTestResult a subclass of unittest.TestResult.
    removeResult(result)  # type: ignore

    return result
