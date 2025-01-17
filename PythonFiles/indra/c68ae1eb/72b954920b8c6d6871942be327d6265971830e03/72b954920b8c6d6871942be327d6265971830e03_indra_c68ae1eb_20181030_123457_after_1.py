import os
import csv
import logging
from os.path import abspath, dirname, join
import rdflib
from indra.util import read_unicode_csv, write_unicode_csv


logger = logging.getLogger('go_client')


go_mappings_file = join(dirname(abspath(__file__)), '..', 'resources',
                 'go_id_label_mappings.tsv')


# This file can be donwloaded from: http://geneontology.org/ontology/go.owl
go_owl_path = join(dirname(abspath(__file__)), '..', '..', 'data', 'go.owl')


# Dictionary to store GO ID->Label mappings
go_mappings = {}
for go_id, go_label in read_unicode_csv(go_mappings_file, delimiter='\t'):
    go_mappings[go_id] = go_label


_prefixes = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX go: <http://purl.obolibrary.org/obo/go#>
    PREFIX obo: <http://purl.obolibrary.org/obo/>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX oboInOwl: <http://www.geneontology.org/formats/oboInOwl#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    """



# Lazily initialize the GO RDF graph because parsing the RDF is expensive
_go_graph = None


def load_go_graph(go_fname):
    """Load the GO data from an OWL file and parse into an RDF graph.

    Parameters
    ----------
    go_fname : str
        Path to the GO OWL file. Can be downloaded from
        http://geneontology.org/ontology/go.owl.

    Returns
    -------
    rdflib.Graph
        RDF graph containing GO data.
    """
    global _go_graph
    if _go_graph is None:
        _go_graph = rdflib.Graph()
        logger.info("Parsing GO OWL file")
        _go_graph.parse(os.path.abspath(go_fname))
    return _go_graph


def get_go_label(go_id):
    """Get label corresponding to a given GO identifier.

    Parameters
    ----------
    go_id : str
        The GO identifier. Should include the `GO:` prefix, e.g., `GO:1903793`
        (positive regulation of anion transport).

    Returns
    -------
    str
        Label corresponding to the GO ID.
    """
    return go_mappings.get(go_id)


def update_id_mappings(g):
    """Compile all ID->label mappings and save to a TSV file.

    Parameters
    ----------
    g : rdflib.Graph
        RDF graph containing GO data.
    """
    g = load_go_graph(go_owl_path)

    query = _prefixes + """
        SELECT ?id ?label
        WHERE {
            ?class oboInOwl:id ?id .
            ?class rdfs:label ?label
        }
    """
    logger.info("Querying for GO ID mappings")
    res = g.query(query)
    mappings = []
    for id_lit, label_lit in sorted(res, key=lambda x: x[0]):
        mappings.append((id_lit.value, label_lit.value))
    # Write to file
    write_unicode_csv(go_mappings_file, mappings)


def get_cellular_components(g):
    # Query for direct part_of relationships
    query = _prefixes + """
        SELECT ?id ?label ?supid ?suplabel
        WHERE {
            ?class oboInOwl:hasOBONamespace "cellular_component"^^xsd:string .
            ?class oboInOwl:id ?id .
            ?class rdfs:label ?label .
            ?class rdfs:subClassOf ?sup .
            ?sup oboInOwl:hasOBONamespace "cellular_component"^^xsd:string .
            ?sup oboInOwl:id ?supid .
            ?sup rdfs:label ?suplabel
            }
        """
    logger.info("Running cellular component query 1")
    res1 = g.query(query)
    query = _prefixes + """
        SELECT ?id ?label ?supid ?suplabel
        WHERE {
            ?class oboInOwl:hasOBONamespace "cellular_component"^^xsd:string .
            ?class oboInOwl:id ?id .
            ?class rdfs:label ?label .
            ?class rdfs:subClassOf ?restr .
            ?restr owl:onProperty ?prop .
            ?prop oboInOwl:id "part_of"^^xsd:string .
            ?restr owl:someValuesFrom ?sup .
            ?sup oboInOwl:hasOBONamespace "cellular_component"^^xsd:string .
            ?sup oboInOwl:id ?supid .
            ?sup rdfs:label ?suplabel
            }
        """
    logger.info("Running cellular component query 2")
    res2 = g.query(query)
    res = list(res1) + list(res2)
    component_map = {}
    component_part_map = {}
    for r in res:
        comp_id, comp_name, sup_id, sup_name = [rr.toPython() for rr in r]
        component_map[comp_id] = comp_name
        component_map[sup_id] = sup_name
        try:
            component_part_map[comp_id].append(sup_id)
        except KeyError:
            component_part_map[comp_id] = [sup_id]
    return component_map, component_part_map



