import atexit
import logging
import os
import shlex
import subprocess
import threading
import time

from future.standard_library import install_aliases

from pyngrok.exception import PyngrokNgrokError, PyngrokSecurityError

install_aliases()

from urllib.request import urlopen, Request

try:
    from http import HTTPStatus as StatusCodes
except ImportError:  # pragma: no cover
    try:
        from http import client as StatusCodes
    except ImportError:
        import httplib as StatusCodes

__author__ = "Alex Laird"
__copyright__ = "Copyright 2020, Alex Laird"
__version__ = "4.0.0"

logger = logging.getLogger(__name__)

_current_processes = {}
_ngrok_threads = {}


class NgrokProcess:
    """
    An object containing information about the `ngrok` process.

    :var string ngrok_path: The path to the `ngrok` binary used to start this process.
    :var string config_path: The path to the `ngrok` config used.
    :var object proc: The child `subprocess.Popen <https://docs.python.org/3/library/subprocess.html#subprocess.Popen>`_ that is running `ngrok`.
    :var function log_func: An optional callback that will be invoked each time `ngrok` emits a log.
    :var string api_url: The API URL for the `ngrok` web interface.
    :var list[NgrokLog] logs: A list of the last 500 logs from `ngrok`.
    :var string startup_error: If `ngrok` startup fails, this will be the log of the failure.
    """

    def __init__(self, ngrok_path, config_path, proc, log_func=None):
        self.ngrok_path = ngrok_path
        self.config_path = config_path
        self.proc = proc
        self.log_func = log_func
        self.api_url = None
        self.logs = []
        self.startup_error = None

        self._max_logs = 500
        self._tunnel_started = False
        self._client_connected = False

    def __repr__(self):
        return "<NgrokProcess: \"{}\">".format(self.api_url)

    def __str__(self):  # pragma: no cover
        return "NgrokProcess: \"{}\"".format(self.api_url)

    @staticmethod
    def _line_has_error(log):
        return log.lvl in ["ERROR", "CRITICAL"]

    def log_boot_line(self, line):
        log = self.log_line(line)

        if log is None:
            return
        elif self._line_has_error(log):
            self.startup_error = log.err
        else:
            # Log `ngrok` boot states as they come up
            if "starting web service" in log.msg and log.addr is not None:
                self.api_url = "http://{}".format(log.addr)
            elif "tunnel session started" in log.msg:
                self._tunnel_started = True
            elif "client session established" in log.msg:
                self._client_connected = True

    def log_line(self, line):
        log = NgrokLog(line)

        if log.line == "":
            return None

        logger.log(getattr(logging, log.lvl), line)
        self.logs.append(log)
        if len(self.logs) > self._max_logs:
            self.logs.pop(0)

        if self.log_func is not None:
            self.log_func(log)

        return log

    def healthy(self):
        if self.api_url is None or \
                not self._tunnel_started or not self._client_connected:
            return False

        if not self.api_url.lower().startswith("http"):
            raise PyngrokSecurityError("URL must start with 'http': {}".format(self.api_url))

        # Ensure the process is available for requests before registering it as healthy
        request = Request("{}/api/tunnels".format(self.api_url))
        response = urlopen(request)
        if response.getcode() != StatusCodes.OK:
            return False

        return self.proc.poll() is None and \
               self.startup_error is None


class NgrokLog:
    """
    A parsed log from the `ngrok` process.

    :var string line: The raw, unparsed log line.
    :var string t: The logs ISO 8601 timestamp.
    :var string lvl: The logs level.
    :var string msg: The logs message.
    :var string err: The logs error, if applicable.
    :var string addr: The URL, if `obj` is "web".
    """

    def __init__(self, line):
        self.line = line.strip()
        self.t = None
        self.lvl = None
        self.msg = None
        self.err = None
        self.addr = None

        for i in shlex.split(self.line):
            if "=" not in i:
                continue

            key, value = i.split("=")

            if key == "lvl":
                value = value.upper()
                if value == "CRIT":
                    value = "CRITICAL"
                elif value in ["ERR", "EROR"]:
                    value = "ERROR"
                elif value == "WARN":
                    value = "WARNING"

            setattr(self, key, value)

    def __repr__(self):
        return "<NgrokLog: t={} lvl={} msg=\"{}\">".format(self.t, self.lvl, self.msg)

    def __str__(self):  # pragma: no cover
        attrs = [attr for attr in dir(self) if not attr.startswith("_") and getattr(self, attr) is not None]
        attrs.remove("line")

        return " ".join("{}=\"{}\"".format(attr, getattr(self, attr)) for attr in attrs)


def set_auth_token(pyngrok_config, token):
    """
    Set the `ngrok` auth token in the config file, enabling authenticated features (for instance,
    more concurrent tunnels, custom subdomains, etc.).

    :param pyngrok_config: Pyngrok's configuration for interacting with `ngrok`.
    :type pyngrok_config: PyngrokConfig
    :param token: The auth token to set.
    :type token: string
    """
    start = [pyngrok_config.ngrok_path, "authtoken", token, "--log=stdout"]
    if pyngrok_config.config_path:
        start.append("--config={}".format(pyngrok_config.config_path))

    result = subprocess.check_output(start)

    if "Authtoken saved" not in str(result):
        raise PyngrokNgrokError("An error occurred when saving the auth token: {}".format(result))


