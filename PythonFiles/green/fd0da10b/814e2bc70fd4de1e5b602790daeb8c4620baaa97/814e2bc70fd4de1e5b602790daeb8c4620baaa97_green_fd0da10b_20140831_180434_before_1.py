from __future__ import unicode_literals
from __future__ import print_function

from unittest.signals import registerResult, installHandler
import warnings

try: # pragma: no cover
    import coverage
except: # pragma: no cover
    coverage = None

from green.loader import toProtoTestList
from green.output import GreenStream
from green.result import GreenTestResult
from green.subprocess import LoggingDaemonlessPool, poolRunner



def run(suite, stream, args):
    """
    Run the given test case or test suite with the specified arguments.

    Any args.stream passed in will be wrapped in a GreenStream
    """
    if not issubclass(GreenStream, type(stream)):
        stream = GreenStream(stream)
    result = GreenTestResult(
            stream, args.verbose, html=args.html,
            termcolor=args.termcolor)
    installHandler()
    registerResult(result)
    with warnings.catch_warnings():
        if args.warnings:
            # if args.warnings is set, use it to filter all the warnings
            warnings.simplefilter(args.warnings)
            # if the filter is 'default' or 'always', special-case the
            # warnings from the deprecated unittest methods to show them
            # no more than once per module, because they can be fairly
            # noisy.  The -Wd and -Wa flags can be used to bypass this
            # only when args.warnings is None.
            if args.warnings in ['default', 'always']:
                warnings.filterwarnings('module',
                        category=DeprecationWarning,
                        message='Please use assert\w+ instead.')

        result.startTestRun()

        if args.subprocesses == 1:
            suite.run(result)
        else:
            tests = toProtoTestList(suite)
            pool = LoggingDaemonlessPool(processes=args.subprocesses)
            if tests:
                async_responses = []
                for index, test in enumerate(tests):
                    if args.run_coverage:
                        coverage_number = index + 1
                    else:
                        coverage_number = None
                    async_responses.append(pool.apply_async(
                        poolRunner,
                        (test.dotted_name, coverage_number, args.omit)))
                pool.close()
                for test, async_response in zip(tests, async_responses):
                    # Prints out the white 'processing...' version of the output
                    result.startTest(test)
                    # This blocks until the worker who is processing this
                    # particular test actually finishes
                    result.addProtoTestResult(async_response.get())
            pool.terminate()
            pool.join()

        result.stopTestRun()

    return result