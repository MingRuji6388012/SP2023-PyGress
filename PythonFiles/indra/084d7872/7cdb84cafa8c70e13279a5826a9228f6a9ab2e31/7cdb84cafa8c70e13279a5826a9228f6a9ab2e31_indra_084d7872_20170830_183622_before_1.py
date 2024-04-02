import pandas
import logging
import requests
# Python3
try:
    from io import StringIO
# Python2
except ImportError:
    from StringIO import StringIO

logger = logging.getLogger('cbio')

cbio_url = 'http://www.cbioportal.org/webservice.do'
ccle_study = 'cellline_ccle_broad'

def send_request(data, skiprows=0):
    """Return a data frame from a web service request to cBio portal.

    Sends a web service requrest to the cBio portal with arguments given in
    the dictionary data and returns a Pandas data frame on success.

    More information about the service here:
    http://www.cbioportal.org/web_api.jsp

    Parameters
    ----------
    data : dict
        A dict of parameters for the query.
    skiprows : Optional[int]
        Number of rows to skip when reading dataframe. This is useful to align
        headers.

    Returns
    -------
    df : Pandas DataFrame
        return the response from cBioPortal as a Pandas DataFrame
    """
    res = requests.get(cbio_url, params=data)
    if res.status_code == 200:
        csv_StringIO = StringIO(res.text)
        df = pandas.read_csv(csv_StringIO, sep='\t', skiprows=skiprows)
        return df
    else:
        logger.error('Request returned with code %d' % res.status_code)


def get_mutations(study_id, gene_list, mutation_type=None,
                  case_id=None):
    """Return mutations as a list of genes and list of amino acid changes.

    Parameters
    ----------
    study_id : str
        The ID of the cBio study.
        Example: 'cellline_ccle_broad' or 'paad_icgc'
    gene_list : list[str]
        A list of genes with their HGNC symbols.
        Example: ['BRAF', 'KRAS']
    mutation_type : Optional[str]
        The type of mutation to filter to.
        mutation_type can be one of: missense, nonsense, frame_shift_ins,
                                     frame_shift_del, splice_site
    case_id : Optional[str]
        The case ID within the study to filter to.

    Returns
    -------
    mutations : tuple[list]
        A tuple of two lists, the first one containing a list of genes, and
        the second one a list of amino acid changes in those genes.
    """
    genetic_profile = get_genetic_profiles(study_id, 'mutation')[0]
    gene_list_str = ','.join(gene_list)

    data = {'cmd': 'getMutationData',
            'case_set_id': study_id,
            'genetic_profile_id': genetic_profile,
            'gene_list': gene_list_str}
    df = send_request(data, skiprows=1)
    if case_id:
        df = df[df['case_id'] == case_id]
    res = _filter_data_frame(df, ['gene_symbol', 'amino_acid_change'],
                                   'mutation_type', mutation_type)
    mutations = {'gene_symbol': res['gene_symbol'].values(),
                 'amino_acid_change': res['amino_acid_change'].values()}
    return mutations


def get_num_sequenced(study_id):
    """Return number of sequenced tumors for given study.

    This is useful for calculating mutation statistics in terms of the
    prevalence of certain mutations within a type of cancer.

    Parameters
    ----------
    study_id : str
        The ID of the cBio study.
        Example: 'paad_icgc'

    Returns
    -------
    num_case : int
        The number of sequenced tumors in the given study
    """
    data = {'cmd': 'getCaseLists',
            'cancer_study_id': study_id}
    df = send_request(data)
    row_filter = df['case_list_id'].str.contains('sequenced', case=False)
    num_case = len(df[row_filter]['case_ids'].tolist()[0].split(' '))
    return num_case

def get_genetic_profiles(study_id, profile_filter=None):
    """Return all the genetic profiles (data sets) for a given study.

    Genetic profiles are different types of data for a given study. For
    instance the study 'cellline_ccle_broad' has profiles such as
    'cellline_ccle_broad_mutations' for mutations, 'cellline_ccle_broad_CNA'
    for copy number alterations, etc.


    Parameters
    ----------
    study_id : str
        The ID of the cBio study.
        Example: 'paad_icgc'
    profile_filter : Optional[str]
        A string used to filter the profiles to return.
        The genetic profiles can include "mutation", "CNA", "rppa",
        "methylation", etc.

    Returns
    -------
    genetic_profiles : list[str]
        A list of genetic profiles available  for the given study.
    """
    data = {'cmd': 'getGeneticProfiles',
            'cancer_study_id': study_id}
    df = send_request(data)
    res = _filter_data_frame(df, ['genetic_profile_id'],
                                  'genetic_alteration_type', profile_filter)
    genetic_profiles = res['genetic_profile_id'].values()
    return genetic_profiles

