from __future__ import absolute_import, print_function, unicode_literals
from builtins import dict, str

__all__ = ['get_statements', 'get_statements_for_paper', 'IndraDBRestError']

import requests

from indra import get_config
from indra.statements import stmts_from_json, get_statement_by_name, \
    get_all_descendants, make_statement_camel


class IndraDBRestError(Exception):
    def __init__(self, status_code, reason):
        self.status_code = status_code
        self.reason = reason
        super(IndraDBRestError, self).__init__('Got bad return code %d: %s'
                                               % (status_code, reason))
        return


def _make_stmts_query(agent_strs, params):
    """Slightly lower level function to get statements from the REST API."""
    resp = _submit_request('statements', *agent_strs, **params)
    stmts_json = resp.json()
    return stmts_from_json(stmts_json)


def get_statements(subject=None, object=None, agents=None, stmt_type=None,
                   use_exact_type=False):
    """Get statements from INDRA's database using the web api.

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
        you do not want this behavior, set use_exact_type=True.
    use_exact_type : bool
        If stmt_type is given, and you only want to search for that specific
        statement type, set this to True. Default is False.

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
    agent_strs = [] if agents is None else ['agent=%s' % ag for ag in agents]
    key_val_list = [('subject', subject), ('object', object)]
    params = {param_key: param_val for param_key, param_val in key_val_list
              if param_val is not None}

    # Handle the type(s).
    if stmt_type is not None:
        if use_exact_type:
            params['type'] = stmt_type
            stmts = _make_stmts_query(agent_strs, params)
        else:
            stmts = []
            stmt_class = get_statement_by_name(stmt_type)
            descendant_classes = get_all_descendants(stmt_class)
            search_classes = descendant_classes + [stmt_class]
            for stmt_class in search_classes:
                params['type'] = stmt_class.__name__
                stmts.extend(_make_stmts_query(agent_strs, params))
    else:
        stmts = _make_stmts_query(agent_strs, params)
    return stmts


def get_statements_for_paper(id_val, id_type='pmid'):
    """Get the set of raw Statements extracted from a paper given by the id.

    Note that in the future this will draw upon preassembled Statements.

    Parameters
    ----------
    id_val : str or int
        The value of the id of the paper of interest.
    id_type : str
        This may be one of 'pmid', 'pmcid', 'doi', 'pii', 'manuscript id', or
        'trid', which is the primary key id of the text references in the
        database. The default is 'pmid'.

    Returns
    -------
    stmts : list[:py:class:`indra.statements.Statement`]
        A list of INDRA Statement instances.
    """
    resp = _submit_request('papers', id=id_val, type=id_type)
    stmts_json = resp.json()
    return stmts_from_json(stmts_json)


def _submit_request(end_point, *args, **kwargs):
    """Low level function to make the request to the rest API."""
    query_str = '?' + '&'.join(['%s=%s' % (k, v) for k, v in kwargs.items()]
                               + list(args))
    url = get_config('INDRA_DB_REST_URL', failure_ok=False)
    api_key = get_config('INDRA_DB_REST_API_KEY', failure_ok=False)
    resp = requests.get(url + ('/%s/' % end_point) + query_str,
                        headers={'x-api-key': api_key})
    if resp.status_code == 200:
        return resp
    else:
        if hasattr(resp, 'text') and resp.text:
            raise IndraDBRestError(resp.status_code, resp.text)
        else:
            raise IndraDBRestError(resp.status_code, resp.reason)
