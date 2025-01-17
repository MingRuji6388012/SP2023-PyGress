import sys
import rdflib
import json
import urllib2
from processor import BelProcessor

def process_ndex_neighborhood(gene_names):
    network_id = '9ea3c170-01ad-11e5-ac0f-000c29cb28fb'
    url = 'http://54.218.49.73/network/%s/asBELRDF/query' % network_id
    params = {'searchString': ' '.join(gene_names)}
    req = urllib2.Request(url)
    req.add_header('Content-Type', 'application/json')
    res = urllib2.urlopen(req, json.dumps(params))
    rdf = res.read()
    bp = process_belrdf(rdf)
    bp.print_statements()
    return bp


def process_belrdf(rdf_str):
    # Parse the RDF
    g = rdflib.Graph()
    g.parse(data=rdf_str, format='nt')
    # Build BelPy statements from RDF
    bp = BelProcessor(g)
    bp.get_complexes()
    bp.get_activating_subs()
    bp.get_modifications()
    bp.get_dephosphorylations()
    bp.get_activating_mods()
    bp.get_composite_activating_mods()
    bp.get_activity_activity()

    # Print some output about the process
    bp.print_statement_coverage()
    print "\n--- Converted BelPy Statements -------------"
    bp.print_statements()
    return bp

if __name__ == '__main__':
    # Make sure the user passed in an RDF filename
    if len(sys.argv) < 2:
        print "Usage: python bel_api.py file.rdf"
        sys.exit()
    # We take the RDF filename as the argument
    rdf_filename = sys.argv[1]
    bp = process_belrdf(open(rdf_filename).read())
