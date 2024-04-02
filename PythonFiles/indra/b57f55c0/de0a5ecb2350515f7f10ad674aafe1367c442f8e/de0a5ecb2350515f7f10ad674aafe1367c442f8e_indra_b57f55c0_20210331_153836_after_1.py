__all__ = ['get_statements', 'get_statements_for_paper',
           'get_statements_by_hash', 'get_statements_from_query',
           'submit_curation', 'get_curations']

from indra.util import clockit
from indra.statements import Complex, SelfModification,  ActiveForm, \
    Translocation, Conversion

from indra.sources.indra_db_rest.query import *
from indra.sources.indra_db_rest.processor import DBQueryStatementProcessor
from indra.sources.indra_db_rest.util import make_db_rest_request, get_url_base


@clockit
def get_statements(subject=None, object=None, agents=None, stmt_type=None,
                   use_exact_type=False, limit=None, persist=True, timeout=None,
                   strict_stop=False, ev_limit=10, filter_ev=True,
                   sort_by='ev_count', tries=3, api_key=None):
    """Get a processor for the INDRA DB web API matching given agents and type.

    You get an IndraDBRestProcessor object, which allow Statements to be loaded
    in a background thread, providing a sample of the "best" content available
    promptly in the sample_statements attribute, and populates the statements
    attribute when the paged load is complete. The "best" is determined by the
    `sort_by` attribute, which may be either 'belief' or 'ev_count' or None.

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
    limit : int or None
        Select the maximum number of statements to return. When set less than
        500 the effect is much the same as setting persist to false, and will
        guarantee a faster response. Default is None.
    persist : bool
        Default is True. When False, if a query comes back limited (not all
        results returned), just give up and pass along what was returned.
        Otherwise, make further queries to get the rest of the data (which may
        take some time).
    timeout : positive int or None
        If an int, block until the work is done and statements are retrieved, or
        until the timeout has expired, in which case the results so far will be
        returned in the response object, and further results will be added in
        a separate thread as they become available. Block indefinitely until all
        statements are retrieved. Default is None.
    strict_stop : bool
        If True, the query will only be given timeout to complete before being
        abandoned entirely. Otherwise the timeout will simply wait for the
        thread to join for `timeout` seconds before returning, allowing other
        work to continue while the query runs in the background. The default is
        False.
    ev_limit : int or None
        Limit the amount of evidence returned per Statement. Default is 10.
    filter_ev : bool
        Indicate whether evidence should have the same filters applied as
        the statements themselves, where appropriate (e.g. in the case of a
        filter by paper).
    sort_by : str or None
        Str options are currently 'ev_count' or 'belief'. Results will return in
        order of the given parameter. If None, results will be turned in an
        arbitrary order.
    tries : int > 0
        Set the number of times to try the query. The database often caches
        results, so if a query times out the first time, trying again after a
        timeout will often succeed fast enough to avoid a timeout. This can also
        help gracefully handle an unreliable connection, if you're willing to
        wait. Default is 3.
    api_key : str or None
        Override or use in place of the API key given in the INDRA config file.

    Returns
    -------
    processor : :py:class:`IndraDBRestSearchProcessor`
        An instance of the IndraDBRestProcessor, which has an attribute
        `statements` which will be populated when the query/queries are done.
    """
    query = EmptyQuery()

    def add_agent(ag_str, role):
        if ag_str is None:
            return

        nonlocal query
        if '@' in ag_str:
            ag_id, ag_ns = ag_str.split('@')
        else:
            ag_id = ag_str
            ag_ns = 'NAME'
        query &= HasAgent(ag_id, ag_ns, role=role)

    add_agent(subject, 'subject')
    add_agent(object, 'object')
    if agents is not None:
        for ag in agents:
            add_agent(ag, None)

    if stmt_type is not None:
        query &= HasType([stmt_type], include_subclasses=not use_exact_type)

    if isinstance(query, EmptyQuery):
        raise ValueError("No constraints provided.")

    return DBQueryStatementProcessor(query, limit=limit, persist=persist,
                                     ev_limit=ev_limit, timeout=timeout,
                                     sort_by=sort_by, tries=tries,
                                     strict_stop=strict_stop,
                                     filter_ev=filter_ev, api_key=api_key)


