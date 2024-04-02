from __future__ import absolute_import, print_function, unicode_literals
from builtins import dict, str

import pickle
from os import path, mkdir
from nose import SkipTest

from indra.tools.reading.read_pmids import READER_DICT, get_proc_num,\
    get_mem_total
from indra.tools.reading.read_db import _convert_id_entry, get_content,\
    get_clauses, post_reading_output, read_content

from indra.tests.test_db import get_db as get_test_db
from indra.tests.test_db import get_db_with_content

# ==============================================================================
# Tests for OLD reading pipeline that did not use the database.
# ==============================================================================


PMID_LIST = [
    '27085964',
    '28739733',
    '18201725',
    '21655183',
    '16254254',
    '15899863',
    '12122017',
    '19426868',
    # '18317068',
    # '24657168'
    ]
BASENAME = 'test_tmp'
TMP_DIR_FMT = '%s_%%s' % BASENAME
OUTPUT_FILE_FMT = '%s_stmts_0-10.pkl' % TMP_DIR_FMT


def _call_reader(reader, num_cores):
    out_dir = TMP_DIR_FMT % reader
    if not path.exists(out_dir):
        mkdir(out_dir)
    stmts = READER_DICT[reader](
        PMID_LIST,
        TMP_DIR_FMT % reader,
        num_cores,
        0,
        len(PMID_LIST),
        True,
        False
        )
    return stmts


def _check_blind_result(reader):
    output_file = OUTPUT_FILE_FMT % reader
    assert path.exists(output_file),\
        "Expected output pickle file missing: %s." % output_file
    with open(output_file, 'rb') as f:
        pkl_out = pickle.load(f)
    assert reader in pkl_out.keys(),\
        "Pickle file does not contain key for reader."
    assert len(pkl_out[reader]),\
        "No statements found."


def _check_result(stmts):
    assert len(stmts), "No statements found."


def test_get_proc_num():
    get_proc_num()


def test_get_mem_total():
    get_mem_total()


def test_reach_one_core():
    if get_mem_total() < 8:
        raise SkipTest("Not enough memory.")
    stmts = _call_reader('reach', 1)
    _check_result(stmts)


def test_reach_two_core():
    if get_mem_total() < 8:
        raise SkipTest("Not enough memory.")
    if get_proc_num() <= 2:
        raise SkipTest("Not enough processes.")
    stmts = _call_reader('reach', 2)
    _check_result(stmts)


def test_sparser_one_core():
    stmts = _call_reader('sparser', 1)
    _check_result(stmts)


def test_sparser_two_core():
    if get_proc_num() <= 2:
        raise SkipTest("Not enough processes.")
    stmts = _call_reader('sparser', 2)
    _check_result(stmts)

# ==============================================================================
# Tests for NEW reading pipeline which uses the database.
# ==============================================================================


def test_convert_id_entry():
    id_entry = 'pmid\t: 12345\n'
    res = _convert_id_entry(id_entry)
    assert len(res) == 2 and res[0] == 'pmid' and res[1] == '12345'


def test_get_clauses():
    db = get_test_db()
    id_str_list = ['pmid:17399955']
    clauses = get_clauses(id_str_list, db.TextRef)
    assert len(clauses)


def test_get_content():
    id_str_list = ['pmid:17399955']
    content = get_content(id_str_list)
    assert len(list(content)) == 1, "Failed to get correct content."


def test_reading():
    "Test that the contents of the database can be read."
    db = get_db_with_content()
    tc_list = db.select_all(db.TextContent)
    res = read_content(tc_list, ['reach'], verbose=True, force_read=True,
                       force_fulltext=False)
    assert len(res) == len(tc_list), "Not all text content successfully read."


def test_reading_content_insert():
    "Test the content copying functionality of read_db."
    db = get_test_db()
    with open('sample_reach_outputs.pkl') as f:
        reading_output = pickle.load(f)
    post_reading_output(reading_output, db=db)
    r_list = db.select_all(db.Readings)
    assert len(r_list) == len(reading_output), "Not all reading output posted."
