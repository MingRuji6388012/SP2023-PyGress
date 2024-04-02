import sys
import shutil
from indra import reach
from indra.literature import pmc_client, get_full_text, id_lookup
from assembly_eval import have_file, run_assembly
import csv
import os
import pickle

if __name__ == '__main__':
    # This script assumes that the papers have been processed offline,
    # e.g., using the submit_reading_pipeline.py script on Amazon,
    # and the results placed in a dict (mapping PMID -> lists of statements)
    # and put in the folder reach/reach_stmts_batch_4_eval.pkl.
    folder = 'reach'

    # Load the PMID to PMCID map
    pmid_to_pmcid = {}
    with open('pmc_batch_4_id_map.txt') as f:
        csvreader = csv.reader(f, delimiter='\t')
        for row in csvreader:
            pmid_to_pmcid[row[1]] = row[0]

    # Load the REACH reading output
    with open(os.path.join(folder, 'reach_stmts_batch_4_eval.pkl')) as f:
        stmts = pickle.load(f)

    # Iterate over all of the PMIDs
    for pmid, stmts in stmts.items():
        pmcid = pmid_to_pmcid[pmid]
        run_assembly(stmts, folder, pmcid)
