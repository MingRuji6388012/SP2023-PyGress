from __future__ import absolute_import, print_function, unicode_literals

from builtins import dict, str

import logging
from collections import defaultdict
from itertools import groupby, permutations, product
from sqlalchemy import or_

from indra.statements import Unresolved

logger = logging.getLogger('db_client')

from indra.util import batch_iter
from indra.databases import hgnc_client
from .util import get_primary_db, get_raw_stmts_frm_db_list, \
    unpack, _get_statement_object, _clockit


def get_reader_output(db, ref_id, ref_type='tcid', reader=None,
                      reader_version=None):
    """Return reader output for a given text content.

    Parameters
    ----------
    db : :py:class:`DatabaseManager`
        Reference to the DB to query
    ref_id : int or str
        The text reference ID whose reader output should be returned
    ref_type : Optional[str]
        The type of ID to look for, options include
        'tcid' for the database's internal unique text content ID,
        or 'pmid', 'pmcid', 'doi, 'pii', 'manuscript_id'
        Default: 'tcid'
    reader : Optional[str]
        The name of the reader whose output is of interest
    reader_version : Optional[str]
        The specific version of the reader

    Returns
    -------
    reading_results : dict{dict{list[str]}}
        A dict of reader outputs that match the query criteria, indexed first
        by text content id, then by reader.
    """
    if ref_type == 'tcid':
        clauses = [db.Reading.text_content_id == ref_id]
    else:
        trids = _get_trids(db, ref_id, ref_type)
        if not trids:
            return []
        logger.debug("Found %d text ref ids." % len(trids))
        clauses = [db.TextContent.text_ref_id.in_(trids),
                   db.Reading.text_content_id == db.TextContent.id]
    if reader:
        clauses.append(db.Reading.reader == reader.upper())
    if reader_version:
        clauses.append(db.Reading.reader_version == reader_version)

    res = db.select_all([db.Reading.text_content_id, db.Readings.reader,
                         db.Reading.bytes], *clauses)
    reading_dict = defaultdict(lambda: defaultdict(lambda: []))
    for tcid, reader, result in res:
        reading_dict[tcid][reader].append(unpack(result))
    return reading_dict


def get_content_by_refs(db, pmid_list=None, trid_list=None, sources=None,
                        formats=None, content_type='abstract', unzip=True):
    """Return content from the database given a list of PMIDs or text ref ids.

    Note that either pmid_list OR trid_list must be set, and only one can be
    set at a time.

    Parameters
    ----------
    db : :py:class:`DatabaseManager`
        Reference to the DB to query
    pmid_list : list[str] or None
        A list of pmids. Default is None, in which case trid_list must be given.
    trid_list : list[int] or None
        A list of text ref ids. Default is None, in which case pmid list must be
        given.
    sources : list[str] or None
        A list of sources to include (e.g. 'pmc_oa', or 'pubmed'). Default is
        None, indicating that all sources will be included.
    formats : list[str]
        A list of the formats to be included ('xml', 'text'). Default is None,
        indicating that all formats will be included.
    content_type : str
        Select the type of content to load ('abstract' or 'fulltext'). Note that
        not all refs will have any, or both, types of content.
    unzip : Optional[bool]
        If True, the compressed output is decompressed into clear text.
        Default: True

    Returns
    -------
    content_dict : dict
        A dictionary whose keys are text ref ids, with each value being the
        the corresponding content.
    """
    # Make sure we only get one type of list.
    if not pmid_list or trid_list:
        raise ValueError("One of `pmid_list` or `trid_list` must be defined.")
    if pmid_list and trid_list:
        raise ValueError("Only one of `pmid_list` or `trid_list` may be used.")

    # Put together the clauses for the general constraints.
    clauses = []
    if sources is not None:
        clauses.append(db.TextContent.source.in_(sources))
    if formats is not None:
        clauses.append(db.TextContent.format.in_(formats))
    if content_type not in ['abstract', 'fulltext']:
        raise ValueError("Unrecognized content type: %s" % content_type)
    else:
        clauses.append(db.TextContent.text_type == content_type)

    # Do the query to get the content.
    if pmid_list is not None:
        content_list = db.select_all([db.TextRef.pmid, db.TextContent.content],
                                     db.TextRef.id == db.TextContent.text_ref_id,
                                     db.TextRef.pmid.in_(pmid_list),
                                     *clauses)
    else:
        content_list = db.select_all([db.TextRef.id, db.TextContent.content],
                                     db.TextContent.text_ref_id.in_(trid_list),
                                     *clauses)
    if unzip:
        content_dict = {id_val: unpack(content)
                        for id_val, content in content_list}
    else:
        content_dict = {id_val: content for id_val, content in content_list}
    return content_dict