def get_cancer_studies(study_filter=None):
    """Return a list of cancer study identifiers, optionally filtered.

    There are typically multiple studies for a given type of cancer and
    a filter can be used to constrain the returned list.

    Parameters
    ----------
    study_filter : Optional[str]
        A string used to filter the study IDs to return. Example: "paad"

    Returns
    -------
    study_ids : list[str]
        A list of study IDs.
        For instance "paad" as a filter would result in a list
        of study IDs with paad in their name like "paad_icgc", "paad_tcga",
        etc.
    """
    data = {'cmd': 'getCancerStudies'}
    df = send_request(data)
    res = _filter_data_frame(df, ['cancer_study_id'],
                             'cancer_study_id', study_filter)
    study_ids = res['cancer_study_id'].values()
    return study_ids

def get_cancer_types(cancer_filter=None):
    """Return a list of cancer types, optionally filtered.

    Parameters
    ----------
    cancer_filter : Optional[str]
        A string used to filter cancer types. Its value is the name or
        part of the name of a type of cancer. Example: "melanoma",
        "pancreatic", "non-small cell lung"

    Returns
    -------
    type_ids : list[str]
        A list of cancer types matching the filter.
        Example: for cancer_filter="pancreatic", the result includes
        "panet" (neuro-endocrine) and "paad" (adenocarcinoma)
    """
    data = {'cmd': 'getTypesOfCancer'}
    df = send_request(data)
    res = _filter_data_frame(df, ['type_of_cancer_id'], 'name', filter_str)
    type_ids = res['type_of_cancer_id'].values()
    return type_ids

def get_mutations_ccle(gene_list, cell_lines, mutation_type=None):
    """Return a dict of mutations in given genes and cell lines from CCLE.

    This is a specialized call to get_mutations tailored to CCLE cell lines.

    Parameters
    ----------
    gene_list : list[str]
        A list of HGNC gene symbols to get mutations in
    cell_lines : list[str]
        A list of CCLE cell line names to get mutations for.
    mutation_type : Optional[str]
        The type of mutation to filter to.
        mutation_type can be one of: missense, nonsense, frame_shift_ins,
                                     frame_shift_del, splice_site

    Returns
    -------
    mutations : dict
        The result from cBioPortal as a dict in the format
        {cell_line : {gene : [mutation1, mutation2, ...] }}

        Example:
        {'LOXIMVI_SKIN': {'BRAF': ['V600E', 'I208V']},
         'SKMEL30_SKIN': {'BRAF': ['D287H', 'E275K']}}
    """
    mutations = {cl: {g: [] for g in gene_list} for cl in cell_lines}
    for cell_line in cell_lines:
        mutations_cl = get_mutations(ccle_study, gene_list,
                                     mutation_type=mutation_type,
                                     case_id=cell_line)
        for gene, aa_change in zip(mutations_cl['gene_symbol'],
                                   mutations_cl['amino_acid_change']):
            mutations[cell_line][gene].append(aa_change)
    return mutations


def check_ccle_lines_for_mutation(gene, amino_acid_change):
    """Return cell lines with a given mutation.

    Check which cell lines in CCLE have a particular mutation and
    return their names in a list.

    Parameters
    ----------
    gene : str
        as HGNC ID
    amino_acid_change : str
        example - V600E

    Returns
    -------
    cell_lines : list
        return the response from cBioPortal as a list of cell lines
    """
    data = {'cmd': 'getMutationData',
            'case_set_id': ccle_study,
            'genetic_profile_id': ccle_study + '_mutations',
            'gene_list': gene}
    df = send_request(data, skiprows=1)
    df = df[df['amino_acid_change'] == amino_acid_change]
    cell_lines = df['case_id'].unique().tolist()
    cell_lines = [x.split('_')[0] for x in cell_lines]
    return cell_lines

def _filter_data_frame(df, data_col, filter_col, filter_str=None):
    """Return a filtered data frame as a dictionary."""
    if filter_str is not None:
        relevant_cols = data_col + [filter_col]
        df.dropna(inplace=True, subset=relevant_cols)
        row_filter = df[filter_col].str.contains(filter_str, case=False)
        data_list = df[row_filter][data_col].to_dict()
    else:
        data_list = df[data_col].to_dict()
    return data_list
