import rdflib
import logging
from indra.sources.bbn import processor


logger = logging.getLogger('bbn')


def process_json_file(fname):
    """Process a JSON-LD file to extract Statements and return a processor.

    Parameters
    ----------
    fname : str
        The path to the JSON-LD file to be processed.

    Returns
    -------
    bp : indra.sources.bbn.BBNProcessor
        A BBNProcessor instance, which contains a list of INDRA Statements
        as its statements attribute.
    """
    graph = _load_graph(fname)
    bp = processor.BBNProcessor(graph)
    return bp


def _load_graph(fname):
    g = rdflib.Graph()
    with open(fname, 'rb') as fh:
        logger.info('Started loading graph from %s' % fname)
        g.parse(fh, format='json-ld')
        logger.info('Finished loading graph')
    return g

if __name__ == '__main__':
    f = '/Users/daniel/Downloads/bbn-m6-cag.v0.1/cag.json-ld'
    bp = process_json_file(f)
    for statement in bp.statements:
        print(statement, statement.evidence)

