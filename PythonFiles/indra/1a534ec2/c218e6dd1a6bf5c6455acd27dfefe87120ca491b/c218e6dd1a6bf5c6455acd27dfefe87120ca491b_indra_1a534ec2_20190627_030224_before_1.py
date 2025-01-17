"""
Search and get metadata for articles in Pubmed.
"""
import xml.etree.ElementTree as ET
import requests
import logging
from functools import lru_cache
from indra.databases import hgnc_client
from indra.util import UnicodeXMLTreeBuilder as UTB

logger = logging.getLogger(__name__)

pubmed_search = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
pubmed_fetch = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'


# Send request can't be cached by lru_cache because it takes a dict
# (a mutable/unhashable type) as an argument. We cache the callers instead.
def send_request(url, data):
    try:
        res = requests.get(url, params=data)
    except requests.exceptions.Timeout as e:
        logger.error('PubMed request timed out')
        logger.error('url: %s, data: %s' % (url, data))
        logger.error(e)
        return None
    except requests.exceptions.RequestException as e:
        logger.error('PubMed request exception')
        logger.error('url: %s, data: %s' % (url, data))
        logger.error(e)
        return None
    if not res.status_code == 200:
        logger.error('Got return code %d from pubmed client.'
                     % res.status_code)
        return None
    tree = ET.XML(res.content, parser=UTB())
    return tree


@lru_cache(maxsize=100)
def get_ids(search_term, **kwargs):
    """Search Pubmed for paper IDs given a search term.

    Search options can be passed as keyword arguments, some of which are
    custom keywords identified by this function, while others are passed on
    as parameters for the request to the PubMed web service
    For details on parameters that can be used in PubMed searches, see
    https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ESearch Some useful
    parameters to pass are db='pmc' to search PMC instead of pubmed reldate=2
    to search for papers within the last 2 days mindate='2016/03/01',
    maxdate='2016/03/31' to search for papers in March 2016.

    PubMed, by default, limits returned PMIDs to a small number, and this
    number can be controlled by the "retmax" parameter. This function
    uses a retmax value of 100,000 by default that can be changed via the
    corresponding keyword argument.

    Parameters
    ----------
    search_term : str
        A term for which the PubMed search should be performed.
    use_text_word : Optional[bool]
        If True, the "[tw]" string is appended to the search term to constrain
        the search to "text words", that is words that appear as whole
        in relevant parts of the PubMed entry (excl. for instance the journal
        name or publication date) like the title and abstract. Using this
        option can eliminate spurious search results such as all articles
        published in June for a search for the "JUN" gene, or journal names
        that contain Acad for a search for the "ACAD" gene.
        See also: https://www.nlm.nih.gov/bsd/disted/pubmedtutorial/020_760.html
        Default : True
    kwargs : kwargs
        Additional keyword arguments to pass to the PubMed search as
        parameters.
    """
    use_text_word = kwargs.pop('use_text_word', True)
    if use_text_word:
        search_term += '[tw]'
    params = {'term': search_term,
              'retmax': 100000,
              'retstart': 0,
              'db': 'pubmed',
              'sort': 'pub+date'}
    params.update(kwargs)
    tree = send_request(pubmed_search, params)
    if tree is None:
        return []
    if tree.find('ERROR') is not None:
        logger.error(tree.find('ERROR').text)
        return []
    if tree.find('ErrorList') is not None:
        for err in tree.find('ErrorList').getchildren():
            logger.error('Error - %s: %s' % (err.tag, err.text))
        return []
    count = int(tree.find('Count').text)
    id_terms = tree.findall('IdList/Id')
    if id_terms is None:
        return []
    ids = [idt.text for idt in id_terms]
    if count != len(ids):
        logger.warning('Not all ids were retrieved for search %s;\n'
                       'limited at %d.' % (search_term, params['retmax']))
    return ids


def get_id_count(search_term):
    """Get the number of citations in Pubmed for a search query.

    Parameters
    ----------
    search_term : str
        A term for which the PubMed search should be performed.

    Returns
    -------
    int or None
        The number of citations for the query, or None if the query fails.
    """
    params = {'term': search_term,
              'rettype': 'count',
              'db': 'pubmed'}
    tree = send_request(pubmed_search, params)
    if tree is None:
        return None
    else:
        count = tree.getchildren()[0].text
        return int(count)