@_clockit
def get_statements_by_gene_role_type(agent_id=None, agent_ns='HGNC-SYMBOL',
                                     role=None, stmt_type=None, count=1000,
                                     db=None, do_stmt_count=False,
                                     preassembled=True, fix_refs=True,
                                     with_evidence=True, with_support=True,
                                     essentials_only=False):
    """Get statements from the DB by stmt type, agent, and/or agent role.

    Parameters
    ----------
    agent_id : str
        String representing the identifier of the agent from the given
        namespace. Note: if the agent namespace argument, `agent_ns`, is set
        to 'HGNC-SYMBOL', this function will treat `agent_id` as an HGNC gene
        symbol and perform an internal lookup of the corresponding HGNC ID.
        Default is 'HGNC-SYMBOL'.
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
    db : :py:class:`DatabaseManager`
        Optionally specify a database manager that attaches to something
        besides the primary database, for example a local databse instance.
    do_stmt_count : bool
        Whether or not to perform an initial statement counting step to give
        more meaningful progress messages.
    preassembled : bool
        If true, statements will be selected from the table of pre-assembled
        statements. Otherwise, they will be selected from the raw statements.
        Default is True.
    with_support : bool
        Choose whether to populate the supports and supported_by list attributes
        of the Statement objects. Generally results in slower queries.
    with_evidence : bool
        Choose whether or not to populate the evidence list attribute of the
        Statements. As with `with_support`, setting this to True will take
        longer.
    fix_refs : bool
        The paper refs within the evidence objects are not populated in the
        database, and thus must be filled using the relations in the database.
        If True (default), the `pmid` field of each Statement Evidence object
        is set to the correct PMIDs, or None if no PMID is available. If False,
        the `pmid` field defaults to the value populated by the reading
        system.
    essentials_only : bool
        Default is False. If True, retrieve only some metadata regarding the
        statements. Implicitly `with_support`, `with_evidence`, `fix_refs`, and
        `do_stmt_count` are all False, as none of the relevant features apply.

    Returns
    -------
    if essentials_only is False:
        list of Statements from the database corresponding to the query.
    else:
        list of tuples containing basic data from the statements.
    """
    if db is None:
        db = get_primary_db()

    if preassembled:
        Statements = db.PAStatements
        Agents = db.PAAgents
    else:
        Statements = db.RawStatements
        Agents = db.RawAgents

    if not (agent_id or role or stmt_type):
        raise ValueError('At least one of agent_id, role, or stmt_type '
                         'must be specified.')
    clauses = []
    if agent_id and agent_ns == 'HGNC-SYMBOL':
        hgnc_id = hgnc_client.get_hgnc_id(agent_id)
        if not hgnc_id:
            logger.warning('Invalid gene name: %s' % agent_id)
            return []
        clauses.extend([Agents.db_name.like('HGNC'),
                        Agents.db_id.like(hgnc_id)])
    elif agent_id:
        clauses.extend([Agents.db_name.like(agent_ns),
                        Agents.db_id.like(agent_id)])
    if role:
        clauses.append(Agents.role == role)
    if agent_id or role:
        if preassembled:
            clauses.append(Agents.stmt_mk_hash == Statements.mk_hash)
        else:
            clauses.append(Agents.stmt_id == Statements.id)
    if stmt_type:
        clauses.append(Statements.type == stmt_type)

    if essentials_only:
        stmts = get_statement_essentials(clauses, count=count, db=db,
                                         preassembled=preassembled)
    else:
        stmts = get_statements(clauses, count=count,
                               do_stmt_count=do_stmt_count, db=db,
                               preassembled=preassembled, fix_refs=fix_refs,
                               with_evidence=with_evidence,
                               with_support=with_support)
    return stmts


