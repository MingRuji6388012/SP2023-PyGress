from __future__ import absolute_import, print_function, unicode_literals
from builtins import dict, str, bytes
from past.builtins import basestring
import json
import logging
import requests
from .processor import EidosProcessor

logger = logging.getLogger('eidos')


try:
    # For text reading
    from .reader import EidosReader
    eidos_reader = EidosReader()
except Exception as e:
    logger.warning('Could not instantiate Eidos reader, text reading '
                   'will not be available.')
    eidos_reader = None


def process_text(text, out_format='json_ld', save_json='eidos_output.json',
                 webservice=None):
    """Return an EidosProcessor by processing the given text.

    This constructs a reader object via Java and extracts mentions
    from the text. It then serializes the mentions into JSON and
    processes the result with process_json.

    Parameters
    ----------
    text : str
        The text to be processed.
    out_format : Optional[str]
        The type of Eidos output to read into and process. Currently only
        'json-ld' is supported which is also the default value used.
    save_json : Optional[str]
        The name of a file in which to dump the JSON output of Eidos.
    webservice : Optional[str]
        An Eidos reader web service URL to send the request to.

    Returns
    -------
    ep : EidosProcessor
        An EidosProcessor containing the extracted INDRA Statements in its
        statements attribute.
    """
    if not webservice:
        if eidos_reader is None:
            logger.error('Eidos reader is not available.')
            return None
        json_dict = eidos_reader.process_text(text, out_format)
    else:
        res = requests.post('%s/process_text' % webservice,
                            json={'text': text})
        json_dict = res.json()
    if save_json:
        with open(save_json, 'wt') as fh:
            json.dump(json_dict, fh, indent=2)
    return process_json(json_dict)


def process_json_file(file_name):
    """Return an EidosProcessor by processing the given Eidos JSON-LD file.

    The output from the Eidos reader is in JSON-LD format. This function is
    useful if the output is saved as a file and needs to be processed.

    Parameters
    ----------
    file_name : str
        The name of the JSON-LD file to be processed.

    Returns
    -------
    ep : EidosProcessor
        A EidosProcessor containing the extracted INDRA Statements
        in ep.statements.
    """
    try:
        with open(file_name, 'rb') as fh:
            json_str = fh.read().decode('utf-8')
            return process_json_str(json_str)
    except IOError:
        logger.exception('Could not read file %s.' % file_name)


def process_json_str(json_str):
    """Return an EidosProcessor by processing the Eidos JSON-LD string.

    The output from the Eidos parser is in JSON-LD format.

    Parameters
    ----------
    json_str : str
        The json-LD string to be processed.

    Returns
    -------
    ep : EidosProcessor
        A EidosProcessor containing the extracted INDRA Statements
        in ep.statements.
    """
    logger.warning('This method is deprecated and will be removed in the next'
                   ' version, please use the equivalent process_json_str'
                   ' instead.')
    json_dict = json.loads(json_str)
    return process_json(json_dict)


def process_json(json_dict):
    """Return an EidosProcessor by processing a Eidos JSON-LD dict.

    Parameters
    ----------
    json_dict : dict
        The JSON-LD dict to be processed.

    Returns
    -------
    ep : EidosProcessor
        A EidosProcessor containing the extracted INDRA Statements
        in ep.statements.
    """
    ep = EidosProcessor(json_dict)
    ep.get_events()
    return ep


def initialize_reader():
    """Instantiate an Eidos reader for fast subsequent reading."""
    eidos_reader.process_text('', 'json_ld')


def process_json_ld_file(file_name):
    """DEPRECATED: see process_json_file"""
    logger.warning('This method is deprecated and will be removed in the next'
                   ' version, please use the equivalent process_json_ld_file'
                   ' instead.')
    return process_json_file(file_name)



def process_json_ld_str(json_str):
    """DEPRECATED: see process_json_str"""
    logger.warning('This method is deprecated and will be removed in the next'
                   ' version, please use the equivalent process_json_str'
                   ' instead.')
    return process_json_str(json_str)


def process_json_ld(json_dict):
    """DEPRECATED: see process_json"""
    logger.warning('This method is deprecated and will be removed in the next'
                   ' version, please use the equivalent process_json instead.')
    return process_json(json_dict)
