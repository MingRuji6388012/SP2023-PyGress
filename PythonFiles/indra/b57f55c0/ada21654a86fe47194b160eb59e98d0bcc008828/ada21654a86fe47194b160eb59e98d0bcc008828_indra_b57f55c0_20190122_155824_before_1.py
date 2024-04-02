from indra.util import clockit
from indra.statements import get_statement_by_name, get_all_descendants, \
    stmts_from_json

from indra.sources.indra_db_rest.processor import IndraDBRestProcessor
from indra.sources.indra_db_rest.util import submit_statement_request, \
    make_db_rest_request

__all__ = ['get_statements', 'get_statements_for_paper',
           'get_statements_by_hash', 'submit_curation']


@clockit
def get_statements(subject=None, object=None, agents=None, stmt_type=None,
                   use_exact_type=False, persist=True, timeout=None,
                   simple_response=False, ev_limit=10, best_first=True, tries=2,
                   max_stmts=None):
    """Get Statements from the INDRA DB web API matching given agents and type.

    There are two types of response available. You can just get a list of
    INDRA Statements, or you can get an IndraRestResponse object, which allows
    Statements to be loaded in a background thread, providing a sample of the
    best* content available promptly in the sample_statements attribute, and
    populates the statements attribute when the paged load is complete.

    *In the sense of having the most supporting evidence.

    Parameters
    ----------
    subject/object : str
        Optionally specify the subject and/or object of the statements in
        you wish to get from the database. By default, the namespace is assumed
        to be HGNC gene names, however you may specify another namespace by
        including `@<namespace>` at the end of the name string. For example, if
        you want to specify an agent by chebi, you could use `CHEBI:6801@CHEBI`,
        or if you wanted to use the HGNC id, you could use `6871@HGNC`.
    agents : list[str]
        A list of agents, specified in the same manner as subject and object,
        but without specifying their grammatical position.
    stmt_type : str
        Specify the types of interactions you are interested in, as indicated
        by the sub-classes of INDRA's Statements. This argument is *not* case
        sensitive. If the statement class given has sub-classes
        (e.g. RegulateAmount has IncreaseAmount and DecreaseAmount), then both
        the class itself, and its subclasses, will be queried, by default. If
        you do not want this behavior, set use_exact_type=True. Note that if
        max_stmts is set, it is possible only the exact statement type will
        be returned, as this is the first searched. The processor then cycles
        through the types, getting a page of results for each type and adding it
        to the quota, until the max number of statements is reached.
    use_exact_type : bool
        If stmt_type is given, and you only want to search for that specific
        statement type, set this to True. Default is False.
    persist : bool
        Default is True. When False, if a query comes back limited (not all
        results returned), just give up and pass along what was returned.
        Otherwise, make further queries to get the rest of the data (which may
        take some time).
    timeout : positive int or None
        If an int, block until the work is done and statements are retrieved, or
        until the timeout has expired, in which case the results so far will be
        returned in the response object, and further results will be added in
        a separate thread as they become available. If simple_response is True,
        all statements available will be returned. Otherwise (if None), block
        indefinitely until all statements are retrieved. Default is None.
    simple_response : bool
        If True, a simple list of statements is returned (thus block should also
        be True). If block is False, only the original sample will be returned
        (as though persist was False), until the statements are done loading, in
        which case the rest should appear in the list. This behavior is not
        encouraged. Default is True (for the sake of backwards compatibility).
    ev_limit : int or None
        Limit the amount of evidence returned per Statement. Default is 10.
    best_first : bool
        If True, the preassembled statements will be sorted by the amount of
        evidence they have, and those with the most evidence will be
        prioritized. When using `max_stmts`, this means you will get the "best"
        statements. If False, statements will be queried in arbitrary order.
    tries : int > 0
        Set the number of times to try the query. The database often caches
        results, so if a query times out the first time, trying again after a
        timeout will often succeed fast enough to avoid a timeout. This can also
        help gracefully handle an unreliable connection, if you're willing to
        wait. Default is 2.
    max_stmts : int or None
        Select the maximum number of statements to return. When set less than
        1000 the effect is much the same as setting persist to false, and will
        guarantee a faster response. Default is None.

    Returns
    -------
    stmts : list[:py:class:`indra.statements.Statement`]
        A list of INDRA Statement instances. Note that if a supporting or
        supported Statement was not included in your query, it will simply be
        instantiated as an `Unresolved` statement, with `uuid` of the statement.
    """
    # Make sure we got at least SOME agents (the remote API will error if we
    # we proceed with no arguments.
    if subject is None and object is None and agents is None:
        raise ValueError("At least one agent must be specified, or else "
                         "the scope will be too large.")

    # Formulate inputs for the agents..
    agent_strs = [] if agents is None else ['agent%d=%s' % (i, ag)
                                            for i, ag in enumerate(agents)]
    key_val_list = [('subject', subject), ('object', object)]
    params = {param_key: param_val for param_key, param_val in key_val_list
              if param_val is not None}
    params['best_first'] = best_first
    params['ev_limit'] = ev_limit
    params['tries'] = tries

    # Handle the type(s).
    stmt_types = [stmt_type] if stmt_type else []
    if stmt_type is not None and not use_exact_type:
        stmt_class = get_statement_by_name(stmt_type)
        descendant_classes = get_all_descendants(stmt_class)
        stmt_types += [cls.__name__ for cls in descendant_classes]

    # Get the response object
    resp = IndraDBRestProcessor(max_stmts=max_stmts)
    resp.make_stmts_queries(agent_strs, stmt_types, params, persist, timeout)

    # Format the result appropriately.
    if simple_response:
        ret = resp.statements
    else:
        ret = resp
    return ret