@lru_cache(maxsize=100)
def get_ids_for_gene(hgnc_name, **kwargs):
    """Get the curated set of articles for a gene in the Entrez database.

    Search parameters for the Gene database query can be passed in as
    keyword arguments. 

    Parameters
    ----------
    hgnc_name : string
        The HGNC name of the gene. This is used to obtain the HGNC ID
        (using the hgnc_client module) and in turn used to obtain the Entrez
        ID associated with the gene. Entrez is then queried for that ID.
    """

    # Get the HGNC ID for the HGNC name
    hgnc_id = hgnc_client.get_hgnc_id(hgnc_name)
    if hgnc_id is None:
        raise ValueError('Invalid HGNC name.')
    # Get the Entrez ID
    entrez_id = hgnc_client.get_entrez_id(hgnc_id)
    if entrez_id is None:
        raise ValueError('Entrez ID not found in HGNC table.')
    # Query the Entrez Gene database
    params = {'db': 'gene',
              'retmode': 'xml',
              'id': entrez_id}
    params.update(kwargs)
    tree = send_request(pubmed_fetch, params)
    if tree is None:
        return []
    if tree.find('ERROR') is not None:
        logger.error(tree.find('ERROR').text)
        return []
    # Get all PMIDs from the XML tree
    id_terms = tree.findall('.//PubMedId')
    if id_terms is None:
        return []
    # Use a set to remove duplicate IDs
    ids = list(set([idt.text for idt in id_terms]))
    return ids


@lru_cache(maxsize=100)
def get_article_xml(pubmed_id):
    """Get the XML metadata for a single article from the Pubmed database.
    """
    if pubmed_id.upper().startswith('PMID'):
        pubmed_id = pubmed_id[4:]
    params = {'db': 'pubmed',
              'retmode': 'xml',
              'id': pubmed_id}
    tree = send_request(pubmed_fetch, params)
    if tree is None:
        return None
    article = tree.find('PubmedArticle/MedlineCitation/Article')
    return article # May be none


def get_title(pubmed_id):
    """Get the title of an article in the Pubmed database."""
    article = get_article_xml(pubmed_id)
    if article is None:
        return None
    return _get_title_from_article_element(article)


def _get_title_from_article_element(article):
    title_tag = article.find('ArticleTitle')
    title = None
    if title_tag is not None:
        title = title_tag.text
        if title is None and hasattr(title_tag, 'itertext'):
            title = ' '.join(list(title_tag.itertext()))
    return title


def _abstract_from_article_element(article, prepend_title=False):
    abstract = article.findall('Abstract/AbstractText')
    if abstract is None:
        return None
    abstract_text = ' '.join(['' if not hasattr(abst, 'itertext')
                              else ' '.join(list(abst.itertext()))
                              for abst in abstract])
    if prepend_title:
        title = _get_title_from_article_element(article)
        if title is not None:
            if not title.endswith('.'):
                title += '.'
            abstract_text = title + ' ' + abstract_text

    return abstract_text


def get_abstract(pubmed_id, prepend_title=True):
    """Get the abstract of an article in the Pubmed database."""
    article = get_article_xml(pubmed_id)
    if article is None:
        return None
    return _abstract_from_article_element(article, prepend_title)


# A function to get the text for the element, or None if not found
def _find_elem_text(root, xpath_string):
    elem = root.find(xpath_string)
    return None if elem is None else elem.text


