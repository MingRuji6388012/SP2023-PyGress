import sys
import json
import logging

from flask import Flask, request, abort, jsonify, Response
from flask_compress import Compress
from flask_cors import CORS

from indra.db import get_primary_db
from indra.db.client import get_statements_by_gene_role_type, \
    get_statements_by_paper, get_statements_from_hashes
from indra.statements import make_statement_camel
from indra.databases import hgnc_client

logger = logging.getLogger("db-api")

app = Flask(__name__)
Compress(app)
CORS(app)


MAX_STATEMENTS = int(1e4)


class DbAPIError(Exception):
    pass


def __process_agent(agent_param):
    """Get the agent id and namespace from an input param."""
    if not agent_param.endswith('TEXT'):
        param_parts = agent_param.split('@')
        if len(param_parts) == 2:
            ag, ns = param_parts
        elif len(param_parts) == 1:
            ag = agent_param
            ns = 'HGNC-SYMBOL'
        else:
            raise DbAPIError('Unrecognized agent spec: \"%s\"' % agent_param)
    else:
        ag = agent_param[:-5]
        ns = 'TEXT'

    if ns == 'HGNC-SYMBOL':
        original_ag = ag
        ag = hgnc_client.get_hgnc_id(original_ag)
        if ag is None and 'None' not in agent_param:
            raise DbAPIError('Invalid agent name: \"%s\"' % original_ag)
        ns = 'HGNC'

    return ag, ns


def _filter_statements(stmts_in, ns, ag_id, role=None):
    """Return statements filtered to ones where agent is at given position."""
    # Make sure the role is good.
    assert role in ['SUBJECT', 'OBJECT', None], \
        "The value of role must be either 'SUBJECT', 'OBJECT', or None."

    # Map the role to an index:
    agent_pos = 0 if role == 'SUBJECT' else 1 if role == 'OBJECT' else None

    # Filter the statements.
    stmts_out = []
    for stmt in stmts_in:
        # Make sure the statement has enough agents to get the one at the
        # position of interest e.g. has only 1 agent but the agent_pos is not 0
        agents = stmt.agent_list()
        if agent_pos is not None:
            if len(agents) <= agent_pos:
                continue
            # Get the agent at the position of interest and make sure it's an
            # actual Agent
            agent = agents[agent_pos]
            if agent is not None:
                # Check if the db_refs for the namespace of interest matches the
                # value
                if agent.db_refs.get(ns) == ag_id:
                    stmts_out.append(stmt)
        else:
            # Search through all the agents looking for an agent with a matching
            # db ref.
            for agent in agents:
                if agent is not None and agent.db_refs.get(ns) == ag_id:
                    stmts_out.append(stmt)
                    break
    return stmts_out


def _get_relevant_statements(stmts, ag_id, ns, stmt_type, role=None):
    """Get statements that are relevant to the criteria included.

    If stmts is an empty list or None (bool evaluates to False), then get a
    matching set of statements from the database. Otherwise, filter down the
    existing list of statements.
    """
    logger.debug("Checking agent %s in namespace %s." % (ag_id, ns))
    # TODO: This is a temporary measure, remove ASAP.
    if role:
        role = role.upper()

    if not stmts:
        # Get an initial list
        stmts = get_statements_by_gene_role_type(agent_id=ag_id, agent_ns=ns,
                                                 role=role, stmt_type=stmt_type,
                                                 do_stmt_count=False,
                                                 with_evidence=False,
                                                 with_support=False)
    else:
        stmts = _filter_statements(stmts, ns, ag_id, role)

    return stmts


@app.route('/')
def welcome():
    logger.info("Got request for welcome info.")
    return Response("Welcome the the INDRA database webservice!\n"
                    "\n"
                    "Use modes:\n"
                    "----------\n"
                    "/            - (you are here) Welcome page.\n"
                    "/statements  - Get detailed instructions for querying "
                    "statements.\n"
                    "/statements/?<query_string> - Get a list of statement "
                    "jsons."
                    "\n")


@app.route('/statements', methods=['GET'])
def get_statements_query_format():
    return Response('To get a list of statements, include a query after '
                    '/statements/ with the following keys:\n\n'
                    'type : the type of interaction (e.g. Phosphorylation)\n'
                    'namespace : select the namespace in which agents are '
                    'identified.\n'
                    '[subject, object, agent] : the agents, indicated by '
                    'their role. Note that at least one agent is needed in '
                    'a query. If agent is use, that agent will be matched to '
                    'any argument in the statement.\n\n'
                    'For example: /statements/?subject=MAP2K1&object=MAPK1'
                    '&type=Phosphorylation'
                    'Most statements have a subject and an object, but unary '
                    'and n-ary statements should have agents specified by '
                    '\"other\".')