@clockit
def get_statements_by_hash(hash_list, limit=None, ev_limit=10, filter_ev=True,
                           sort_by='ev_count', persist=True, timeout=None,
                           strict_stop=False, tries=3, api_key=None):
    """Get fully formed statements from a list of hashes.

    Parameters
    ----------
    hash_list : list[int or str]
        A list of statement hashes.
    limit : int or None
        Select the maximum number of statements to return. When set less than
        500 the effect is much the same as setting persist to false, and will
        guarantee a faster response. Default is None.
    ev_limit : int or None
        Limit the amount of evidence returned per Statement. Default is 100.
    filter_ev : bool
        Indicate whether evidence should have the same filters applied as
        the statements themselves, where appropriate (e.g. in the case of a
        filter by paper).
    sort_by : str or None
        Options are currently 'ev_count' or 'belief'. Results will return in
        order of the given parameter. If None, results will be turned in an
        arbitrary order.
    persist : bool
        Default is True. When False, if a query comes back limited (not all
        results returned), just give up and pass along what was returned.
        Otherwise, make further queries to get the rest of the data (which may
        take some time).
    timeout : positive int or None
        If an int, return after `timeout` seconds, even if query is not done.
        Default is None.
    strict_stop : bool
        If True, the query will only be given timeout to complete before being
        abandoned entirely. Otherwise the timeout will simply wait for the
        thread to join for `timeout` seconds before returning, allowing other
        work to continue while the query runs in the background. The default is
        False.
    tries : int > 0
        Set the number of times to try the query. The database often caches
        results, so if a query times out the first time, trying again after a
        timeout will often succeed fast enough to avoid a timeout. This can
        also help gracefully handle an unreliable connection, if you're
        willing to wait. Default is 3.
    api_key : str or None
        Override or use in place of the API key given in the INDRA config file.

    Returns
    -------
    processor : :py:class:`IndraDBRestSearchProcessor`
        An instance of the IndraDBRestProcessor, which has an attribute
        `statements` which will be populated when the query/queries are done.
    """
    return DBQueryStatementProcessor(HasHash(hash_list), limit=limit,
                                     ev_limit=ev_limit, sort_by=sort_by,
                                     persist=persist, timeout=timeout,
                                     tries=tries, filter_ev=filter_ev,
                                     strict_stop=strict_stop, api_key=api_key)


@clockit
def get_statements_for_paper(ids, limit=None, ev_limit=10, sort_by='ev_count',
                             persist=True, timeout=None, strict_stop=False,
                             tries=3, filter_ev=True, api_key=None):
    """Get the set of raw Statements extracted from a paper given by the id.

    Parameters
    ----------
    ids : list[(<id type>, <id value>)]
        A list of tuples with ids and their type. The type can be any one of
        'pmid', 'pmcid', 'doi', 'pii', 'manuscript id', or 'trid', which is the
        primary key id of the text references in the database.
    limit : int or None
        Select the maximum number of statements to return. When set less than
        500 the effect is much the same as setting persist to false, and will
        guarantee a faster response. Default is None.
    ev_limit : int or None
        Limit the amount of evidence returned per Statement. Default is 10.
    filter_ev : bool
        Indicate whether evidence should have the same filters applied as
        the statements themselves, where appropriate (e.g. in the case of a
        filter by paper).
    sort_by : str or None
        Options are currently 'ev_count' or 'belief'. Results will return in
        order of the given parameter. If None, results will be turned in an
        arbitrary order.
    persist : bool
        Default is True. When False, if a query comes back limited (not all
        results returned), just give up and pass along what was returned.
        Otherwise, make further queries to get the rest of the data (which may
        take some time).
    timeout : positive int or None
        If an int, return after `timeout` seconds, even if query is not done.
        Default is None.
    strict_stop : bool
        If True, the query will only be given timeout to complete before being
        abandoned entirely. Otherwise the timeout will simply wait for the
        thread to join for `timeout` seconds before returning, allowing other
        work to continue while the query runs in the background. The default is
        False.
    tries : int > 0
        Set the number of times to try the query. The database often caches
        results, so if a query times out the first time, trying again after a
        timeout will often succeed fast enough to avoid a timeout. This can also
        help gracefully handle an unreliable connection, if you're willing to
        wait. Default is 3.
    api_key : str or None
        Override or use in place of the API key given in the INDRA config file.

    Returns
    -------
    processor : :py:class:`IndraDBRestSearchProcessor`
        An instance of the IndraDBRestProcessor, which has an attribute
        `statements` which will be populated when the query/queries are done.
    """
    return DBQueryStatementProcessor(FromPapers(ids), limit=limit,
                                     ev_limit=ev_limit, sort_by=sort_by,
                                     persist=persist, timeout=timeout,
                                     tries=tries, filter_ev=filter_ev,
                                     strict_stop=strict_stop, api_key=api_key)


