from __future__ import absolute_import, print_function, unicode_literals
from builtins import dict, str
from indra.tools.machine.gmail_client import get_text

__all__ = ['get_defaults', 'get_primary_db', 'insert_agents', 'insert_pa_stmts',
           'insert_db_stmts', 'get_abstracts_by_pmids', 'get_auth_xml_pmcids',
           'get_statements_by_gene_role_type', 'get_statements',
           'make_stmts_from_db_list']

import os
import re
import json
import logging
from os import path
from sqlalchemy import func
from indra.databases import hgnc_client
from indra.util.get_version import get_version
from indra.util import unzip_string
from indra.statements import Complex, SelfModification, ActiveForm,\
    stmts_from_json, Conversion, Translocation
from .database_manager import DatabaseManager, IndraDatabaseError, texttypes


logger = logging.getLogger('db_util')


DEFAULTS_FILE = path.join(path.dirname(path.abspath(__file__)), 'defaults.txt')
__PRIMARY_DB = None


def get_defaults():
    "Get the default database hosts provided in the specified `DEFAULTS_FILE`."
    default_default_file = DEFAULTS_FILE
    env_key_dict = {'primary': 'INDRADBPRIMARY', 'test': 'INDRADBTEST'}
    env = os.environ
    available_keys = {k: v for k, v in env_key_dict.items() if v in env.keys()}
    if not path.exists(default_default_file) and not available_keys:
        raise IndraDatabaseError(
            "Cannot find default file or environment vars."
            )
    elif path.exists(default_default_file):
        with open(default_default_file, 'r') as f:
            defaults_raw = f.read().splitlines()
        defaults_dict = {}
        for default_line in defaults_raw:
            key, value = default_line.split('=')
            defaults_dict[key.strip()] = value.strip()
    else:
        defaults_dict = {
            purpose: env_val for purpose, my_env_key in env_key_dict.items()
            for env_key, env_val in env.items() if my_env_key == env_key
            }
    return defaults_dict


def get_primary_db(force_new=False):
    """Get a DatabaseManager instance for the primary database host.

    The primary database host is defined in the defaults.txt file, or in a file
    given by the environment variable DEFAULTS_FILE. Alternatively, it may be
    defined by the INDRADBPRIMARY environment variable. If none of the above
    are specified, this function will raise an exception.

    Note: by default, calling this function twice will return the same
    `DatabaseManager` instance. In other words:

    > db1 = get_primary_db()
    > db2 = get_primary_db()
    > db1 is db2
    True

    This means also that, for example `db1.select_one(db2.TextRef)` will work,
    in the above context.

    It is still recommended that when creating a script or function, or other
    general application, you should not rely on this feature to get your access
    to the database, as it can make substituting a different database host both
    complicated and messy. Rather, a database instance should be explicitly
    passed between different users as is done in `get_statements_by_gene_role_type`
    function's call to `get_statements` in `indra.db.query_db_stmts`.

    Parameters
    ----------
    force_new : bool
        If true, a new instance will be created and returned, regardless of
        whether there is an existing instance or not. Default is False, so that
        if this function has been called before within the global scope, a the
        instance that was first created will be returned.

    Returns
    -------
    primary_db : DatabaseManager instance
        An instance of the database manager that is attached to the primary
        database.
    """
    defaults = get_defaults()
    if 'primary' in defaults.keys():
        primary_host = defaults['primary']
    else:
        raise IndraDatabaseError("No primary host available in defaults file.")

    global __PRIMARY_DB
    if __PRIMARY_DB is None or force_new:
        __PRIMARY_DB = DatabaseManager(primary_host, label='primary')
        __PRIMARY_DB.grab_session()
    return __PRIMARY_DB


