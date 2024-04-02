import re
import json
import logging
from urllib import parse
from indra.resources import load_resource_json


logger = logging.getLogger(__name__)


identifiers_url = 'https://identifiers.org'

identifiers_mappings = {
    'REFSEQ_PROT': 'refseq',
    'NCBI': 'ncibgene',
    'UP': 'uniprot',
    'NONCODE': 'noncodev4.rna',
    'EGID': 'ncbigene',
    'LINCS': 'lincs.smallmolecule',
    'LNCRNADB': 'rnacentral',
    'PUBCHEM': 'pubchem.compound',
    'UPPRO': 'uniprot.chain',
    'UPISO': 'uniprot.isoform',
    'PF': 'pfam',
    'CHEMBL': 'chembl.compound',
    'MIRBASEM': 'mirbase.mature',
    'HGNC_GROUP': 'hgnc.genefamily',
    'CTD': 'ctd.chemical',
    'IP': 'interpro',
}

non_registry = {
    'SDIS', 'SCHEM', 'SFAM', 'SCOMP', 'SIGNOR', 'HMS-LINCS', 'NXPFA',
    'GENBANK', 'OMIM', 'LSPCI', 'ECCODE'
}

non_grounding = {
    'TEXT', 'TEXT_NORM'
}


# These are only the URLs that are strictly prefixes and not more complicated
# patterns. This is because some downstream code uses these as prefixes
# rather than arbitrary patterns.
url_prefixes = {
    'NXPFA': 'https://www.nextprot.org/term/FA-',
    'SIGNOR': 'https://signor.uniroma2.it/relation_result.php?id=',
    'UN': 'https://github.com/clulab/eidos/wiki/JSON-LD#Grounding/',
    'WDI': 'https://github.com/clulab/eidos/wiki/JSON-LD#Grounding/',
    'FAO': 'https://github.com/clulab/eidos/wiki/JSON-LD#Grounding/',
    'HUME': ('https://github.com/BBN-E/Hume/blob/master/resource/ontologies'
             '/hume_ontology/'),
    'CWMS': 'http://trips.ihmc.us/',
    'SOFIA': 'http://cs.cmu.edu/sofia/',
    'HGNC_GROUP': 'https://www.genenames.org/data/genegroup/#!/group/',
    'PR': 'https://proconsortium.org/app/entry/PR%3A',
    'GENBANK': 'https://www.ncbi.nlm.nih.gov/protein/',
}


def get_url_prefix(db_name):
    identifiers_entry = identifiers_registry.get(db_name.lower())
    if identifiers_entry:
        if not identifiers_entry['prefix_embedded']:
            return '%s/%s:' % (identifiers_url, db_name.lower())
        else:
            return '%s/' % identifiers_url
    else:
        if db_name in url_prefixes:
            return url_prefixes[db_name]
    return None


def get_identifiers_url(db_name, db_id):
    """Return an identifiers.org URL for a given database name and ID.

    Parameters
    ----------
    db_name : str
        An internal database name: HGNC, UP, CHEBI, etc.
    db_id : str
        An identifier in the given database.

    Returns
    -------
    url : str
        An identifiers.org URL corresponding to the given database name and ID.
    """
    # This is the case where we have a prefix that we can simply attach the
    # db_id to to get the desired URL.
    prefix = get_url_prefix(db_name)
    if prefix:
        return '%s%s' % (prefix, db_id)

    # Otherwise, we have to handle some special cases
    bel_scai_url = 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/'
    if db_name == 'LINCS':
        if db_id.startswith('LSM-'):  # Lincs Small Molecule ID
            url = identifiers_url + '/lincs.smallmolecule:%s' % db_id
        elif db_id.startswith('LCL-'):  # Lincs Cell Line ID
            url = identifiers_url + '/lincs.cell:%s' % db_id
        else:  # Assume LINCS Protein
            url = identifiers_url + '/lincs.protein:%s' % db_id
    elif db_name == 'CHEMBL':
        if not db_id.startswith('CHEMBL'):
            db_id = 'CHEMBL%s' % db_id
        url = identifiers_url + '/chembl.compound:%s' % db_id
    elif db_name == 'HMS-LINCS':
        url = 'http://lincs.hms.harvard.edu/db/sm/%s-101' % db_id
    # Special cases with no identifiers entry
    elif db_name == 'SCHEM':
        url = bel_scai_url + 'selventa-legacy-chemicals/' + \
            'selventa-legacy-chemicals-20150601.belns'
    elif db_name == 'SCOMP':
        url = bel_scai_url + 'selventa-named-complexes/' + \
            'selventa-named-complexes-20150601.belns'
    elif db_name == 'SFAM':
        url = bel_scai_url + 'selventa-protein-families/' + \
            'selventa-protein-families-20150601.belns'
    elif db_name == 'LNCRNADB':
        # Note that this website is disabled
        if db_id.startswith('ENSG'):
            url = 'http://www.lncrnadb.org/search/?q=%s' % db_id
        else:  # Assmuing HGNC symbol
            url = 'http://www.lncrnadb.org/%s/' % db_id
    elif db_name == 'NONCODE':
        if '.' in db_id:
            _id, version = db_id.split('.')
            url = 'http://www.noncode.org/show_gene.php?id=%s&version=%s' \
                % (_id, version)
        else:
            url = 'http://www.noncode.org/show_gene.php?id=%s' % db_id
    elif db_name == 'TEXT' or db_name == 'TEXT_NORM':
        return None
    else:
        logger.warning('Unhandled name space %s' % db_name)
        url = None
    return url