def _get_journal_info(medline_citation, get_issns_from_nlm):
    # Journal info
    journal = medline_citation.find('Article/Journal')
    journal_title = _find_elem_text(journal, 'Title')
    journal_abbrev = _find_elem_text(journal, 'ISOAbbreviation')

    # Add publish date from JournalIssue/PubDate in Journal info
    pub_date = {}
    journal_pub_date = journal.find('JournalIssue/PubDate')
    pub_date['year'] = _find_elem_text(journal_pub_date, 'Year')
    pub_date['month'] = _find_elem_text(journal_pub_date, 'Month')
    pub_date['day'] = _find_elem_text(journal_pub_date, 'Day')

    # Add the ISSN from the article record
    issn_list = []
    issn = _find_elem_text(journal, 'ISSN')
    if issn:
        issn_list.append(issn)

    # Add the Linking ISSN from the article record
    issn_linking = _find_elem_text(medline_citation,
                                   'MedlineJournalInfo/ISSNLinking')
    if issn_linking:
        issn_list.append(issn_linking)

    # Now get the list of ISSNs from the NLM Catalog
    nlm_id = _find_elem_text(medline_citation,
                             'MedlineJournalInfo/NlmUniqueID')
    if nlm_id and get_issns_from_nlm:
        nlm_issn_list = get_issns_for_journal(nlm_id)
        if nlm_issn_list:
            issn_list += nlm_issn_list

    # Remove any duplicate issns
    issn_list = list(set(issn_list))

    return {'journal_title': journal_title, 'journal_abbrev': journal_abbrev,
            'issn_list': issn_list, 'journal_nlm_id': nlm_id,
            'publication_date': pub_date}


def _get_article_info(medline_citation, pubmed_data):
    article = medline_citation.find('Article')
    pmid = _find_elem_text(medline_citation, './PMID')
    pii = _find_elem_text(article,
                          './ELocationID[@EIdType="pii"][@ValidYN="Y"]')

    # Look for the DOI in the ELocationID field...
    doi = _find_elem_text(article,
                          './ELocationID[@EIdType="doi"][@ValidYN="Y"]')

    # ...and if that doesn't work, look in the ArticleIdList
    if doi is None:
        doi = _find_elem_text(pubmed_data, './/ArticleId[@IdType="doi"]')

    # Try to get the PMCID
    pmcid = _find_elem_text(pubmed_data, './/ArticleId[@IdType="pmc"]')

    # Title
    title = _get_title_from_article_element(article)

    # Author list
    author_elems = article.findall('AuthorList/Author/LastName')
    author_names = None if author_elems is None \
        else [au.text for au in author_elems]

    # Get the page number entry
    page = _find_elem_text(article, 'Pagination/MedlinePgn')

    return {'pmid': pmid, 'pii': pii, 'doi': doi, 'pmcid': pmcid,
            'title': title, 'authors': author_names, 'page': page}


def get_metadata_from_xml_tree(tree, get_issns_from_nlm=False,
                               get_abstracts=False, prepend_title=False,
                               mesh_annotations=False):
    """Get metadata for an XML tree containing PubmedArticle elements.

    Documentation on the XML structure can be found at:
        - https://www.nlm.nih.gov/bsd/licensee/elements_descriptions.html
        - https://www.nlm.nih.gov/bsd/licensee/elements_alphabetical.html

    Parameters
    ----------
    tree : xml.etree.ElementTree
        ElementTree containing one or more PubmedArticle elements.
    get_issns_from_nlm : boolean
        Look up the full list of ISSN number for the journal associated with
        the article, which helps to match articles to CrossRef search results.
        Defaults to False, since it slows down performance.
    get_abstracts : boolean
        Indicates whether to include the Pubmed abstract in the results.
    prepend_title : boolean
        If get_abstracts is True, specifies whether the article title should
        be prepended to the abstract text.
    mesh_annotations : boolean
        If True, extract mesh annotations from the pubmed entries and include
        in the returned data. If false, don't.

    Returns
    -------
    dict of dicts
        Dictionary indexed by PMID. Each value is a dict containing the
        following fields: 'doi', 'title', 'authors', 'journal_title',
        'journal_abbrev', 'journal_nlm_id', 'issn_list', 'page'.
    """
    # Iterate over the articles and build the results dict
    results = {}
    pm_articles = tree.findall('./PubmedArticle')
    for art_ix, pm_article in enumerate(pm_articles):
        medline_citation = pm_article.find('./MedlineCitation')

        article_info = _get_article_info(medline_citation,
                                         pm_article.find('PubmedData'))
        journal_info = _get_journal_info(medline_citation, get_issns_from_nlm)
        context_info = _get_annotations(medline_citation)

        # Build the result
        result = {}
        result.update(article_info)
        result.update(journal_info)
        result.update(context_info)

        # Get the abstracts if requested
        if get_abstracts:
            abstract = _abstract_from_article_element(
                medline_citation.find('Article'),
                prepend_title=prepend_title
                )
            result['abstract'] = abstract

        # Add to dict
        results[article_info['pmid']] = result

    return results