def get_statements_by_paper(id_val, id_type='pmid', count=1000, db=None,
                            do_stmt_count=False, preassembled=True):
    """Get the statements from a particular paper.

    Parameters
    ----------
    id_val : int or str
        The value of the id for the paper whose statements you wish to retrieve.
    id_type : str
        The type of id used (default is pmid). Options include pmid, pmcid, doi,
        pii, url, or manuscript_id. Note that pmid is generally the best means
        of getting a paper.
    count : int
        Number of statements to retrieve in each batch (passed to
        :py:func:`get_statements`).
    db : :py:class:`DatabaseManager`
        Optionally specify a database manager that attaches to something
        besides the primary database, for example a local databse instance.
    do_stmt_count : bool
        Whether or not to perform an initial statement counting step to give
        more meaningful progress messages.
    preassembled : bool
        If True, statements will be selected from the table of pre-assembled
        statements. Otherwise, they will be selected from the raw statements.
        Default is True.

    Returns
    -------
    A list of Statements from the database corresponding to the paper id given.
    """
    if db is None:
        db = get_primary_db()

    trid_list = _get_trids(db, id_val, id_type)
    if not trid_list:
        return None

    stmts = []
    for trid in trid_list:
        clauses = db.join(db.TextContent, db.RawStatements) \
                  + [db.TextContent.text_ref_id == trid]
        if preassembled:
            clauses += db.join(db.RawStatements, db.PAStatements)
        stmts.extend(get_statements(clauses, count=count, db=db,
                                    preassembled=preassembled,
                                    do_stmt_count=do_stmt_count))
    return stmts


