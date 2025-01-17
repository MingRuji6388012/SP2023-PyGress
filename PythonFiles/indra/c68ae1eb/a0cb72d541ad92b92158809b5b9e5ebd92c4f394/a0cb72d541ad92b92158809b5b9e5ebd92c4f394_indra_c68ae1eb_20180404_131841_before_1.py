from __future__ import absolute_import, print_function, unicode_literals
from builtins import dict, str
import logging
from collections import namedtuple
from .processor import SignorProcessor
from indra.util import read_unicode_csv

logger = logging.getLogger('signor')

_signor_fields = [
    'ENTITYA',
    'TYPEA',
    'IDA',
    'DATABASEA',
    'ENTITYB',
    'TYPEB',
    'IDB',
    'DATABASEB',
    'EFFECT',
    'MECHANISM',
    'RESIDUE',
    'SEQUENCE',
    'TAX_ID',
    'CELL_DATA',
    'TISSUE_DATA',
    'MODULATOR_COMPLEX',
    'TARGET_COMPLEX',
    'MODIFICATIONA',
    'MODASEQ',
    'MODIFICATIONB',
    'MODBSEQ',
    'PMID',
    'DIRECT',
    'NOTES',
    'ANNOTATOR',
    'SENTENCE',
    'SIGNOR_ID',
]


SignorRow = namedtuple('SignorRow', _signor_fields)

def _read_signor_complex_map(filename):
    raw_map = read_unicode_csv(filename, ';')
    m = {}
    for row in raw_map:
        m[row[0]] = row[2].split(',  ')
    return m


def process_file(signor_data_file, signor_complexes_file=None):
    """Process Signor interaction data from CSV files.

    Parameters
    ----------
    signor_data_file : str
        Path to the Signor interaction data file in CSV format.
    signor_complexes_file : str
        Path to the Signor complexes data in CSV format. If unspecified,
        Signor complexes will not be expanded to their constitutents.

    Returns
    -------
    indra.sources.signor.SignorProcessor
        SignorProcessor containing Statements extracted from the Signor data.
    """
    # Get generator over the CSV file
    data_iter = read_unicode_csv(signor_data_file, delimiter=';', skiprows=1)
    # Process into a list of SignorRow namedtuples
    # Strip off any funky \xa0 whitespace characters
    data = [SignorRow(*[f.strip() for f in r]) for r in data_iter]
    if signor_complexes_file:
        complex_map = _read_signor_complex_map(signor_complexes_file)
    else:
        complex_map = {}
        logger.warning('Signor complex mapping file not provided, Statements '
                       'involving complexes will not be expanded to members.')
    return SignorProcessor(data, complex_map)

    """
    # If no CSV given, download directly from web
    else:
        url = 'https://signor.uniroma2.it/download_entity.php'
        res = requests.post(url, data={'organism':'human',
                                       'format':'csv',
                                       'submit':'Download'})
        if res.status_code == 200:
            # Python 2 -- csv.reader will need bytes
            if sys.version_info[0] < 3:
                csv_io = BytesIO(res.content)
            # Python 3 -- csv.reader needs str
            else:
                csv_io = StringIO(res.text)
            data_iter = read_unicode_csv_fileobj(csv_io,
                                                 delimiter=delimiter,
                                                 skiprows=1)
        else:
            raise Exception('Could not download Signor data.')
    """

def process_url():
    pass