def _get_annotations(medline_citation):

    def _major_topic(e):
        if e is not None and e.get('MajorTopicYN').upper() == 'Y':
            return True
        return False

    info = []
    for elem in medline_citation.findall('.//MeshHeading'):
        dname = elem.find('DescriptorName')
        qname = elem.find('QualifierName')

        mid = dname.attrib['UI']
        major = _major_topic(dname) or _major_topic(qname)
        if qname is not None:
            qual = {'text': qname.text, 'mesh': qname.attrib['UI']}
        else:
            qual = None

        info.append({'mesh': mid, 'text': dname.text, 'major_topic': major,
                     'qualifier': qual})
    return {'mesh_annotations': info}


def get_metadata_for_ids(pmid_list, get_issns_from_nlm=False,
                         get_abstracts=False, prepend_title=False):
    """Get article metadata for up to 200 PMIDs from the Pubmed database.

    Parameters
    ----------
    pmid_list : list of PMIDs as strings
        Can contain 1-200 PMIDs.
    get_issns_from_nlm : boolean
        Look up the full list of ISSN number for the journal associated with
        the article, which helps to match articles to CrossRef search results.
        Defaults to False, since it slows down performance.
    get_abstracts : boolean
        Indicates whether to include the Pubmed abstract in the results.
    prepend_title : boolean
        If get_abstracts is True, specifies whether the article title should
        be prepended to the abstract text.

    Returns
    -------
    dict of dicts
        Dictionary indexed by PMID. Each value is a dict containing the
        following fields: 'doi', 'title', 'authors', 'journal_title',
        'journal_abbrev', 'journal_nlm_id', 'issn_list', 'page'.
    """
    if len(pmid_list) > 200:
        raise ValueError("Metadata query is limited to 200 PMIDs at a time.")
    params = {'db': 'pubmed',
              'retmode': 'xml',
              'id': pmid_list}
    tree = send_request(pubmed_fetch, params)
    if tree is None:
        return None
    return get_metadata_from_xml_tree(tree, get_issns_from_nlm, get_abstracts,
                                      prepend_title)


@lru_cache(maxsize=1000)
def get_issns_for_journal(nlm_id):
    """Get a list of the ISSN numbers for a journal given its NLM ID.

    Information on NLM XML DTDs is available at
    https://www.nlm.nih.gov/databases/dtd/
    """
    params = {'db': 'nlmcatalog',
              'retmode': 'xml',
              'id': nlm_id}
    tree = send_request(pubmed_fetch, params)
    if tree is None:
        return None
    issn_list = tree.findall('.//ISSN')
    issn_linking = tree.findall('.//ISSNLinking')
    issns = issn_list + issn_linking
    # No ISSNs found!
    if not issns:
        return None
    else:
        return [issn.text for issn in issns]


def expand_pagination(pages):
    """Convert a page number to long form, e.g., from 456-7 to 456-457."""
    # If there is no hyphen, it's a single page, and we're good to go
    parts = pages.split('-')
    if len(parts) == 1: # No hyphen, so no split
        return pages
    elif len(parts) == 2:
        start = parts[0]
        end = parts[1]
        # If the end is the same number of digits as the start, then we
        # don't change anything!
        if len(start) == len(end):
            return pages
        # Otherwise, replace the last digits of start with the digits of end
        num_end_digits = len(end)
        new_end = start[:-num_end_digits] + end
        return '%s-%s' % (start, new_end)
    else: # More than one hyphen, something weird happened
        logger.warning("Multiple hyphens in page number: %s" % pages)
        return pages