@_clockit
def get_statements(clauses, count=1000, do_stmt_count=False, db=None,
                   preassembled=True, with_support=False, fix_refs=True,
                   with_evidence=True):
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
    db : :py:class:`DatabaseManager`
        Optionally specify a database manager that attaches to something
        besides the primary database, for example a local database instance.
    preassembled : bool
        If true, statements will be selected from the table of pre-assembled
        statements. Otherwise, they will be selected from the raw statements.
        Default is True.
    with_support : bool
        Choose whether to populate the supports and supported_by list attributes
        of the Statement objects. General results in slower queries.
    with_evidence : bool
        Choose whether or not to populate the evidence list attribute of the
        Statements. As with `with_support`, setting this to True will take
        longer.
    fix_refs : bool
        The paper refs within the evidence objects are not populated in the
        database, and thus must be filled using the relations in the database.
        If True (default), the `pmid` field of each Statement Evidence object
        is set to the correct PMIDs, or None if no PMID is available. If False,
        the `pmid` field defaults to the value populated by the reading
        system.

    Returns
    -------
    list of Statements from the database corresponding to the query.
    """
    if db is None:
        db = get_primary_db()

    stmts_tblname = 'pa_statements' if preassembled else 'raw_statements'

    if not preassembled:
        stmts = []
        q = db.filter_query(stmts_tblname, *clauses)
        if do_stmt_count:
            logger.info("Counting statements...")
            num_stmts = q.count()
            logger.info("Total of %d statements" % num_stmts)
        db_stmts = q.yield_per(count)
        for subset in batch_iter(db_stmts, count):
            stmts.extend(get_raw_stmts_frm_db_list(db, subset, with_sids=False,
                                                   fix_refs=fix_refs))
            if do_stmt_count:
                logger.info("%d of %d statements" % (len(stmts), num_stmts))
            else:
                logger.info("%d statements" % len(stmts))
    else:
        logger.info("Getting preassembled statements.")
        if with_evidence:
            logger.info("Getting preassembled statements.")
            # Get pairs of pa statements with their linked raw statements
            clauses += db.join(db.PAStatements, db.RawStatements)
            pa_raw_stmt_pairs = \
                db.select_all([db.PAStatements, db.RawStatements],
                              *clauses, yield_per=count)

            # Iterate over the batches to create the statement objects.
            stmt_dict = {}
            ev_dict = {}
            raw_stmt_dict = {}
            total_ev = 0
            for stmt_pair_batch in batch_iter(pa_raw_stmt_pairs, count):
                # Instantiate the PA statement objects, and record the uuid
                # evidence (raw statement) links.
                raw_stmt_objs = []
                for pa_stmt_db_obj, raw_stmt_db_obj in stmt_pair_batch:
                    k = pa_stmt_db_obj.mk_hash
                    if k not in stmt_dict.keys():
                        stmt_dict[k] = _get_statement_object(pa_stmt_db_obj)
                        ev_dict[k] = [raw_stmt_db_obj.id,]
                    else:
                        ev_dict[k].append(raw_stmt_db_obj.id)
                    raw_stmt_objs.append(raw_stmt_db_obj)
                    total_ev += 1

                logger.info("Up to %d pa statements, with %d pieces of "
                            "evidence in all." % (len(stmt_dict), total_ev))

                # Instantiate the raw statements.
                raw_stmt_sid_tpls = get_raw_stmts_frm_db_list(db, raw_stmt_objs,
                                                              fix_refs,
                                                              with_sids=True)
                raw_stmt_dict.update({sid: s for sid, s in raw_stmt_sid_tpls})
                logger.info("Processed %d raw statements."
                            % len(raw_stmt_sid_tpls))

            # Attach the evidence
            logger.info("Inserting evidence.")
            for k, sid_list in ev_dict.items():
                stmt_dict[k].evidence = [raw_stmt_dict[sid].evidence[0]
                                         for sid in sid_list]
        else:
            # Get just pa statements without their supporting raw statement(s).
            pa_stmts = db.select_all(db.PAStatements, *clauses, yield_per=count)

            # Iterate over the batches to create the statement objects.
            stmt_dict = {}
            for stmt_pair_batch in batch_iter(pa_stmts, count):
                # Instantiate the PA statement objects.
                for pa_stmt_db_obj in stmt_pair_batch:
                    k = pa_stmt_db_obj.mk_hash
                    if k not in stmt_dict.keys():
                        stmt_dict[k] = _get_statement_object(pa_stmt_db_obj)

                logger.info("Up to %d pa statements in all." % len(stmt_dict))

        # Populate the supports/supported by fields.
        if with_support:
            logger.info("Populating support links.")
            support_links = db.select_all(
                [db.PASupportLinks.supported_mk_hash,
                 db.PASupportLinks.supporting_mk_hash],
                or_(db.PASupportLinks.supported_mk_hash.in_(stmt_dict.keys()),
                    db.PASupportLinks.supporting_mk_hash.in_(stmt_dict.keys()))
                )
            for supped_hash, supping_hash in set(support_links):
                if supped_hash == supping_hash:
                    assert False, 'Self-support found on-load.'
                supped_stmt = stmt_dict.get(supped_hash)
                if supped_stmt is None:
                    supped_stmt = Unresolved(shallow_hash=supped_hash)
                supping_stmt = stmt_dict.get(supping_hash)
                if supping_stmt is None:
                    supping_stmt = Unresolved(shallow_hash=supping_hash)
                supped_stmt.supported_by.append(supping_stmt)
                supping_stmt.supports.append(supped_stmt)

        stmts = list(stmt_dict.values())
        logger.info("In all, there are %d pa statements." % len(stmts))

    return stmts


@_clockit
def get_statement_essentials(clauses, count=1000, db=None, preassembled=True):
    """Get the type, agents, and id data for the specified statements.

    This function is useful for light-weight searches of basic mechanistic
    information, without the need to follow as many links in the database to
    populate the Statement objects.

    To get full statements, use `get_statements`.

    Parameters
    ----------
    clauses : list
        list of sqlalchemy WHERE clauses to pass to the filter query.
    count : int
        Number of statements to retrieve and process in each batch.
    do_stmt_count : bool
        Whether or not to perform an initial statement counting step to give
        more meaningful progress messages.
    db : :py:class:`DatabaseManager`
        Optionally specify a database manager that attaches to something
        besides the primary database, for example a local database instance.
    preassembled : bool
        If true, statements will be selected from the table of pre-assembled
        statements. Otherwise, they will be selected from the raw statements.
        Default is True.

    Returns
    -------
    A list of tuples containing:
        `(uuid, sid, hash, type, (agent_1, agent_2, ...))`.
    """
    if db is None:
        db = get_primary_db()

    stmts_tblname = 'pa_statements' if preassembled else 'raw_statements'

    stmt_data = []
    db_stmts = db.select_all(stmts_tblname, *clauses, yield_per=count)
    for db_stmt in db_stmts:
        stmt = _get_statement_object(db_stmt)
        sid = db_stmt.id if hasattr(db_stmt, 'id') else None
        stmt_data.append((db_stmt.uuid, sid, stmt.get_hash(shallow=True),
                          db_stmt.type, stmt.agent_list()))

    return stmt_data


def get_relation_dict(db, groundings=None, with_evidence_count=False,
                      with_support_count=False):
    """Get a dictionary of entity interactions from the database.

    Use only metadata from the database to rapidly get simple interaction data.
    This is much faster than handling the full Statement jsons, while providing
    some basic valuable functionality.

    Parameters
    ----------
    db : DatabaseManager instance
        An instance of a database manager.
    groundings : list[str] or None
        Select which types of grounding namespaces to include, e.g. HGNC, or
        FPLX, or both. Only agent refs with these groundings will be selected.
        If None, only HGNC is used.
    with_evidence_count : bool
        Default is False. If True, an additional query will be made for each
        statement to get the count of supporting evidence, which is a userful
        proxy for belief. This is currently VERY SLOW.
    with_support_count : bool
        Default is False. Like `with_evidence_count`, except the number of
        supporting statements is counted.
    """
    other_params = []
    if groundings is None:
        other_params.append(db.PAAgents.db_name.like('HGNC'))
    elif len(groundings) == 1:
        other_params.append(db.PAAgents.db_name.like(groundings[0]))
    else:
        ors = []
        for gdng in groundings:
            ors.append(db.PAAgents.db_name.like(gdng))
        other_params.append(or_(*ors))

    # Query the database
    results = db.select_all(
        [db.PAAgents.id, db.PAAgents.db_id, db.PAAgents.role,
         db.PAAgents.db_name, db.PAStatements.type, db.PAStatements.mk_hash],
        db.PAStatements.mk_hash == db.PAAgents.stmt_mk_hash,
        *other_params, **{'yield_per': 10000}
        )

    # Sort into a dict.
    stmt_dict = {}
    for res in results:
        ag_id, ag_dbid, ag_role, ag_dbname, stmt_type, stmt_hash = res

        # Handle the case that this is or isn't HGNC
        if ag_dbname == 'HGNC':
            ag_tpl = (ag_id, ag_role, ag_dbname, ag_dbid,
                      hgnc_client.get_hgnc_name(ag_dbid))
        else:
            ag_tpl = (ag_id, ag_role, ag_dbname, ag_dbid, ag_dbid)

        # Add the tuple to the dict in the appropriate manner.
        if stmt_hash not in stmt_dict.keys():
            stmt_dict[stmt_hash] = {'type': stmt_type, 'agents': [ag_tpl]}
            if with_evidence_count:
                logger.info('Getting a count of evidence for %d' % stmt_hash)
                n_ev = db.count(db.RawUniqueLinks,
                                db.RawUniqueLinks.pa_stmt_mk_hash == stmt_hash)
                stmt_dict[stmt_hash]['n_ev'] = n_ev
            if with_support_count:
                logger.info('Getting a count of support for %d' % stmt_hash)
                n_sup = db.count(db.PASupportLinks,
                               db.PASupportLinks.supported_mk_hash == stmt_hash)
                stmt_dict[stmt_hash]['n_sup'] = n_sup
        else:
            assert stmt_dict[stmt_hash]['type'] == stmt_type
            stmt_dict[stmt_hash]['agents'].append(ag_tpl)

    # Only return the entries with at least 2 agents.
    return {k: d for k, d in stmt_dict.items() if len(d['agents']) >= 2}


def export_relation_dict_to_tsv(relation_dict, out_base, out_types=None):
    """Export a relation dict (from get_relation_dict) to a tsv.

    Available output types are:
    - "full_tsv" : get a tsv with directed pairs of entities (e.g. HGNC symbols),
        the type of relation (e.g. Phosphorylation) and the hash of the
        preassembled statement. Columns are agent_1, agent_2 (where agent_1
        affects agent_2), type, hash.
    - "short_tsv" : like the above, but without the hashes, so only one instance
        of each pair and type trio occurs. However, the information cannot be
        traced. Columns are agent_1, agent_2, type, where agent_1 affects
        agent_2.
    - "pairs_tsv" : like the above, but without the relation type. Similarly,
        each row is unique. In addition, the agents are undirected. Thus this is
        purely a list of pairs of related entities. The columns are just agent_1
        and agent_2, where nothing is implied by the ordering.

    Parameters
    ----------
    relation_dict : dict
        This should be the output from `get_relation_dict`, or something
        equivalently constructed.
    out_base : str
        The base-name for the output files.
    out_types : list[str]
        A list of the types of tsv to output. See above for details.
    """
    # Check to make sure the output types are valid.
    ok_types = ['full_tsv', 'short_tsv', 'pairs_tsv']
    if out_types is None:
        out_types = ok_types[:]

    if any(ot not in ok_types for ot in out_types):
        raise ValueError('Invalid output_types: %s. Allowed types are: %s'
                         % (out_types, ok_types))

    # Now write any tsv's.
    def write_tsv_line(f, row_tpl):
        f.write('\t'.join(list(row_tpl)) + '\n')

    # Open the tsv files.
    tsv_files = {}
    for output_type in out_types:
        tsv_files[output_type] = open('%s_%s.tsv' % (out_base, output_type), 'w')

    # Write the tsv files.
    short_set = set()
    very_short_set = set()
    for h, d in relation_dict.items():
        # Do some pre-processing
        roles = sorted([ag_tpl[1] for ag_tpl in d['agents']])
        ag_by_roles = dict.fromkeys(roles)
        for role in roles:
            ag_by_roles[role] = [ag_tpl[-1] for ag_tpl in d['agents']
                                 if ag_tpl[1] == role]
        if roles == ['OBJECT', 'SUBJECT']:
            data_tpls = [(ag_by_roles['SUBJECT'][0], ag_by_roles['OBJECT'][0],
                          d['type'], str(h))]
        elif set(roles) == {'OTHER'}:
            data_tpls = [(a, b, d['type'], str(h))
                         for a, b in permutations(ag_by_roles['OTHER'], 2)]
        elif d['type'] == 'Conversion':
            continue  # TODO: Handle conversions.
        else:
            print("This is weird...", h, d)
            continue

        # Handle writing the various files.
        if 'full_tsv' in out_types:
            for data_tpl in data_tpls:
                write_tsv_line(tsv_files['full_tsv'], data_tpl)

        if 'short_tsv' in out_types:
            short_tpls = [t[:-1] for t in data_tpls]
            for t in short_tpls:
                if t not in short_set:
                    short_set.add(t)
                    write_tsv_line(tsv_files['short_tsv'], t)

        if 'pairs_tsv' in out_types:
            vs_tpls ={tuple(sorted(t[:-2])) for t in data_tpls}
            for t in vs_tpls:
                if t not in very_short_set:
                    very_short_set.add(t)
                    write_tsv_line(tsv_files['pairs_tsv'], t)

    # Close the tsv files.
    for file_handle in tsv_files.values():
        file_handle.close()

    return relation_dict


@_clockit
def get_evidence(pa_stmt_list, db=None, fix_refs=True):
    """Fill in the evidence for a list of pre-assembled statements.

    Parameters
    ----------
    pa_stmt_list : list[Statement]
        A list of unique statements, generally drawn from the database
        pa_statement table (via `get_statemetns`).
    db : DatabaseManager instance or None
        An instance of a database manager. If None, defaults to the "primary"
        database, as defined in the db_config.ini file in .config/indra.
    fix_refs : bool
        The paper refs within the evidence objects are not populated in the
        database, and thus must be filled using the relations in the database.
        If True (default), the `pmid` field of each Statement Evidence object
        is set to the correct PMIDs, or None if no PMID is available. If False,
        the `pmid` field defaults to the value populated by the reading
        system.

    Returns
    -------
    None - modifications are made to the Statements "in-place".
    """
    if db is None:
        db = get_primary_db()

    # Turn the list into a dict.
    stmt_dict = {s.get_hash(shallow=True): s for s in pa_stmt_list}

    # Get the data from the database
    raw_list = db.select_all([db.PAStatements.mk_hash, db.RawStatements],
                             db.PAStatements.mk_hash.in_(stmt_dict.keys()),
                             *db.join(db.PAStatements, db.RawStatements))

    # Note that this step depends on the ordering being maintained.
    mk_hashes, raw_stmt_objs = zip(*raw_list)
    raw_stmts = get_raw_stmts_frm_db_list(db, raw_stmt_objs, fix_refs,
                                          with_sids=False)
    raw_stmt_mk_pairs = zip(mk_hashes, raw_stmts)

    # Now attach the evidence
    for mk_hash, raw_stmt in raw_stmt_mk_pairs:
        # Each raw statement can have just one piece of evidence.
        stmt_dict[mk_hash].evidence.append(raw_stmt.evidence[0])

    return


def get_statements_from_hashes():
    """Retrieve statement objects given only a statement hash."""
    pass


def get_support():
    """Populate the supports and supported_by lists of the given statements."""
    pass


def get_related_papers():
    """Get papers with references to the same mechanisms."""
    pass


def _get_trids(db, id_val, id_type):
    """Return text ref IDs corresponding to any ID type and value."""
    # Get the text ref id(s)
    if id_type in ['trid']:
        trid_list = [int(id_val)]
    else:
        id_types = ['pmid', 'pmcid', 'doi', 'pii', 'url', 'manuscript_id']
        if id_type not in id_types:
            raise ValueError('id_type must be one of: %s' % str(id_types))
        constraint = (getattr(db.TextRef, id_type) == id_val)
        trid_list = [trid for trid, in db.select_all(db.TextRef.id, constraint)]
    return trid_list