def get_process(pyngrok_config):
    """
    Retrieve the current `ngrok` process for the given path. If `ngrok` is not currently running for the
    given path, a new process will be started and returned.

    If `ngrok` is not running, calling this method will start a process for the given path.

    :param pyngrok_config: Pyngrok's configuration for interacting with `ngrok`.
    :type pyngrok_config: PyngrokConfig
    :return: The `ngrok` process.
    :rtype: NgrokProcess
    """
    if pyngrok_config.ngrok_path in _current_processes:
        # Ensure the process is still running and hasn't been killed externally
        if _current_processes[pyngrok_config.ngrok_path].proc.poll() is None:
            return _current_processes[pyngrok_config.ngrok_path]
        else:
            _current_processes.pop(pyngrok_config.ngrok_path, None)

    return start_process(pyngrok_config)


def run_process(ngrok_path, args):
    """
    Start a blocking `ngrok` process with the given args.

    :param ngrok_path: The path to the `ngrok` binary.
    :type ngrok_path: string
    :param args: The args to pass to `ngrok`.
    :type args: list
    """
    _ensure_path_ready(ngrok_path)

    start = [ngrok_path] + args
    subprocess.call(start)


def kill_process(ngrok_path):
    """
    Terminate the `ngrok` processes, if running, for the given path. This method will not block, it will just issue
    a kill request.

    :param ngrok_path: The path to the `ngrok` binary.
    :type ngrok_path: string
    """
    if ngrok_path in _current_processes:
        ngrok_process = _current_processes[ngrok_path]

        logger.info("Killing ngrok process: {}".format(ngrok_process.proc.pid))

        try:
            ngrok_process.proc.kill()
        except OSError as e:
            # If the process was already killed, nothing to do but cleanup state
            if e.errno != 3:
                raise e

        _current_processes.pop(ngrok_path, None)
        _ngrok_threads.pop(ngrok_path, None)
    else:
        logger.debug("\"ngrok_path\" {} is not running a process".format(ngrok_path))


def _ensure_path_ready(ngrok_path):
    """
    Ensure the binary for `ngrok` at the given path is ready to be started, raise a relevant
    exception if not.

    :param ngrok_path: The path to the `ngrok` binary.
    """
    if not os.path.exists(ngrok_path):
        raise PyngrokNgrokError(
            "ngrok binary was not found. Be sure to call `ensure_ngrok_installed()` first for "
            "\"ngrok_path\": {}".format(ngrok_path))

    if ngrok_path in _current_processes:
        raise PyngrokNgrokError("ngrok is already running for the \"ngrok_path\": {}".format(ngrok_path))


def _terminate_process(process):
    if process is None:
        return

    try:
        process.terminate()
    except OSError:
        logger.debug("ngrok process already terminated: {}".format(process.pid))


def _read_ngrok_logs(ngrok_process):
    while ngrok_process.proc.poll() is None:
        ngrok_process.log_line(ngrok_process.proc.stdout.readline())


def start_process(pyngrok_config):
    """
    Start a `ngrok` process with no tunnels. This will start the `ngrok` web interface, against
    which HTTP requests can be made to create, interact with, and destroy tunnels.

    :param pyngrok_config: Pyngrok's configuration for interacting with `ngrok`.
    :type pyngrok_config: PyngrokConfig
    :return: The `ngrok` process.
    :rtpe: NgrokProcess
    """
    _ensure_path_ready(pyngrok_config.ngrok_path)

    start = [pyngrok_config.ngrok_path, "start", "--none", "--log=stdout"]
    if pyngrok_config.config_path:
        logger.info("Starting ngrok with config file: {}".format(pyngrok_config.config_path))
        start.append("--config={}".format(pyngrok_config.config_path))
    if pyngrok_config.auth_token:
        logger.info("Overriding default auth token")
        start.append("--authtoken={}".format(pyngrok_config.auth_token))
    if pyngrok_config.region:
        logger.info("Starting ngrok in region: {}".format(pyngrok_config.region))
        start.append("--region={}".format(pyngrok_config.region))

    process = subprocess.Popen(start, stdout=subprocess.PIPE, universal_newlines=True)
    atexit.register(_terminate_process, process)

    logger.info("ngrok process starting: {}".format(process.pid))

    ngrok_process = NgrokProcess(pyngrok_config.ngrok_path, pyngrok_config.config_path, process,
                                 pyngrok_config.log_func)
    _current_processes[pyngrok_config.ngrok_path] = ngrok_process

    timeout = time.time() + pyngrok_config.boot_timeout
    while time.time() < timeout:
        line = process.stdout.readline()
        ngrok_process.log_boot_line(line)

        if ngrok_process.healthy():
            logger.info("ngrok process has started: {}".format(ngrok_process.api_url))

            if pyngrok_config.keep_thread_alive:
                _ngrok_threads[pyngrok_config.ngrok_path] = threading.Thread(target=_read_ngrok_logs,
                                                                             args=(ngrok_process,))
                _ngrok_threads[pyngrok_config.ngrok_path].start()

            break
        elif ngrok_process.startup_error is not None or \
                ngrok_process.proc.poll() is not None:
            break

    if not ngrok_process.healthy():
        # If the process did not come up in a healthy state, clean up the state
        kill_process(pyngrok_config.ngrok_path)

        if ngrok_process.startup_error is not None:
            raise PyngrokNgrokError("The ngrok process errored on start: {}.".format(ngrok_process.startup_error),
                                    ngrok_process.logs,
                                    ngrok_process.startup_error)
        else:
            raise PyngrokNgrokError("The ngrok process was unable to start.", ngrok_process.logs)

    return ngrok_process