def get_test_db():
    """Get a DatabaseManager for the test database."""
    defaults = get_defaults()
    test_defaults = {k: v for k, v in defaults.items() if 'test' in k}
    key_list = list(test_defaults.keys())
    key_list.sort()
    for k in key_list:
        test_name = test_defaults[k]
        m = re.match('(\w+)://.*?/([\w.]+)', test_name)
        sqltype = m.groups()[0]
        try:
            db = DatabaseManager(test_name, sqltype=sqltype)
            db.grab_session()
        except Exception as e:
            logger.error("%s didn't work" % test_name)
            logger.exception(e)
            continue  # Clearly this test database won't work.
        logger.info("Using test database %s." % k)
        break
    else:
        logger.error("Could not load a test database!")
    return db


def insert_agents(db, stmt_tbl_obj, agent_tbl_obj, *other_stmt_clauses,
                  **kwargs):
    """Insert agents for statements that don't have any agents.

    Note: This method currently works for both Statements and PAStatements and their
    corresponding agents (Agents and PAAgents).

    Parameters:
    -----------
    db : indra.db.DatabaseManager
        The manager for the database into which you are adding agents.
    stmt_tbl_obj : sqlalchemy table object
        For example, `db.Statements`. The object corresponding to the
        statements column you creating agents for.
    agent_tbl_obj : sqlalchemy table object
        That agent table corresponding to the statement table above.
    *other_stmt_clauses : sqlalchemy clauses
        Further arguments, such as `db.Statements.db_ref == 1' are used to
        restrict the scope of statements whose agents may be added.
    verbose : bool
        If True, print extra information and a status bar while compiling
        agents for insert from statements. Default False.
    num_per_yield : int
        To conserve memory, statements are loaded in batches of `num_per_yeild`
        using the `yeild_per` feature of sqlalchemy queries.
    """
    verbose = kwargs.pop('verbose', False)
    num_per_yield = kwargs.pop('num_per_yield', 100)
    if len(kwargs):
        raise IndraDatabaseError("Unrecognized keyword argument(s): %s."
                                 % kwargs)
    # Build a dict mapping stmt UUIDs to statement IDs
    logger.info("Getting %s that lack %s in the database."
                % (stmt_tbl_obj.__tablename__, agent_tbl_obj.__tablename__))
    stmts_w_agents_q = db.filter_query(
        stmt_tbl_obj,
        stmt_tbl_obj.id == agent_tbl_obj.stmt_id
        )
    stmts_wo_agents_q = (db.filter_query(stmt_tbl_obj, *other_stmt_clauses)
                         .except_(stmts_w_agents_q))
    if verbose:
        num_stmts = stmts_wo_agents_q.count()
        print("Adding agents for %d statements." % num_stmts)
    stmts_wo_agents = stmts_wo_agents_q.yield_per(num_per_yield)

    # Now assemble agent records
    logger.info("Building agent data for insert...")
    if verbose:
        print("Loading:", end='', flush=True)
    agent_data = []
    for i, db_stmt in enumerate(stmts_wo_agents):
        # Convert the database statement entry object into an indra statement.
        stmt = stmts_from_json(json.loads(db_stmt.json.decode()))

        # Figure out how the agents are structured and assign roles.
        ag_list = stmt.agent_list()
        nary_stmt_types = [Complex, SelfModification, ActiveForm, Conversion,
                           Translocation]
        if any([isinstance(stmt, tp) for tp in nary_stmt_types]):
            agents = {('OTHER', ag) for ag in ag_list}
        elif len(ag_list) == 2:
            agents = {('SUBJECT', ag_list[0]), ('OBJECT', ag_list[1])}
        else:
            raise IndraDatabaseError("Unhandled agent structure for stmt %s "
                                     "with agents: %s."
                                     % (str(stmt), str(stmt.agent_list())))

        # Prep the agents for copy into the database.
        for role, ag in agents:
            # If no agent, or no db_refs for the agent, skip the insert
            # that follows.
            if ag is None or ag.db_refs is None:
                continue
            for ns, ag_id in ag.db_refs.items():
                if isinstance(ag_id, list):
                    for sub_id in ag_id:
                        agent_data.append((db_stmt.id, ns, sub_id, role))
                else:
                    agent_data.append((db_stmt.id, ns, ag_id, role))

        # Optionally print another tick on the progress bar.
        if verbose and i % (num_stmts//25) == 0:
            print('|', end='', flush=True)

    if verbose:
        print()

    cols = ('stmt_id', 'db_name', 'db_id', 'role')
    db.copy(agent_tbl_obj.__tablename__, agent_data, cols)
    return


def insert_db_stmts(db, stmts, db_ref_id, verbose=False):
    """Insert statement, their database, and any affiliated agents.

    Note that this method is for uploading statements that came from a
    database to our databse, not for inserting any statements to the database.

    Parameters:
    -----------
    db : indra.db.DatabaseManager
        The manager for the database into which you are loading statements.
    stmts : list [indra.statements.Statement]
        A list of un-assembled indra statements to be uploaded to the datbase.
    db_ref_id : int
        The id to the db_ref entry corresponding to these statements.
    verbose : bool
        If True, print extra information and a status bar while compiling
        statements for insert. Default False.
    """
    # Preparing the statements for copying
    stmt_data = []
    cols = ('uuid', 'db_ref', 'type', 'json', 'indra_version')
    if verbose:
        print("Loading:", end='', flush=True)
    for i, stmt in enumerate(stmts):
        stmt_rec = (
            stmt.uuid,
            db_ref_id,
            stmt.__class__.__name__,
            json.dumps(stmt.to_json()).encode('utf8'),
            get_version()
        )
        stmt_data.append(stmt_rec)
        if verbose and i % (len(stmts)//25) == 0:
            print('|', end='', flush=True)
    if verbose:
        print(" Done loading %d statements." % len(stmts))
    db.copy('statements', stmt_data, cols)
    insert_agents(db, db.Statements, db.Agents,
                  db.Statements.db_ref == db_ref_id)
    return


def insert_pa_stmts(db, stmts, verbose=False):
    """Insert pre-assembled statements, and any affiliated agents.

    Parameters:
    -----------
    db : indra.db.DatabaseManager
        The manager for the database into which you are loading pre-assembled
        statements.
    stmts : list [indra.statements.Statement]
        A list of pre-assembled indra statements to be uploaded to the datbase.
    verbose : bool
        If True, print extra information and a status bar while compiling
        statements for insert. Default False.
    """
    logger.info("Beginning to insert pre-assembled statements.")
    stmt_data = []
    indra_version = get_version()
    cols = ('uuid', 'type', 'json', 'indra_version')
    if verbose:
        print("Loading:", end='', flush=True)
    for i, stmt in enumerate(stmts):
        stmt_rec = (
            stmt.uuid,
            stmt.__class__.__name__,
            json.dumps(stmt.to_json()).encode('utf8'),
            indra_version
        )
        stmt_data.append(stmt_rec)
        if verbose and i % (len(stmts)//25) == 0:
            print('|', end='', flush=True)
    if verbose:
        print(" Done loading %d statements." % len(stmts))
    db.copy('pa_statements', stmt_data, cols)
    insert_agents(db, db.PAStatements, db.PAAgents, verbose=verbose)
    return


def get_abstracts_by_pmids(db, pmid_list, unzip=True):
    "Get abstracts using the pmids in pmid_list."
    abst_list = db.filter_query(
        [db.TextRef, db.TextContent],
        db.TextContent.text_ref_id == db.TextRef.id,
        db.TextContent.text_type == 'abstract',
        db.TextRef.pmid.in_(pmid_list)
        ).all()
    if unzip:
        def unzip_func(s):
            return unzip_string(s.tobytes())
    else:
        def unzip_func(s):
            return s
    return [(r.pmid, unzip_func(c.content)) for (r, c) in abst_list]


def get_auth_xml_pmcids(db):
    tref_list = db.filter_query(
        [db.TextRef, db.TextContent],
        db.TextRef.id == db.TextContent.text_ref_id,
        db.TextContent.text_type == texttypes.FULLTEXT,
        db.TextContent.source == 'pmc_auth'
        )
    return [tref.pmcid for tref in tref_list]


#==============================================================================
# Below are some functions that are useful for getting raw statements from the
# database at various levels of abstraction.
#==============================================================================

def get_statements_by_gene_role_type(agent_id=None, agent_ns='HGNC', role=None,
                                     stmt_type=None, count=1000, db=None,
                                     do_stmt_count=True, preassembled=True):
    """Get statements from the DB by stmt type, agent, and/or agent role.

    Parameters
    ----------
    agent_id : str
        String representing the identifier of the agent from the given
        namespace. Note: if the agent namespace argument, `agent_ns`, is set
        to 'HGNC', this function will treat `agent_id` as an HGNC gene
        symbol and perform an internal lookup of the corresponding HGNC ID.
    agent_ns : str
        Namespace for the identifier given in `agent_id`.
    role : str
        String corresponding to the role of the agent in the statement.
        Options are 'SUBJECT', 'OBJECT', or 'OTHER' (in the case of `Complex`,
        `SelfModification`, and `ActiveForm` Statements).
    stmt_type : str
        Name of the Statement class.
    count : int
        Number of statements to retrieve in each batch (passed to
        :py:func:`get_statements`).
    db : indra.db.DatabaseManager object.
        Optionally specify a database manager that attaches to something
        besides the primary database, for example a local databse instance.
    do_stmt_count : bool
        Whether or not to perform an initial statement counting step to give
        more meaningful progress messages.
    preassembled : bool
        If true, statements will be selected from the table of pre-assembled
        statements. Otherwise, they will be selected from the raw statements.
        Default is True.

    Returns
    -------
    list of Statements from the database corresponding to the query.
    """
    if db is None:
        db = get_primary_db()

    if preassembled:
        Statements = db.PAStatements
        Agents = db.PAAgents
    else:
        Statements = db.Statements
        Agents = db.Agents

    if not (agent_id or role or stmt_type):
        raise ValueError('At least one of agent_id, role, or stmt_type '
                         'must be specified.')
    clauses = []
    if agent_id and agent_ns == 'HGNC':
        hgnc_id = hgnc_client.get_hgnc_id(agent_id)
        if not hgnc_id:
            logger.warning('Invalid gene name: %s' % agent_id)
            return []
        clauses.extend([Agents.db_name == 'HGNC',
                        Agents.db_id == hgnc_id])
    elif agent_id:
        clauses.extend([Agents.db_name == agent_ns,
                        Agents.db_id == agent_id])
    if role:
        clauses.append(Agents.role == role)
    if agent_id or role:
        clauses.append(Agents.stmt_id == Statements.id)
    if stmt_type:
        clauses.append(Statements.type == stmt_type)
    stmts = get_statements(clauses, count=count, do_stmt_count=do_stmt_count,
                           db=db, preassembled=preassembled)
    return stmts


def get_statements(clauses, count=1000, do_stmt_count=True, db=None,
                   preassembled=True):
    """Select statements according to a given set of clauses.

    Parameters
    ----------
    clauses : list
        list of sqlalchemy WHERE clauses to pass to the filter query.
    count : int
        Number of statements to retrieve and process in each batch.
    do_stmt_count : bool
        Whether or not to perform an initial statement counting step to give
        more meaningful progress messages.
    db : indra.db.DatabaseManager object.
        Optionally specify a database manager that attaches to something
        besides the primary database, for example a local database instance.
    preassembled : bool
        If true, statements will be selected from the table of pre-assembled
        statements. Otherwise, they will be selected from the raw statements.
        Default is True.

    Returns
    -------
    list of Statements from the database corresponding to the query.
    """
    if db is None:
        db = get_primary_db()

    stmts_tblname = 'pa_statements' if preassembled else 'statements'

    stmts = []
    q = db.filter_query(stmts_tblname, *clauses)
    if do_stmt_count:
        logger.info("Counting statements...")
        num_stmts = q.count()
        logger.info("Total of %d statements" % num_stmts)
    db_stmts = q.yield_per(count)
    subset = []
    total_counter = 0
    for stmt in db_stmts:
        subset.append(stmt)
        if len(subset) == count:
            stmts.extend(make_stmts_from_db_list(subset))
            subset = []
        total_counter += 1
        if total_counter % count == 0:
            if do_stmt_count:
                logger.info("%d of %d statements" % (total_counter, num_stmts))
            else:
                logger.info("%d statements" % total_counter)

    stmts.extend(make_stmts_from_db_list(subset))
    return stmts


def make_stmts_from_db_list(db_stmt_objs):
    stmt_json_list = []
    for st_obj in db_stmt_objs:
        stmt_json_list.append(json.loads(st_obj.json.decode('utf8')))
    return stmts_from_json(stmt_json_list)


#==============================================================================
# Below are functions used for getting statistics on tables in the database.
#==============================================================================


def __report_stat(report_str, fname=None, do_print=True):
    if do_print:
        print(report_str)
    if fname is not None:
        with open(fname, 'a+') as f:
            f.write(report_str + '\n')
    return


def get_text_ref_stats(fname=None, db=None):
    if db is None:
        db = get_primary_db()
    tr_tc_link = db.TextRef.id == db.TextContent.text_ref_id
    tc_rdng_link = db.TextContent.id == db.Readings.text_content_id
    __report_stat("Text ref statistics:", fname)
    __report_stat("--------------------", fname)
    tr_q = db.filter_query(db.TextRef)
    total_refs = tr_q.count()
    __report_stat('Total number of text refs: %d' % total_refs, fname)
    tr_w_cont_q = tr_q.filter(tr_tc_link)
    refs_with_content = tr_w_cont_q.distinct().count()
    __report_stat('Total number of refs with content: %d' % refs_with_content,
                  fname)
    tr_w_fulltext_q = tr_w_cont_q.filter(db.TextContent.text_type == 'fulltext')
    refs_with_fulltext = tr_w_fulltext_q.distinct().count()
    __report_stat('Number of refs with fulltext: %d' % refs_with_fulltext,
                  fname)
    tr_w_abstract_q = tr_w_cont_q.filter(db.TextContent.text_type == 'abstract')
    refs_with_abstract = tr_w_abstract_q.distinct().count()
    __report_stat('Number of refs with abstract: %d' % refs_with_abstract,
                  fname)
    __report_stat(('Number of refs with only abstract: %d'
                   % (refs_with_content-refs_with_fulltext)), fname)
    tr_w_read_content_q = tr_w_cont_q.filter(tc_rdng_link)
    refs_with_reading = tr_w_read_content_q.distinct().count()
    __report_stat('Number of refs that have been read: %d' % refs_with_reading,
                  fname)
    tr_w_fulltext_read_q = tr_w_fulltext_q.filter(tc_rdng_link)
    refs_with_fulltext_read = tr_w_fulltext_read_q.distinct().count()
    __report_stat(('Number of refs with fulltext read: %d'
                   % refs_with_fulltext_read), fname)
    return


def get_text_content_stats(fname=None, db=None):
    if db is None:
        db = get_primary_db()
    tc_rdng_link = db.TextContent.id == db.Readings.text_content_id
    __report_stat("\nText Content statistics:", fname)
    __report_stat('------------------------', fname)
    tc_q = db.filter_query(db.TextContent)
    total_content = tc_q.count()
    __report_stat("Total number of text content entries: %d" % total_content)
    latest_updates = (db.session.query(db.Updates.source,
                                       func.max(db.Updates.datetime))
                      .group_by(db.Updates.source)
                      .all())
    __report_stat(("Latest updates:\n    %s"
                   % '\n    '.join(['%s: %s' % (s, d)
                                    for s, d in latest_updates])),
                  fname
                  )
    tc_w_reading_q = tc_q.filter(tc_rdng_link)
    content_read = tc_w_reading_q.distinct().count()
    __report_stat("Total content read: %d" % content_read, fname)
    tc_fulltext_q = tc_q.filter(db.TextContent.text_type == 'fulltext')
    fulltext_content = tc_fulltext_q.distinct().count()
    __report_stat("Number of fulltext entries: %d" % fulltext_content, fname)
    tc_fulltext_read_q = tc_fulltext_q.filter(tc_rdng_link)
    fulltext_read = tc_fulltext_read_q.distinct().count()
    __report_stat("Number of fulltext entries read: %d" % fulltext_read, fname)
    content_by_source = (db.session.query(db.TextContent.source,
                                          func.count(db.TextContent.id))
                         .distinct()
                         .group_by(db.TextContent.source)
                         .all())
    __report_stat(("Content by source:\n    %s"
                   % '\n    '.join(['%s: %d' % (s, n)
                                    for s, n in content_by_source])),
                  fname
                  )
    content_read_by_source = (db.session.query(db.TextContent.source,
                                               func.count(db.TextContent.id))
                              .filter(tc_rdng_link)
                              .distinct()
                              .group_by(db.TextContent.source)
                              .all())
    __report_stat(("Content read by source:\n    %s"
                   % '\n    '.join(['%s: %d' % (s, n)
                                    for s, n in content_read_by_source])),
                  fname
                  )
    return


def get_readings_stats(fname=None, db=None):
    if db is None:
        db = get_primary_db()

    __report_stat('\nReading statistics:', fname)
    __report_stat('-------------------', fname)
    rdg_q = db.filter_query(db.Readings)
    __report_stat('Total number or readings: %d' % rdg_q.count(), fname)
    readings_by_reader_and_version = (
        db.session.query(db.Readings.reader_version,
                         db.TextContent.source,
                         func.count(db.Readings.id))
        .filter(db.TextContent.id == db.Readings.text_content_id)
        .distinct()
        .group_by(db.Readings.reader_version, db.TextContent.source)
        .all()
        )
    __report_stat(("Readings by reader version and content source:\n    %s"
                   % '\n    '.join([str(r) for r
                                    in readings_by_reader_and_version])),
                  fname
                  )
    return


def get_statements_stats(fname=None, db=None):
    if db is None:
        db = get_primary_db()
    tc_rdng_link = db.TextContent.id == db.Readings.text_content_id
    stmt_rdng_link = db.Readings.id == db.Statements.reader_ref

    __report_stat('\nStatement Statistics:', fname)
    __report_stat('---------------------', fname)
    stmt_q = db.filter_query(db.Statements)
    __report_stat("Total number of statments: %d" % stmt_q.count(), fname)
    statements_by_reading_source = (
        db.session.query(db.Readings.reader, db.TextContent.text_type,
                         func.count(db.Statements.id))
        .filter(stmt_rdng_link, tc_rdng_link)
        .distinct()
        .group_by(db.Readings.reader, db.TextContent.source)
        .all()
        )
    __report_stat(("Statements by reader and content source:\n    %s"
                   % '\n    '.join([str(r) for r
                                    in statements_by_reading_source])),
                  fname
                  )
    statements_by_db_source = (
        db.session.query(db.DBInfo.db_name, func.count(db.Statements.id))
        .filter(db.Statements.db_ref == db.DBInfo.id)
        .distinct()
        .group_by(db.DBInfo.db_name)
        .all()
        )
    __report_stat(("Statements by database:\n    %s"
                   % '\n    '.join(['%s: %d' % (s, n)
                                    for s, n in statements_by_db_source])),
                  fname
                  )
    statements_produced_by_indra_version = (
        db.session.query(db.Statements.indra_version,
                         func.count(db.Statements.id))
        .group_by(db.Statements.indra_version)
        .all()
        )
    __report_stat(("Number of statements by indra version:\n    %s"
                   % '\n    '.join(['%s: %d' % (s, n) for s, n
                                    in statements_produced_by_indra_version])),
                  fname
                  )
    return


def get_db_statistics(fname=None, db=None, tables=None):
    """Get statistics on the contents of the database"""
    if db is None:
        db = get_primary_db()

    # Text Ref statistics
    if tables is None or (tables is not None and 'text_ref' in tables):
        get_text_ref_stats(fname, db)

    # Text Content statistics
    if tables is None or (tables is not None and 'text_content' in tables):
        get_text_content_stats(fname, db)

    # Readings statistics
    if tables is None or (tables is not None and 'readings' in tables):
        get_readings_stats(fname, db)

    # Statement Statistics
    if tables is None or (tables is not None and 'statements' in tables):
        get_statements_stats(fname, db)

    return