from __future__ import absolute_import, print_function, unicode_literals
from builtins import dict, str

import json
import logging
from functools import wraps
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger('db_preassembly')


if __name__ == '__main__':
    # NOTE: PEP8 will complain about this, however having the args parsed up
    # here prevents a long wait just to fined out you entered a command wrong.
    from argparse import ArgumentParser
    parser = ArgumentParser(
        description='Manage content on INDRA\'s database.'
        )
    parser.add_argument(
        choices=['create', 'update'],
        dest='task',
        help=('Choose whether you want to perform an initial upload or update '
              'the existing content on the database.')
        )
    parser.add_argument(
        '-c', '--continue',
        dest='continuing',
        action='store_true',
        help='Continue uploading or updating, picking up where you left off.'
        )
    parser.add_argument(
        '-n', '--num_procs',
        dest='num_procs',
        type=int,
        default=1,
        help=('Select the number of processors to use during this operation. '
              'Default is 1.')
        )
    parser.add_argument(
        '-b', '--batch',
        type=int,
        default=10000,
        help=("Select the number of statements loaded at a time. More "
              "statements at a time will run faster, but require more memory.")
    )
    parser.add_argument(
        '-d', '--debug',
        dest='debug',
        action='store_true',
        help='Run with debugging level output.'
        )
    parser.add_argument(
        '-D', '--database',
        default='primary',
        help=('Select a database from the names given in the config or '
              'environment, for example primary is INDRA_DB_PRIMAY in the '
              'config file and INDRADBPRIMARY in the environment. The default '
              'is \'primary\'. Note that this is overwridden by use of the '
              '--test flag if \'test\' is not a part of the name given.')
        )
    args = parser.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)
        from indra.db.database_manager import logger as db_logger
        db_logger.setLevel(logging.DEBUG)


import indra.tools.assemble_corpus as ac
from indra.util import batch_iter
from indra.statements import Statement
from indra.preassembler import Preassembler
from indra.preassembler.hierarchy_manager import hierarchies

from indra.db.util import insert_pa_stmts, distill_stmts, get_db


def _handle_update_table(func):
    @wraps(func)
    def run_and_record_update(cls, db, *args, **kwargs):
        run_datetime = datetime.utcnow()
        completed = func(cls, db, *args, **kwargs)
        if completed:
            is_corpus_init = (func.__name__ == 'create_corpus')
            db.insert('preassembly_updates', corpus_init=is_corpus_init,
                      run_datetime=run_datetime)
        return completed
    return run_and_record_update


def _stmt_from_json(stmt_json_bytes):
    return Statement._from_json(json.loads(stmt_json_bytes.decode('utf-8')))


class IndraDBPreassemblyError(Exception):
    pass