@app.route('/statements/', methods=['GET'])
def get_statements():
    """Get some statements constrained by query."""
    logger.info("Got query for statements!")

    query_dict = request.args.copy()
    limit_behavior = query_dict.pop('on_limit', 'sample')
    if limit_behavior not in ['sample', 'truncate', 'error']:
        abort(Response('Unrecognized value for on_limit: %s' % limit_behavior,
                       400))

    logger.info("Getting query details.")
    try:
        # Get the agents without specified locations (subject or object).
        free_agents = [__process_agent(ag)
                       for ag in query_dict.poplist('agent')]

        # Get the agents with specified roles.
        roled_agents = {role: __process_agent(query_dict.pop(role))
                        for role in ['subject', 'object']
                        if query_dict.get(role) is not None}
    except DbAPIError as e:
        logger.exception(e)
        abort(Response('Failed to make agents from names: %s\n' % str(e), 400))
        return

    # Get the raw name of the statement type (we allow for variation in case).
    act_uncamelled = query_dict.pop('type', None)

    # Fix the case, if we got a statement type.
    if act_uncamelled is not None:
        act = make_statement_camel(act_uncamelled)
    else:
        act = None

    # If there was something else in the query, there shouldn't be, so someone's
    # probably confused.
    if query_dict:
        abort(Response("Unrecognized query options; %s." %
                       list(query_dict.keys()),
                       400))
        return

    # Make sure we got SOME agents. We will not simply return all
    # phosphorylations, or all activations.
    if not any(roled_agents.values()) and not free_agents:
        logger.error("No agents.")
        abort(Response(("No agents. Must have 'subject', 'object', or "
                        "'other'!\n"), 400))

    # Check to make sure none of the agents are None.
    assert None not in roled_agents.values() and None not in free_agents, \
        "None agents found. No agents should be None."

    # Now find the statements.
    logger.info("Getting statements...")

    # First look for statements matching the role'd agents.
    agent_iter = [(role, ag_dbid, ns)
                  for role, (ag_dbid, ns) in roled_agents.items()]
    agent_iter += [(None, ag_dbid, ns) for ag_dbid, ns in free_agents]
    db = get_primary_db()
    sub_q = None
    for role, ag_dbid, ns in agent_iter:
        # Create this query (for this agent)
        q = db.filter_query([db.PaMeta.mk_hash, db.PaMeta.ev_count],
                            db.PaMeta.db_id.like(ag_dbid),
                            db.PaMeta.db_name.like(ns))
        if act is not None:
            q = q.filter(db.PaMeta.type.like(act))

        if role is not None:
            q = q.filter(db.PaMeta.role == role.upper())

        # Intersect with the previous query.
        if sub_q:
            sub_q = sub_q.intersect(q)
        else:
            sub_q = q
    assert sub_q, "No conditions imposed."
    sub_q = sub_q.distinct()
    sub_al = sub_q.subquery('mk_hashes')

    if hasattr(sub_al.c, 'mk_hash'):
        link = db.FastRawPaLink.mk_hash == sub_al.c.mk_hash
    elif hasattr(sub_al.c, 'pa_meta_mk_hash'):
        link = db.FastRawPaLink.mk_hash == sub_al.c.pa_meta_mk_hash
    else:
        raise DbAPIError("Cannot find correct attribute to use for linking: %s"
                         % str(sub_al.c._all_columns))

    # Get the statements from reading
    stmts_dict = {}
    master_q = (db.filter_query([db.FastRawPaLink.mk_hash,
                                db.FastRawPaLink.raw_json,
                                db.FastRawPaLink.pa_json,
                                db.ReadingRefLink.pmid], link)
                .outerjoin(db.FastRawPaLink.reading_ref))

    # TODO: Do better than truncating.
    # Specifically, this should probably be an order-by a parameter such as
    # evidence count and/or support count.
    res = master_q.limit(MAX_STATEMENTS).all()
    for mk_hash, raw_json_bts, pa_json_bts, pmid in res:
        raw_json = json.loads(raw_json_bts.decode('utf-8'))
        if mk_hash not in stmts_dict.keys():
            stmts_dict[mk_hash] = json.loads(pa_json_bts.decode('utf-8'))
            stmts_dict[mk_hash]['evidence'] = []
        if pmid:
            raw_json['evidence'][0]['pmid'] = pmid
        stmts_dict[mk_hash]['evidence'].append(raw_json['evidence'][0])
    resp = jsonify({'statements': list(stmts_dict.values()), 'limited': True})
    logger.info("Exiting with %d statements of nominal size %f MB."
                % (len(stmts_dict), sys.getsizeof(resp.data)/1e6))
    return resp


@app.route('/statements/from_hashes', methods=['POST', 'GET'])
def get_statements_by_hash():
    hashes = request.json.get('hashes')
    if not hashes:
        logger.error("No hashes provided!")
        abort(Response("No hashes given!", 400))
    if len(hashes) > MAX_STATEMENTS:
        logger.error("Too many hashes given!")
        abort(Response("Too many hashes given, %d allowed." % MAX_STATEMENTS,
                       400))

    stmts = get_statements_from_hashes(hashes, with_support=True)
    resp = jsonify({'statements': [s.to_json() for s in stmts if s.evidence]})
    logger.info("Exiting with %d statements of nominal size %f MB."
                % (len(stmts), sys.getsizeof(resp.data)/1e6))
    return resp


@app.route('/papers/', methods=['GET'])
def get_paper_statements():
    """Get and preassemble statements from a paper given by pmid."""
    logger.info("Got query for statements from a paper!")
    query_dict = request.args.copy()

    # Get the paper id.
    id_val = query_dict.get('id')
    if id_val is None:
        logger.error("No id provided!")
        abort(Response("No id in request!", 400))

    # Get the id type, if given.
    id_type = query_dict.get('type', 'pmid')

    # Now get the statements.
    logger.info('Getting statements for %s=%s...' % (id_type, id_val))
    stmts = get_statements_by_paper(id_val, id_type, do_stmt_count=False)
    if stmts is None:
        msg = "Invalid or unavailable id %s=%s!" % (id_type, id_val)
        logger.error(msg)
        abort(Response(msg, 404))
    logger.info("Found %d statements." % len(stmts))

    resp = jsonify({'statements': [stmt.to_json() for stmt in stmts]})
    logger.info("Exiting with %d statements." % len(stmts))
    return resp


if __name__ == '__main__':
    app.run()