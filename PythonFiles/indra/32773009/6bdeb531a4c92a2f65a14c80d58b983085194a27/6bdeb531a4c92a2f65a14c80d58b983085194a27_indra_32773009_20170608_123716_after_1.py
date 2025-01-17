import sys
import json
import logging
from bottle import route, run, request, default_app, response
from indra import trips, reach, bel, biopax
from indra.statements import *
from indra.assemblers import PysbAssembler, CxAssembler, GraphAssembler,\
                             CyJSAssembler, SifAssembler
import indra.tools.assemble_corpus as ac

logger = logging.getLogger('rest_api')
logger.setLevel(logging.DEBUG)


#   ALLOW CORS   #
def allow_cors(func):
    """This is a decorator which enable CORS for the specified endpoint."""
    def wrapper(*args, **kwargs):
        response.headers['Access-Control-Allow-Origin'] = '*'
        return func(*args, **kwargs)
    return wrapper

#     INPUT PROCESSING     #


#   TRIPS   #
@route('/trips/process_text', method='POST')
@allow_cors
def trips_process_text():
    """Process text with TRIPS and return INDRA Statements."""
    response = request.body.read().decode('utf-8')
    body = json.loads(response)
    text = body.get('text')
    tp = trips.process_text(text)
    if tp and tp.statements:
        stmts = stmts_to_json(tp.statements)
        res = {'statements': stmts}
        return res
    else:
        res = {'statements': []}
    return res


@route('/trips/process_xml', method='POST')
@allow_cors
def trips_process_xml():
    """Process TRIPS EKB XML and return INDRA Statements."""
    response = request.body.read().decode('utf-8')
    body = json.loads(response)
    xml_str = body.get('xml_str')
    tp = trips.process_xml(xml_str)
    if tp and tp.statements:
        stmts = stmts_to_json(tp.statements)
        res = {'statements': stmts}
        return res
    else:
        res = {'statements': []}
    return res
################


#   REACH   #
@route('/reach/process_text', method='POST')
@allow_cors
def reach_process_text():
    """Process text with REACH and return INDRA Statements."""
    response = request.body.read().decode('utf-8')
    body = json.loads(response)
    text = body.get('text')
    rp = reach.process_text(text)
    if rp and rp.statements:
        stmts = stmts_to_json(rp.statements)
        res = {'statements': stmts}
        return res
    else:
        res = {'statements': []}
    return res


@route('/reach/process_json', method='POST')
@allow_cors
def reach_process_json():
    """Process REACH json and return INDRA Statements."""
    response = request.body.read().decode('utf-8')
    body = json.loads(response)
    json_str = body.get('json')
    rp = reach.process_json_str(json_str)
    if rp and rp.statements:
        stmts = stmts_to_json(rp.statements)
        res = {'statements': stmts}
        return res
    else:
        res = {'statements': []}
    return res


@route('/reach/process_pmc', method='POST')
@allow_cors
def reach_process_pmc():
    """Process PubMedCentral article and return INDRA Statements."""
    response = request.body.read().decode('utf-8')
    body = json.loads(response)
    pmcid = body.get('pmcid')
    rp = reach.process_pmc(pmcid)
    if rp and rp.statements:
        stmts = stmts_to_json(rp.statements)
        res = {'statements': stmts}
        return res
    else:
        res = {'statements': []}
    return res
##################


#   BEL   #
@route('/bel/process_ndex_neighborhood', method='POST')
@allow_cors
def bel_process_ndex_neighborhood():
    """Process BEL Large Corpus neighborhood and return INDRA Statements."""
    response = request.body.read().decode('utf-8')
    body = json.loads(response)
    genes = body.get('genes')
    bp = bel.process_ndex_neighborhood(genes)
    if bp and bp.statements:
        stmts = stmts_to_json(bp.statements)
        res = {'statements': stmts}
        return res
    else:
        res = {'statements': []}
    return res


@route('/bel/process_belrdf', method='POST')
@allow_cors
def bel_process_belrdf():
    """Process BEL RDF and return INDRA Statements."""
    response = request.body.read().decode('utf-8')
    body = json.loads(response)
    belrdf = body.get('belrdf')
    bp = bel.process_belrdf(belrdf)
    if bp and bp.statements:
        stmts = stmts_to_json(bp.statements)
        res = {'statements': stmts}
        return res
    else:
        res = {'statements': []}
    return res


#   BioPAX   #
@route('/biopax/process_pc_pathsbetween', method='POST')
@allow_cors
def biopax_process_pc_pathsbetween():
    """Process PathwayCommons paths between genes, return INDRA Statements."""
    response = request.body.read().decode('utf-8')
    body = json.loads(response)
    genes = body.get('genes')
    bp = biopax.process_pc_pathsbetween(genes)
    if bp and bp.statements:
        stmts = stmts_to_json(bp.statements)
        res = {'statements': stmts}
        return res
    else:
        res = {'statements': []}
    return res


@route('/biopax/process_pc_pathsfromto', method='POST')
@allow_cors
def biopax_process_pc_pathsfromto():
    """Process PathwayCommons paths from-to genes, return INDRA Statements."""
    response = request.body.read().decode('utf-8')
    body = json.loads(response)
    source = body.get('source')
    target = body.get('target')
    bp = biopax.process_pc_pathsfromto(source, target)
    if bp and bp.statements:
        stmts = stmts_to_json(bp.statements)
        res = {'statements': stmts}
        return res
    else:
        res = {'statements': []}
    return res