class PreassemblyManager(object):
    """Class used to manage the preassembly pipeline

    Parameters
    ----------
    n_proc : int
        Select the number of processes that will be used when performing
        preassembly. Default is 1.
    batch_size : int
        Select the maximum number of statements you wish to be handled at a
        time. In general, a larger batch size will somewhat be faster, but
        require much more memory.
    """
    def __init__(self, n_proc=1, batch_size=10000, print_logs=False):
        self.n_proc = n_proc
        self.batch_size = batch_size
        self.pa = Preassembler(hierarchies)
        self.__tag = 'Unpurposed'
        self.__print_logs = print_logs
        return

    def _get_latest_updatetime(self, db):
        """Get the date of the latest update."""
        update_list = db.select_all(db.PreassemblyUpdates)
        if not len(update_list):
            logger.warning("The preassembled corpus has not been initialized, "
                           "or else the updates table has not been populated.")
            return None
        return max([u.run_datetime for u in update_list])

    def _pa_batch_iter(self, db, in_mks=None, ex_mks=None):
        """Return an iterator over batches of preassembled statements.

        This avoids the need to load all such statements from the database into
        RAM at the same time (as this can be quite large).

        You may limit the set of pa_statements loaded by providing a set/list of
        matches-keys of the statements you wish to include.
        """
        if in_mks is None and ex_mks is None:
            db_stmt_iter = db.select_all(db.PAStatements.json,
                                         yield_per=self.batch_size)
        elif ex_mks is None and in_mks is not None:
            if not in_mks:
                return []
            db_stmt_iter = db.select_all(
                db.PAStatements.json,
                db.PAStatements.mk_hash.in_(in_mks),
                yield_per=self.batch_size
                )
        elif in_mks is None and ex_mks is not None:
            if not ex_mks:
                return []
            db_stmt_iter = db.select_all(
                db.PAStatements.json,
                db.PAStatements.mk_hash.notin_(ex_mks),
                yield_per=self.batch_size
                )
        elif in_mks and ex_mks:
            db_stmt_iter = db.select_all(
                db.PAStatements.json,
                db.PAStatements.mk_hash.notin_(ex_mks),
                db.PAStatements.mk_hash.in_(in_mks),
                yield_per=self.batch_size
                )
        else:  # Neither is None, and both are empty.
            return []

        pa_stmts = (_stmt_from_json(s_json) for s_json, in db_stmt_iter)
        return batch_iter(pa_stmts, self.batch_size, return_func=list)

    def _get_unique_statements(self, db, stmt_tpls, num_stmts, mk_done=None):
        """Get the unique Statements from the raw statements."""
        if mk_done is None:
            mk_done = set()

        new_mk_set = set()
        stmt_batches = batch_iter(stmt_tpls, self.batch_size, return_func=list)
        num_batches = num_stmts/self.batch_size
        for i, stmt_tpl_batch in enumerate(stmt_batches):
            self._log("Processing batch %d/%d of %d/%d statements."
                       % (i, num_batches, len(stmt_tpl_batch), num_stmts))
            unique_stmts, evidence_links = \
                self._make_unique_statement_set(stmt_tpl_batch)
            new_unique_stmts = []
            for s in unique_stmts:
                s_hash = s.get_hash(shallow=True)
                if s_hash not in (mk_done | new_mk_set):
                    new_mk_set.add(s_hash)
                    new_unique_stmts.append(s)
            insert_pa_stmts(db, new_unique_stmts)
            db.copy('raw_unique_links', evidence_links,
                    ('pa_stmt_mk_hash', 'raw_stmt_id'))
        self._log("Added %d new pa statements into the database."
                    % len(new_mk_set))
        return new_mk_set

    @_handle_update_table
    def create_corpus(self, db, continuing=False):
        """Initialize the table of preassembled statements.

        This method will find the set of unique knowledge represented in the
        table of raw statements, and it will populate the table of preassembled
        statements (PAStatements/pa_statements), while maintaining links between
        the raw statements and their unique (pa) counterparts. Furthermore, the
        refinement/support relationships between unique statements will be found
        and recorded in the PASupportLinks/pa_support_links table.

        For more detail on preassembly, see indra/preassembler/__init__.py
        """
        self.__tag = 'create'
        # Get the statements
        stmt_ids = distill_stmts(db, num_procs=self.n_proc)
        if continuing:
            self._log("Getting set of statements already de-duplicated...")
            checked_raw_stmt_ids, pa_stmt_hashes = \
                zip(*db.select_all([db.RawUniqueLinks.raw_stmt_uuid,
                                    db.RawUniqueLinks.pa_stmt_mk_hash]))
            stmt_ids -= set(checked_raw_stmt_ids)
            done_pa_ids = set(pa_stmt_hashes)
            self._log("Found %d preassembled statements already done."
                        % len(done_pa_ids))
        else:
            done_pa_ids = set()
        stmts = ((sid, _stmt_from_json(s_json)) for sid, s_json
                 in db.select_all([db.RawStatements.id, db.RawStatements.json],
                                  db.RawStatements.id.in_(stmt_ids),
                                  yield_per=self.batch_size))
        self._log("Found %d statements in all." % len(stmt_ids))

        # Get the set of unique statements
        if stmt_ids:
            self._get_unique_statements(db, stmts, len(stmt_ids), done_pa_ids)

        # If we are continuing, check for support links that were already found.
        if continuing:
            self._log("Getting pre-existing links...")
            db_existing_links = db.select_all([
                db.PASupportLinks.supporting_mk_hash,
                db.PASupportLinks.supporting_mk_hash
                ])
            existing_links = {tuple(res) for res in db_existing_links}
            self._log("Found %d existing links." % len(existing_links))
        else:
            existing_links = set()

        # Now get the support links between all batches.
        support_links = set()
        for i, outer_batch in enumerate(self._pa_batch_iter(db)):
            # Get internal support links
            self._log('Getting internal support links outer batch %d.' % i)
            some_support_links = self._get_support_links(outer_batch,
                                                         poolsize=self.n_proc)
            outer_mk_hashes = {s.get_hash(shallow=True) for s in outer_batch}

            # Get links with all other batches
            ib_iter = self._pa_batch_iter(db, ex_mks=outer_mk_hashes)
            for j, inner_batch in enumerate(ib_iter):
                split_idx = len(inner_batch)
                full_list = inner_batch + outer_batch
                self._log('Getting support compared to other batch %d of outer'
                          'batch %d.' % (j, i))
                some_support_links |= \
                    self._get_support_links(full_list, split_idx=split_idx,
                                            poolsize=self.n_proc)

            # Add all the new support links
            support_links |= (some_support_links - existing_links)

            # There are generally few support links compared to the number of
            # statements, so it doesn't make sense to copy every time, but for
            # long preassembly, this allows for better failure recovery.
            if len(support_links) >= self.batch_size:
                self._log("Copying batch of %d support links into db."
                          % len(support_links))
                db.copy('pa_support_links', support_links,
                        ('supported_mk_hash', 'supporting_mk_hash'))
                existing_links |= support_links
                support_links = set()

        # Insert any remaining support links.
        if support_links:
            self._log("Copying final batch of %d support links into db."
                      % len(support_links))
            db.copy('pa_support_links', support_links,
                    ('supported_mk_hash', 'supporting_mk_hash'))

        return True

    def _get_new_stmt_ids(self, db):
        """Get all the uuids of statements not included in evidence."""
        old_id_q = db.filter_query(
            db.RawStatements.id,
            db.RawStatements.id == db.RawUniqueLinks.raw_stmt_id
        )
        new_sid_q = db.filter_query(db.RawStatements.id).except_(old_id_q)
        all_new_stmt_ids = {sid for sid, in new_sid_q.all()}
        self._log("Found %d new statement ids." % len(all_new_stmt_ids))
        return all_new_stmt_ids

    @_handle_update_table
    def supplement_corpus(self, db, continuing=False):
        """Update the table of preassembled statements.

        This method will take any new raw statements that have not yet been
        incorporated into the preassembled table, and use them to augment the
        preassembled table.

        The resulting updated table is indistinguishable from the result you
        would achieve if you had simply re-run preassembly on _all_ the
        raw statements.
        """
        self.__tag = 'supplement'
        last_update = self._get_latest_updatetime(db)
        self._log("Latest update was: %s" % last_update)

        # Get the new statements...
        self._log("Loading info about the existing state of preassembly. "
                  "(This may take a little time)")
        new_ids = self._get_new_stmt_ids(db)

        # If we are continuing, check for support links that were already found.
        if continuing:
            self._log("Getting pre-existing links...")
            db_existing_links = db.select_all([
                db.PASupportLinks.supporting_mk_hash,
                db.PASupportLinks.supporting_mk_hash
                ])
            existing_links = {tuple(res) for res in db_existing_links}
            self._log("Found %d existing links." % len(existing_links))
        else:
            existing_links = set()

        # Weed out exact duplicates.
        stmt_ids = distill_stmts(db, num_procs=self.n_proc)
        new_stmt_ids = new_ids & stmt_ids
        self._log("There are %d new distilled raw statement ids."
                  % len(new_stmt_ids))
        new_stmts = ((sid, _stmt_from_json(s_json)) for sid, s_json
                     in db.select_all([db.RawStatements.id,
                                       db.RawStatements.json],
                                      db.RawStatements.id.in_(new_stmt_ids),
                                      yield_per=self.batch_size))

        # Get the set of new unique statements and link to any new evidence.
        old_mk_set = {mk for mk, in db.select_all(db.PAStatements.mk_hash)}
        self._log("Found %d old pa statements." % len(old_mk_set))
        new_mk_set = self._get_unique_statements(db, new_stmts,
                                                 len(new_stmt_ids), old_mk_set)
        self._log("Found %d new pa statements." % len(new_mk_set))

        # Now find the new support links that need to be added.
        new_support_links = set()
        new_stmt_iter = self._pa_batch_iter(db, in_mks=new_mk_set)
        for i, npa_batch in enumerate(new_stmt_iter):

            # Compare internally
            self._log("Getting support for new pa batch %d." % i)
            some_support_links = self._get_support_links(npa_batch)

            # Compare against the other new batch statements.
            diff_new_mks = new_mk_set - {s.get_hash(shallow=True)
                                         for s in npa_batch}
            other_new_stmt_iter =  self._pa_batch_iter(db, in_mks=diff_new_mks)
            for j, diff_npa_batch in enumerate(other_new_stmt_iter):
                split_idx = len(npa_batch)
                full_list = npa_batch + diff_npa_batch
                self._log("Comparing %d to batch %d of other new statements."
                          % (i, j))
                some_support_links |= \
                    self._get_support_links(full_list, split_idx=split_idx,
                                            poolsize=self.n_proc)

            # Compare against the existing statements.
            old_stmt_iter =  self._pa_batch_iter(db, in_mks=old_mk_set)
            for k, opa_batch in enumerate(old_stmt_iter):
                split_idx = len(npa_batch)
                full_list = npa_batch + opa_batch
                self._log("Comparing %d to batch of %d of old statements."
                          % (i, k))
                some_support_links |= \
                    self._get_support_links(full_list, split_idx=split_idx,
                                            poolsize=self.n_proc)

            new_support_links |= (some_support_links - existing_links)

            # There are generally few support links compared to the number of
            # statements, so it doesn't make sense to copy every time, but for
            # long preassembly, this allows for better failure recovery.
            if len(new_support_links) >= self.batch_size:
                self._log("Copying batch of %d support links into db."
                          % len(new_support_links))
                db.copy('pa_support_links', new_support_links,
                        ('supported_mk_hash', 'supporting_mk_hash'))
                existing_links |= new_support_links
                new_support_links = set()

        # Insert any remaining support links.
        if new_support_links:
            self._log("Copying batch final of %d support links into db."
                      % len(new_support_links))
            db.copy('pa_support_links', new_support_links,
                    ('supported_mk_hash', 'supporting_mk_hash'))
            existing_links |= new_support_links

        return True

    def _log(self, msg, level='info'):
        """Applies a task specific tag to the log message."""
        if self.__print_logs:
            print("Preassembly Manager [%s] (%s): %s"
                  % (datetime.now(), self.__tag, msg))
        getattr(logger, level)("(%s) %s" % (self.__tag, msg))

    def _make_unique_statement_set(self, stmt_tpls):
        """Perform grounding, sequence mapping, and find unique set from stmts.

        This method returns a list of statement objects, as well as a set of
        tuples of the form (uuid, matches_key) which represent the links between
        raw (evidence) statements and their unique/preassembled counterparts.
        """
        stmts = []
        uuid_sid_dict = {}
        for sid, stmt in stmt_tpls:
            uuid_sid_dict[stmt.uuid] = sid
            stmts.append(stmt)
        self._log("Map grounding...")
        stmts = ac.map_grounding(stmts)
        self._log("Map sequences...")
        stmts = ac.map_sequence(stmts)
        self._log("Condense into unique statements...")
        stmt_groups = self.pa._get_stmt_matching_groups(stmts)
        unique_stmts = []
        evidence_links = defaultdict(lambda: set())
        for _, duplicates in stmt_groups:
            # Get the first statement and add the evidence of all subsequent
            # Statements to it
            for stmt_ix, stmt in enumerate(duplicates):
                if stmt_ix == 0:
                    first_stmt = stmt.make_generic_copy()
                    stmt_hash = first_stmt.get_hash(shallow=True)
                evidence_links[stmt_hash].add(uuid_sid_dict[stmt.uuid])
            # This should never be None or anything else
            assert isinstance(first_stmt, type(stmt))
            unique_stmts.append(first_stmt)
        return unique_stmts, flatten_evidence_dict(evidence_links)

    def _get_support_links(self, unique_stmts, **generate_id_map_kwargs):
        """Find the links of refinement/support between statements."""
        id_maps = self.pa._generate_id_maps(unique_stmts,
                                            **generate_id_map_kwargs)
        ret = set()
        for ix_pair in id_maps:
            if ix_pair[0] == ix_pair[1]:
                assert False, "Self-comparison occurred."
            hash_pair = \
                tuple([unique_stmts[ix].get_hash(True) for ix in ix_pair])
            if hash_pair[0] == hash_pair[1]:
                assert False, "Input list included duplicates."
            ret.add(hash_pair)

        return ret