@clockit
def get_statements_from_query(query, limit=None, ev_limit=10,
                              sort_by='ev_count', persist=True, timeout=None,
                              strict_stop=False, tries=3, filter_ev=True,
                              api_key=None):
    """Get the set of raw Statements extracted from a paper given by the id.

    Parameters
    ----------
    query : :py:class:`Query`
        The query to be evaluated in return for statements.
    limit : int or None
        Select the maximum number of statements to return. When set less than
        500 the effect is much the same as setting persist to false, and will
        guarantee a faster response. Default is None.
    ev_limit : int or None
        Limit the amount of evidence returned per Statement. Default is 10.
    filter_ev : bool
        Indicate whether evidence should have the same filters applied as
        the statements themselves, where appropriate (e.g. in the case of a
        filter by paper).
    sort_by : str or None
        Options are currently 'ev_count' or 'belief'. Results will return in
        order of the given parameter. If None, results will be turned in an
        arbitrary order.
    persist : bool
        Default is True. When False, if a query comes back limited (not all
        results returned), just give up and pass along what was returned.
        Otherwise, make further queries to get the rest of the data (which may
        take some time).
    timeout : positive int or None
        If an int, return after `timeout` seconds, even if query is not done.
        Default is None.
    strict_stop : bool
        If True, the query will only be given `timeout` time to complete before
        being abandoned entirely. Otherwise the timeout will simply wait for the
        thread to join for `timeout` seconds before returning, allowing other
        work to continue while the query runs in the background. The default is
        False.
    tries : int > 0
        Set the number of times to try the query. The database often caches
        results, so if a query times out the first time, trying again after a
        timeout will often succeed fast enough to avoid a timeout. This can also
        help gracefully handle an unreliable connection, if you're willing to
        wait. Default is 3.
    api_key : str or None
        Override or use in place of the API key given in the INDRA config file.

    Returns
    -------
    processor : :py:class:`IndraDBRestSearchProcessor`
        An instance of the IndraDBRestProcessor, which has an attribute
        `statements` which will be populated when the query/queries are done.
    """
    return DBQueryStatementProcessor(query, limit=limit,
                                     ev_limit=ev_limit, sort_by=sort_by,
                                     persist=persist, timeout=timeout,
                                     tries=tries, filter_ev=filter_ev,
                                     strict_stop=strict_stop, api_key=api_key)


def submit_curation(hash_val, tag, curator_email, text=None,
                    source='indra_rest_client', ev_hash=None, pa_json=None,
                    ev_json=None, api_key=None, is_test=False):
    """Submit a curation for the given statement at the relevant level.

    Parameters
    ----------
    hash_val : int
        The hash corresponding to the statement.
    tag : str
        A very short phrase categorizing the error or type of curation,
        e.g. "grounding" for a grounding error, or "correct" if you are
        marking a statement as correct.
    curator_email : str
        The email of the curator.
    text : str
        A brief description of the problem.
    source : str
        The name of the access point through which the curation was performed.
        The default is 'direct_client', meaning this function was used
        directly. Any higher-level application should identify itself here.
    ev_hash : int
        A hash of the sentence and other evidence information. Elsewhere
        referred to as `source_hash`.
    pa_json : None or dict
        The JSON of a statement you wish to curate. If not given, it may be
        inferred (best effort) from the given hash.
    ev_json : None or dict
        The JSON of an evidence you wish to curate. If not given, it cannot be
        inferred.
    api_key : str or None
        Override or use in place of the API key given in the INDRA config file.
    is_test : bool
        Used in testing. If True, no curation will actually be added to the
        database.
    """
    data = {'tag': tag, 'text': text, 'email': curator_email, 'source': source,
            'ev_hash': ev_hash, 'pa_json': pa_json, 'ev_json': ev_json}
    url = 'curation/submit/%s' % hash_val
    if is_test:
        qstr = '?test'
    else:
        qstr = ''
    resp = make_db_rest_request('post', url, qstr, data=data, api_key=api_key)
    return resp.json()