@route('/biopax/process_pc_neighborhood', method='POST')
@allow_cors
def biopax_process_pc_neighborhood():
    """Process PathwayCommons neighborhood, return INDRA Statements."""
    response = request.body.read().decode('utf-8')
    body = json.loads(response)
    genes = body.get('genes')
    bp = biopax.process_pc_neighborhood(genes)
    if bp and bp.statements:
        stmts = stmts_to_json(bp.statements)
        res = {'statements': stmts}
        return res
    else:
        res = {'statements': []}
    return res

#   OUTPUT ASSEMBLY   #


#   PYSB   #
@route('/assemblers/pysb', method='POST')
@allow_cors
def assemble_pysb():
    """Assemble INDRA Statements and return PySB model string."""
    response = request.body.read().decode('utf-8')
    body = json.loads(response)
    stmts_json = body.get('statements')
    stmts = stmts_from_json(stmts_json)
    pa = PysbAssembler()
    pa.add_statements(stmts)
    pa.make_model()
    model_str = pa.print_model()
    res = {'model': model_str}
    return res


#   CX   #
@route('/assemblers/cx', method='POST')
@allow_cors
def assemble_cx():
    """Assemble INDRA Statements and return CX network json."""
    response = request.body.read().decode('utf-8')
    body = json.loads(response)
    stmts_json = body.get('statements')
    stmts = stmts_from_json(stmts_json)
    ca = CxAssembler(stmts)
    model_str = ca.make_model()
    res = {'model': model_str}
    return res


#  GRAPH   #
@route('/assemblers/graph', method='POST')
@allow_cors
def assemble_graph():
    """Assemble INDRA Statements and return Graphviz graph dot string."""
    response = request.body.read().decode('utf-8')
    body = json.loads(response)
    stmts_json = body.get('statements')
    stmts = stmts_from_json(stmts_json)
    ga = GraphAssembler(stmts)
    model_str = ga.make_model()
    res = {'model': model_str}
    return res


#   CyJS   #
@route('/assemblers/cyjs', method='POST')
@allow_cors
def assemble_cyjs():
    """Assemble INDRA Statements and return Cytoscape JS network."""
    response = request.body.read().decode('utf-8')
    body = json.loads(response)
    stmts_json = body.get('statements')
    stmts = stmts_from_json(stmts_json)
    cja = CyJSAssembler()
    cja.add_statements(stmts)
    cja.make_model(grouping=True)
    model_str = cja.print_cyjs_graph()
    return model_str


@route('/assemblers/sif/loopy', method='POST')
@allow_cors
def assemble_loopy():
    """Assemble INDRA Statements into a Loopy model using SIF Assembler."""
    response = request.body.read().decode('utf-8')
    body = json.loads(response)
    stmts_json = body.get('statements')
    stmts = stmts_from_json(stmts_json)
    sa = SifAssembler(stmts)
    sa.make_model(use_name_as_key=True)
    model_str = sa.print_loopy(as_url=True)
    res = {'loopy_url': model_str}
    return res


@route('/preassembly/map_grounding', method='POST')
@allow_cors
def map_grounding():
    """Map grounding on a list of INDRA Statements."""
    response = request.body.read().decode('utf-8')
    body = json.loads(response)
    stmts_json = body.get('statements')
    stmts = stmts_from_json(stmts_json)
    stmts_out = ac.map_grounding(stmts)
    if stmts_out:
        stmts_json = stmts_to_json(stmts_out)
        res = {'statements': stmts_json}
        return res
    else:
        res = {'statements': []}
    return res


@route('/preassembly/map_sequence', method='POST')
@allow_cors
def map_grounding():
    """Map sequence on a list of INDRA Statements."""
    response = request.body.read().decode('utf-8')
    body = json.loads(response)
    stmts_json = body.get('statements')
    stmts = stmts_from_json(stmts_json)
    stmts_out = ac.map_sequence(stmts)
    if stmts_out:
        stmts_json = stmts_to_json(stmts_out)
        res = {'statements': stmts_json}
        return res
    else:
        res = {'statements': []}
    return res


@route('/preassembly/run_preassembly', method='POST')
@allow_cors
def run_preassembly():
    """Run preassembly on a list of INDRA Statements."""
    response = request.body.read().decode('utf-8')
    body = json.loads(response)
    stmts_json = body.get('statements')
    stmts = stmts_from_json(stmts_json)
    stmts_out = ac.run_preassembly(stmts)
    if stmts_out:
        stmts_json = stmts_to_json(stmts_out)
        res = {'statements': stmts_json}
        return res
    else:
        res = {'statements': []}
    return res


@route('/preassembly/filter_by_type', method='POST')
@allow_cors
def filter_by_type():
    """Filter to a given INDRA Statement type."""
    response = request.body.read().decode('utf-8')
    body = json.loads(response)
    stmts_json = body.get('statements')
    stmt_type_str = body.get('type')
    stmt_type_str = stmt_type_str.capitalize()
    stmt_type = getattr(sys.modules[__name__], stmt_type_str)
    stmts = stmts_from_json(stmts_json)
    stmts_out = ac.filter_by_type(stmts, stmt_type)
    if stmts_out:
        stmts_json = stmts_to_json(stmts_out)
        res = {'statements': stmts_json}
        return res
    else:
        res = {'statements': []}
    return res


@route('/preassembly/filter_grounded_only', method='POST')
@allow_cors
def filter_grounded_only():
    """Filter to grounded Statements only."""
    response = request.body.read().decode('utf-8')
    body = json.loads(response)
    stmts_json = body.get('statements')
    stmts = stmts_from_json(stmts_json)
    stmts_out = ac.filter_grounded_only(stmts)
    if stmts_out:
        stmts_json = stmts_to_json(stmts_out)
        res = {'statements': stmts_json}
        return res
    else:
        res = {'statements': []}
    return res


if __name__ == '__main__':
    app = default_app()
    run(app, host='0.0.0.0', port='8080')