def parse_identifiers_url(url):
    """Retrieve database name and ID given the URL.

    Parameters
    ----------
    url : str
        An identifiers.org URL to parse.

    Returns
    -------
    db_name : str
        An internal database name: HGNC, UP, CHEBI, etc. corresponding to the
        given URL.
    db_id : str
        An identifier in the database.
    """
    prefixed_ids = ['CHEBI', 'DOID', 'GO', 'HP']
    # Try reverse dictionary lookup first
    ns_options = {}
    for ns, prefix in url_prefixes.items():
        if ns not in prefixed_ids and url.startswith(prefix):
            db_id = url[len(prefix):]
            # If we got UP and UPPRO, return UPPRO
            if ns == 'UP' and '#PRO_' in db_id:
                ns = 'UPPRO'
                db_id = db_id[db_id.find('PRO_'):]
            ns_options[ns] = db_id

    # If we got the only possible option, return it
    if len(ns_options) == 1:
        return [(k, v) for (k, v) in ns_options.items()][0]
    # Handle cases when 2 matches are possible
    elif len(ns_options) == 2:
        for ns in ['PUBCHEM', 'IP', 'MIRBASEM']:
            if ns in ns_options:
                return ns, ns_options[ns]
    elif len(ns_options) > 2:
        logger.warning('Got too many options: %s' % ns_options)

    # Special handling for IDs including prefix
    for ns in prefixed_ids:
        if ns in url and url.startswith(url_prefixes[ns]):
            return ns, url[url.find(ns):]

    # Try matching by string pattern
    db_name, db_id = None, None
    url_pattern = \
        r'(?:https?)://identifiers.org/([A-Za-z.-]+)(/|:)([A-Za-z0-9:_.-]+)'
    match = re.match(url_pattern, url)
    if match is not None:
        g = match.groups()
        if len(g) == 3:
            ns, db_id = g[0], g[2]
            ns_map = {'uniprot': 'UP', 'interpro': 'IP', 'pfam': 'PF',
                      'pubchem.compound': 'PUBCHEM',
                      'mirbase.mature': 'MIRBASEM', 'ncbigene': 'EGID',
                      'refseq': 'REFSEQ_PROT', 'ec-code': 'ECCODE'}
            if ns in ns_map.keys():
                db_name = ns_map[ns]
            elif ns.upper() in url_prefixes.keys():
                db_name = ns.upper()
            if db_name == 'HGNC':
                if db_id.startswith('HGNC:'):
                    db_id = db_id[5:]
            # If we got UP and UPPRO, return UPPRO
            if db_name == 'UP' and '#PRO_' in url:
                db_name = 'UPPRO'
                db_id = url[url.find('PRO_'):]
            if db_name in prefixed_ids:
                if not db_id.startswith(db_name):
                    db_id = db_name + ':' + db_id
            if db_name and db_id:
                return db_name, db_id

    # Handle other special cases
    for part in ['/lincs.smallmolecule', '/lincs.cell', '/lincs.protein']:
        if part in url:
            return 'LINCS', url[(url.find(part) + len(part) + 1):]
    if '/chembl.compound' in url:
        return 'CHEMBL', url[
            (url.find('/chembl.compound') + len('/chembl.compound:')):]
    if 'lincs.hms.harvard.edu' in url:
        return 'HMS-LINCS', url[len('http://lincs.hms.harvard.edu/db/sm/'):-4]
    if 'selventa-legacy-chemicals/' in url:
        return 'SCHEM', None
    if 'selventa-named-complexes/' in url:
        return 'SCOMP', None
    if 'selventa-protein-families/' in url:
        return 'SFAM', None
    if 'lncrnadb' in url:
        # Note that this website is disabled
        if 'ENSG' in url:
            return 'LNCRNADB', url[len('http://www.lncrnadb.org/search/?q='):]
        else:
            return 'LNCRNADB', url[len('http://www.lncrnadb.org/'):-1]
    if 'noncode' in url:
        q = parse.parse_qs(parse.urlparse(url).query)
        _id, version = q.get('id'), q.get('version')
        if version:
            db_id = _id[0] + '.' + version[0]
        else:
            db_id = _id[0]
        return 'NONCODE', db_id
    else:
        logger.warning('Could not parse URL %s' % url)
    return None, None


def ensure_chebi_prefix(chebi_id):
    if chebi_id is None:
        return None
    if not chebi_id.startswith('CHEBI:'):
        return f'CHEBI:{chebi_id}'
    return chebi_id


def ensure_chembl_prefix(chembl_id):
    if chembl_id is None:
        return None
    if not chembl_id.startswith('CHEMBL'):
        return f'CHEMBL{chembl_id}'
    return chembl_id


identifiers_registry = load_resource_json('identifiers_patterns.json')
