import sys
import logging

from flask import Flask, request, abort, jsonify, Response
from flask_compress import Compress

from indra.db.util import get_statements_by_gene_role_type, \
    get_statements_by_paper
from indra.statements import make_statement_camel
from indra.databases import hgnc_client

logger = logging.getLogger("db-api")

app = Flask(__name__)
Compress(app)


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


def _filter_statements(stmts_in, agent_pos, ns, value):
    """Return statements filtered to ones where agent is at given position."""
    stmts_out = []
    for stmt in stmts_in:
        # Make sure the statement has enough agents to get the one at the
        # position of interest e.g. has only 1 agent but the agent_pos is not 0
        agents = stmt.agent_list()
        if len(agents) <= agent_pos:
            continue
        # Get the agent at the position of interest and make sure it's an
        # actual Agent
        agent = agents[agent_pos]
        if agent is not None:
            # Check if the db_refs for the namespace of interest matches the
            # value
            if agent.db_refs.get(ns) == value:
                stmts_out.append(stmt)
    return stmts_out


@app.route('/statements/', methods=['GET'])
def get_statements():
    """Get some statements constrained by query."""
    logger.info("Got query for statements!")
    query_dict = request.args.copy()

    logger.info("Getting query details.")
    try:
        free_agents = [__process_agent(ag)
                       for ag in query_dict.poplist('agent')]
        agents = {role: __process_agent(query_dict.pop(role, None)) for role
                  in ['subject', 'object'] if query_dict.get(role) is not None}
    except DbAPIError as e:
        logger.exception(e)
        abort(Response('Failed to make agents from names: %s\n' % str(e), 400))
        return
    act_uncamelled = query_dict.pop('type', None)
    if act_uncamelled is not None:
        act = make_statement_camel(act_uncamelled)
    else:
        act = None
    if query_dict:
        abort(Response("Unrecognized query options; %s." %
                       list(query_dict.keys()),
                       400))
        return

    if not any(agents.values()) and not free_agents:
        logger.error("No agents.")
        abort(Response(("No agents. Must have 'subject', 'object', or "
                        "'other'!\n"), 400))

    stmts = []
    logger.info("Getting statements...")
    for role, (agent, ns) in agents.items():
        logger.debug("Checking agent %s in namespace %s." % (agent, ns))
        # TODO: This is a temporary measure, remove ASAP.
        if ns == 'FPLX':
            ns = 'BE'

        if not stmts:
            # Get an initial list
            stmts = get_statements_by_gene_role_type(agent_id=agent,
                                                     agent_ns=ns,
                                                     role=role.upper(),
                                                     stmt_type=act,
                                                     do_stmt_count=False)
        elif role.lower() == 'subject':
            stmts = _filter_statements(stmts, 0, ns, agent)
        elif role.lower() == 'object':
            stmts = _filter_statements(stmts, 1, ns, agent)
        else:
            abort(Response("Unrecognized role: %s." % role.lower(), 400))
        if not len(stmts):
            break
    for agent, ns in free_agents:
        if ns == 'FPLX':
            ns = 'BE'
        logger.debug("Checking agent %s in namespace %s." % (agent, ns))
        if not stmts:
            # Get an initial list
            stmts = get_statements_by_gene_role_type(agent_id=agent,
                                                     agent_ns=ns,
                                                     stmt_type=act,
                                                     do_stmt_count=False)
        else:
            stmts = [
                s for s in stmts if len(s.agent_list()) > 0 and agent in [
                    ag for other_agent in s.agent_list() if other_agent is not None
                    for ag in other_agent.db_refs.values()
                    ] + [
                    ag for ag in s.agent_list() if ag is None
                    ]
                ]
        if not len(stmts):
            break

    # TODO: remove this too
    for s in stmts:
        for ag in s.agent_list():
            if ag is not None:
                if 'BE' in ag.db_refs.keys():
                    ag.db_refs['FPLX'] = ag.db_refs.pop('BE')

    resp = jsonify([stmt.to_json() for stmt in stmts])
    logger.info("Exiting with %d statements of nominal size %f MB."
                % (len(stmts), sys.getsizeof(resp.data)/1e6))
    return resp


@app.route('/papers/', methods=['GET'])
def get_paper_statements():
    """Get and preassemble statements from a paper given by pmid."""
    logger.info("Got query for statements from a paper!")
    query_dict = request.args.copy()
    id_val = query_dict.get('id')
    if id_val is None:
        logger.error("No id provided!")
        abort(Response("No id in request!", 400))
    id_type = query_dict.get('type', 'pmid')
    stmts = get_statements_by_paper(id_val, id_type, do_stmt_count=False)
    if stmts is None:
        msg = "Invalid or unavailable id %s=%s!" % (id_type, id_val)
        logger.error(msg)
        abort(Response(msg, 404))

    resp = jsonify([stmt.to_json() for stmt in stmts])
    logger.info("Exiting with %d statements." % len(stmts))
    return resp


if __name__ == '__main__':
    app.run()
