from __future__ import absolute_import, print_function, unicode_literals
from builtins import dict, str
import os
import logging
import subprocess
import xml.etree.ElementTree as ET
from indra.util import UnicodeXMLTreeBuilder as UTB
from .processor import SparserProcessor

logger = logging.getLogger('sparser')

sparser_path_var = 'SPARSERPATH'
sparser_path = os.environ.get(sparser_path_var)

def process_xml(xml_str):
    try:
        tree = ET.XML(xml_str, parser=UTB())
    except ET.ParseError as e:
        logger.error('Could not parse XML string')
        logger.error(e)
        return None
    sp = _process_elementtree(tree)
    return sp

def process_nxml(fname, output_format='json'):
    if not sparser_path or not os.path.exists(sparser_path):
        logger.error('Sparser executable not set in %s' % sparser_path_var)
        return None
    if output_format == 'xml':
        format_flag = '-x'
        suffix = '.xml'
    elif output_format == 'json':
        format_flag = '-j'
        suffix = '.json'
    else:
        logger.error('Unknown output format: %s' % output_format)
    subprocess.call([sparser_path, format_flag, fname])

    output_fname = fname.split('.')[0] + '-semantics' + suffix
    with open(output_fname, 'rb') as fh:
        json_dict = json.load(fh)
        return process_json_dict(json_dict)

def process_json_dict(json_dict):
    sp = SparserJSONProcessor(json_dict)
    sp.get_statements()
    return sp

def _process_elementtree(tree):
    sp = SparserXMLProcessor(tree)
    sp.get_modifications()
    sp.get_activations()
    return sp