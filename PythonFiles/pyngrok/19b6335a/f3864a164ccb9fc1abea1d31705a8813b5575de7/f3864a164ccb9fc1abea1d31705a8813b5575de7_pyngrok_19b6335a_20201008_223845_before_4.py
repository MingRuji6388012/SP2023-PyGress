import os
import shutil
import unittest

import psutil
from psutil import AccessDenied, NoSuchProcess

from pyngrok import ngrok, installer, conf
from pyngrok import process
from pyngrok.conf import PyngrokConfig

__author__ = "Alex Laird"
__copyright__ = "Copyright 2020, Alex Laird"
__version__ = "5.0.0"


class NgrokTestCase(unittest.TestCase):
    def setUp(self):
        self.config_dir = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), ".ngrok2"))
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        config_path = os.path.join(self.config_dir, "config.yml")

        conf.DEFAULT_NGROK_CONFIG_PATH = config_path

        self.pyngrok_config = PyngrokConfig(config_path=conf.DEFAULT_NGROK_CONFIG_PATH)

        installer.DEFAULT_RETRY_COUNT = 1

    def tearDown(self):
        for p in list(process._current_processes.values()):
            try:
                process.kill_process(p.pyngrok_config.ngrok_path)
                p.proc.wait()
            except OSError:
                pass

        ngrok._current_tunnels.clear()

        if os.path.exists(self.config_dir):
            shutil.rmtree(self.config_dir)

    @staticmethod
    def given_ngrok_installed(ngrok_path):
        ngrok.install_ngrok(ngrok_path)

    @staticmethod
    def given_ngrok_not_installed(ngrok_path):
        if os.path.exists(ngrok_path):
            os.remove(ngrok_path)

    def assertNoZombies(self):
        try:
            self.assertEqual(0, len(
                list(filter(lambda p: p.name() == "ngrok" and p.status() == "zombie", psutil.process_iter()))))
        except (AccessDenied, NoSuchProcess):
            # Some OSes are flaky on this assertion, but that isn't an indication anything is wrong, so pass
            pass