@clockit
def get_statements_by_hash(hash_list, ev_limit=100, best_first=True, tries=2):
    """Get fully formed statements from a list of hashes.

    Parameters
    ----------
    hash_list : list[int or str]
        A list of statement hashes.
    ev_limit : int or None
        Limit the amount of evidence returned per Statement. Default is 100.
    best_first : bool
        If True, the preassembled statements will be sorted by the amount of
        evidence they have, and those with the most evidence will be
        prioritized. When using `max_stmts`, this means you will get the "best"
        statements. If False, statements will be queried in arbitrary order.
    tries : int > 0
        Set the number of times to try the query. The database often caches
        results, so if a query times out the first time, trying again after a
        timeout will often succeed fast enough to avoid a timeout. This can
        also help gracefully handle an unreliable connection, if you're
        willing to wait. Default is 2.
    """
    if not isinstance(hash_list, list):
        raise ValueError("The `hash_list` input is a list, not %s."
                         % type(hash_list))
    if not hash_list:
        return []
    if isinstance(hash_list[0], str):
        hash_list = [int(h) for h in hash_list]
    if not all([isinstance(h, int) for h in hash_list]):
        raise ValueError("Hashes must be ints or strings that can be "
                         "converted into ints.")
    resp = submit_statement_request('post', 'from_hashes', ev_limit=ev_limit,
                                    data={'hashes': hash_list},
                                    best_first=best_first, tries=tries)
    return stmts_from_json(resp.json()['statements'].values())


@clockit
def get_statements_for_paper(ids, ev_limit=10, best_first=True, tries=2,
                             max_stmts=None):
    """Get the set of raw Statements extracted from a paper given by the id.

    Parameters
    ----------
    ids : list[(<id type>, <id value>)]
        A list of tuples with ids and their type. The type can be any one of
        'pmid', 'pmcid', 'doi', 'pii', 'manuscript id', or 'trid', which is the
        primary key id of the text references in the database.
    ev_limit : int or None
        Limit the amount of evidence returned per Statement. Default is 10.
    best_first : bool
        If True, the preassembled statements will be sorted by the amount of
        evidence they have, and those with the most evidence will be
        prioritized. When using `max_stmts`, this means you will get the "best"
        statements. If False, statements will be queried in arbitrary order.
    tries : int > 0
        Set the number of times to try the query. The database often caches
        results, so if a query times out the first time, trying again after a
        timeout will often succeed fast enough to avoid a timeout. This can also
        help gracefully handle an unreliable connection, if you're willing to
        wait. Default is 2.
    max_stmts : int or None
        Select a maximum number of statements to be returned. Default is None.

    Returns
    -------
    stmts : list[:py:class:`indra.statements.Statement`]
        A list of INDRA Statement instances.
    """
    id_l = [{'id': id_val, 'type': id_type} for id_type, id_val in ids]
    resp = submit_statement_request('post', 'from_papers', data={'ids': id_l},
                                    ev_limit=ev_limit, best_first=best_first,
                                    tries=tries, max_stmts=max_stmts)
    stmts_json = resp.json()['statements']
    return stmts_from_json(stmts_json.values())


def submit_curation(hash_val, tag, curator, text=None,
                    source='indra_rest_client', ev_hash=None, is_test=False):
    """Submit a curation for the given statement at the relevant level.

    Parameters
    ----------
    hash_val : int
        The hash corresponding to the statement.
    tag : str
        A very short phrase categorizing the error or type of curation,
        e.g. "grounding" for a grounding error, or "correct" if you are
        marking a statement as correct.
    curator : str
        The name or identifier for the curator.
    text : str
        A brief description of the problem.
    source : str
        The name of the access point through which the curation was performed.
        The default is 'direct_client', meaning this function was used
        directly. Any higher-level application should identify itself here.
    ev_hash : int
        A hash of the sentence and other evidence information. Elsewhere
        referred to as `source_hash`.
    is_test : bool
        Used in testing. If True, no curation will actually be added to the
        database.
    """
    data = {'tag': tag, 'text': text, 'curator': curator, 'source': source,
            'ev_hash': ev_hash}
    url = 'curation/submit/%s' % hash_val
    if is_test:
        qstr = '?test'
    else:
        qstr = ''
    return make_db_rest_request('post', url, qstr, data=data)


