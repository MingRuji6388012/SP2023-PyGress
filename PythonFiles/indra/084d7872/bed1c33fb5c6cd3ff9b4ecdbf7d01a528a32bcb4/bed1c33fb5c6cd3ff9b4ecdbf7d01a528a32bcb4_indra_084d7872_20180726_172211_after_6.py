import json
import rdflib
import logging
from indra.sources.hume import processor
from os.path import abspath

logger = logging.getLogger('hume')


def process_jsonld_file(fname):
    """Process a JSON-LD file in the new format to extract Statements.

    Parameters
    ----------
    fname : str
        The path to the JSON-LD file to be processed.

    Returns
    -------
    bp : indra.sources.hume.HumeProcessor
        A HumeProcessor instance, which contains a list of INDRA Statements
        as its statements attribute.
    """
    with open(fname, 'r') as fh:
        json_dict = json.load(fh)
    bp = processor.HumeJsonLdProcessor(json_dict)
    bp.get_events()
    return bp


def process_json_file_old(fname):
    """Process a JSON-LD file in the old format to extract Statements.

    Parameters
    ----------
    fname : str
        The path to the JSON-LD file to be processed.

    Returns
    -------
    bp : indra.sources.hume.HumeProcessor
        A HumeProcessor instance, which contains a list of INDRA Statements
        as its statements attribute.
    """
    graph = _load_graph(fname)
    bp = processor.HumeProcessor(graph)
    bp.get_statements()
    return bp


def _load_graph(fname):
    fname = abspath(fname)
    g = rdflib.Graph()
    with open(fname, 'rb') as fh:
        logger.info('Started loading graph from %s' % fname)
        g.parse(fh, format='json-ld')
        logger.info('Finished loading graph')
    return g
