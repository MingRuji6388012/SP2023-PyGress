import logging
import os
import platform
import shutil
import sys
import tempfile
import zipfile

from future.standard_library import install_aliases

from pyngrok.exception import PyngrokNgrokInstallError

install_aliases()

from urllib.request import urlopen

__author__ = "Alex Laird"
__copyright__ = "Copyright 2019, Alex Laird"
__version__ = "1.3.3"

logger = logging.getLogger(__name__)

CDN_URL_PREFIX = "https://bin.equinox.io/c/4VmDzA7iaHb/"
PLATFORMS = {
    'darwin_x86_64': CDN_URL_PREFIX + "ngrok-stable-darwin-amd64.zip",
    'darwin_i386': CDN_URL_PREFIX + "ngrok-stable-darwin-386.zip",
    'windows_x86_64': CDN_URL_PREFIX + "ngrok-stable-windows-amd64.zip",
    'windows_i386': CDN_URL_PREFIX + "ngrok-stable-windows-386.zip",
    'linux_x86_64_arm': CDN_URL_PREFIX + "ngrok-stable-linux-arm64.zip",
    'linux_i386_arm': CDN_URL_PREFIX + "ngrok-stable-linux-arm.zip",
    'linux_i386': CDN_URL_PREFIX + "ngrok-stable-linux-386.zip",
    'linux_x86_64': CDN_URL_PREFIX + "ngrok-stable-linux-amd64.zip",
    'freebsd_x86_64': CDN_URL_PREFIX + "ngrok-stable-freebsd-amd64.zip",
    'freebsd_i386': CDN_URL_PREFIX + "ngrok-stable-freebsd-386.zip",
}


def get_ngrok_bin():
    """
    Retrieve the `ngrok` command for the current system.

    :return: The `ngrok` command.
    :rtype: string
    """
    system = platform.system()
    if system in ["Darwin", "Linux"]:
        return "ngrok"
    elif system == "Windows":  # pragma: no cover
        return "ngrok.exe"
    else:  # pragma: no cover
        raise PyngrokNgrokInstallError("\"{}\" is not a supported platform".format(system))


def install_ngrok(ngrok_path):
    """
    Download and install `ngrok` for the current system in the given location.

    :param ngrok_path: The path to where the `ngrok` binary will be downloaded.
    :type ngrok_path: string
    """
    logger.debug("Binary not found at {}, installing ngrok ...".format(ngrok_path))

    ngrok_dir = os.path.dirname(ngrok_path)

    if not os.path.exists(ngrok_dir):
        os.mkdir(ngrok_dir)

    arch = 'x86_64' if sys.maxsize > 2 ** 32 else 'i386'
    if 'arm' in os.uname()[4]:
        arch += '_arm'
    plat = platform.system().lower() + "_" + arch
    try:
        url = PLATFORMS[plat]

        logger.debug("Platform to download: {}".format(plat))
    except KeyError:
        raise PyngrokNgrokInstallError("\"{}\" is not a supported platform".format(plat))

    try:
        download_path = _download_file(url)

        with zipfile.ZipFile(download_path, "r") as zip_ref:
            logger.debug("Extracting ngrok binary to {} ...".format(download_path))
            zip_ref.extractall(os.path.dirname(ngrok_path))

        os.chmod(ngrok_path, int("777", 8))
    except Exception as e:
        raise PyngrokNgrokInstallError("An error occurred while downloading ngrok from {}: {}".format(url, e))


def _download_file(url):
    logger.debug("Download ngrok from {} ...".format(url))

    local_filename = url.split("/")[-1]
    response = urlopen(url)

    status_code = response.getcode()
    logger.debug("Response status code: {}".format(status_code))

    if status_code != 200:
        return None

    download_path = os.path.join(tempfile.gettempdir(), local_filename)

    with open(download_path, "wb") as f:
        shutil.copyfileobj(response, f)

    return download_path