def get_curations(hash_val=None, source_hash=None, api_key=None):
    """Get the curations for a specific statement and evidence.

    If neither hash_val nor source_hash are given, all curations will be
    retrieved. This will require the user to have extra permissions, as
    determined by their API key.

    Parameters
    ----------
    hash_val : int or None
        The hash of a statement whose curations you want to retrieve.
    source_hash : int or None
        The hash generated for a piece of evidence for which you want curations.
        The `hash_val` must be provided to use the `source_hash`.
    api_key : str or None
        Override or use in place of the API key given in the INDRA config file.

    Returns
    -------
    curations : list
        A list of dictionaries containing the curation data.
    """
    url = 'curation/list'
    if hash_val is not None:
        url += f'/{hash_val}'
        if source_hash is not None:
            url += f'/{source_hash}'
    elif source_hash is not None:
        raise ValueError("A hash_val must be given if a source_hash is given.")
    resp = make_db_rest_request('get', url, api_key=api_key)
    return resp.json()


def get_statement_queries(stmts, fallback_ns='NAME', pick_ns_fun=None,
                          **params):
    """Get queries used to search based on a statement.

    In addition to the stmts, you can enter any parameters standard to the
    query. See https://github.com/indralab/indra_db/rest_api for a full list.

    Parameters
    ----------
    stmts : list[Statement]
        A list of INDRA statements.
    fallback_ns : Optional[str]
        The name space to search by when an Agent in a Statement is not
        grounded to one of the standardized name spaces. Typically,
        searching by 'NAME' (i.e., the Agent's name) is a good option if
        (1) An Agent's grounding is missing but its name is
        known to be standard in one of the name spaces. In this case the
        name-based lookup will yield the same result as looking up by
        grounding. Example: MAP2K1(db_refs={})
        (2) Any Agent that is encountered with the same name as this Agent
        is never standardized, so looking up by name yields the same result
        as looking up by TEXT. Example: xyz(db_refs={'TEXT': 'xyz'})
        Searching by TEXT is better in other cases e.g., when the given
        specific Agent is not grounded but we have other Agents with the
        same TEXT that are grounded and then standardized to a different name.
        Example: Erk(db_refs={'TEXT': 'Erk'}).
        Default: 'NAME'
    pick_ns_fun : Optional[function]
        An optional user-supplied function which takes an Agent as input and
        returns a string of the form value@ns where 'value' will be looked
        up in namespace 'ns' to search for the given Agent.
    **params : kwargs
        A set of keyword arguments that are added as parameters to the
        query URLs.
    """
    def pick_ns(ag):
        # If the Agent has grounding, in order of preference, in any of these
        # name spaces then we look it up based on grounding.
        for ns in ['FPLX', 'HGNC', 'UP', 'CHEBI', 'GO', 'MESH']:
            if ns in ag.db_refs:
                dbid = ag.db_refs[ns]
                return '%s@%s' % (dbid, ns)
        # Otherwise we fall back on searching by NAME or TEXT
        # (or any other given name space as long as the Agent name can be
        # usefully looked up in that name space).
        return '%s@%s' % (ag.name, fallback_ns)

    pick_ns_fun = pick_ns if not pick_ns_fun else pick_ns_fun

    queries = []
    url_base = get_url_base('statements/from_agents')
    non_binary_statements = (Complex, SelfModification, ActiveForm,
                             Translocation, Conversion)
    for stmt in stmts:
        kwargs = {}
        if not isinstance(stmt, non_binary_statements):
            for pos, ag in zip(['subject', 'object'], stmt.agent_list()):
                if ag is not None:
                    kwargs[pos] = pick_ns_fun(ag)
        else:
            for i, ag in enumerate(stmt.agent_list()):
                if ag is not None:
                    kwargs['agent%d' % i] = pick_ns_fun(ag)
        kwargs['type'] = stmt.__class__.__name__
        kwargs.update(params)
        query_str = '?' + '&'.join(['%s=%s' % (k, v) for k, v in kwargs.items()
                                    if v is not None])
        queries.append(url_base + query_str)
    return queries
