"""Handles all imports from jnius to prevent conflicts resulting from attempts
to set JVM options while the VM is already running."""

from __future__ import absolute_import, print_function, unicode_literals
from builtins import dict, str
import os
import logging
import jnius_config
from indra import get_config

logger = logging.getLogger(__name__)


def _has_xmx(options):
    for option in options:
        if option.startswith('-Xmx'):
            return True
    return False


default_mem_limit = get_config("INDRA_DEFAULT_JAVA_MEM_LIMIT")
if default_mem_limit is None:
    # Set to 8g if not specified in the configuration
    default_mem_limit = '8g'

if not _has_xmx(jnius_config.get_options()):
    if not jnius_config.vm_running:
        jnius_config.add_options('-Xmx%s' % default_mem_limit)
    else:
        logger.warning("Couldn't set memory limit for Java VM because the VM "
                       "is already running.")

path_here = os.path.dirname(os.path.realpath(__file__))
cp = os.path.join(path_here, 'sources/biopax/jars/paxtools.jar')
cp_existing = os.environ.get('CLASSPATH')

if cp_existing is not None:
    os.environ['CLASSPATH'] = cp + ':' + cp_existing
else:
    os.environ['CLASSPATH'] = cp

from jnius import autoclass, JavaException, cast