def make_graph(unique_stmts, match_key_maps):
    """Create a networkx graph of the statement and their links."""
    import networkx as nx
    g = nx.Graph()
    link_matches = {m for l in match_key_maps for m in l}
    unique_stmts_dict = {}
    for stmt in unique_stmts:
        if stmt.matches_key() in link_matches:
            g.add_node(stmt)
            unique_stmts_dict[stmt.matches_key()] = stmt

    for k1, k2 in match_key_maps:
        g.add_edge(unique_stmts_dict[k1], unique_stmts_dict[k2])

    return g


def flatten_evidence_dict(ev_dict):
    return {(u_stmt_key, ev_stmt_uuid)
            for u_stmt_key, ev_stmt_uuid_set in ev_dict.items()
            for ev_stmt_uuid in ev_stmt_uuid_set}


if __name__ == '__main__':
    print("Getting %s database." % args.database)
    db = get_db(args.database)
    assert db is not None
    db.grab_session()
    pm = PreassemblyManager(args.num_procs, args.batch)

    print("Beginning to %s preassembled corpus." % args.task)
    if args.task == 'create':
        pm.create_corpus(db, args.continuing)
    elif args.task == 'update':
        pm.supplement_corpus(db)
    else:
        raise IndraDBPreassemblyError('Unrecognized task: %s.' % args.task)
