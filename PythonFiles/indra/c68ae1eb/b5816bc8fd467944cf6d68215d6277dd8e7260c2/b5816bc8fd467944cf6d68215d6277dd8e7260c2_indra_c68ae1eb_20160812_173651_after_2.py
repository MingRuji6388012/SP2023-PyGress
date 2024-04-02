from indra import trips, reach
from indra.literature import id_lookup
from assembly_eval import have_file, run_assembly
import rasmodel
import pickle
import csv

if __name__ == '__main__':
    pmc_ids = [s.strip() for s in open('pmcids.txt', 'rt').readlines()]

    # Load the REACH reading output
    with open('reach/reach_stmts_batch_4_eval.pkl') as f:
        reach_stmts = pickle.load(f)

    # Load the PMID to PMCID map
    pmcid_to_pmid = {}
    with open('pmc_batch_4_id_map.txt') as f:
        csvreader = csv.reader(f, delimiter='\t')
        for row in csvreader:
            pmcid_to_pmid[row[0]] = row[1]

    for pmcid in pmc_ids:
        print 'Processing %s...' % pmcid
        # Process TRIPS
        trips_fname = 'trips/' + pmcid + '.ekb'
        tp = trips.process_xml(open(trips_fname).read())
        # Get REACH statements
        reach_stmts_for_pmcid = reach_stmts.get(pmcid_to_pmid[pmcid], [])
        if not reach_stmts_for_pmcid:
            print "No REACH statements for %s" % pmcid
        # Get prior statements
        rasmodel_stmts = rasmodel.get_statements()
        # Combine all statements
        all_statements = tp.statements + reach_stmts_for_pmcid
        # Run assembly
        run_assembly(all_statements, 'combined', pmcid,
                     background_assertions=rasmodel_stmts)
