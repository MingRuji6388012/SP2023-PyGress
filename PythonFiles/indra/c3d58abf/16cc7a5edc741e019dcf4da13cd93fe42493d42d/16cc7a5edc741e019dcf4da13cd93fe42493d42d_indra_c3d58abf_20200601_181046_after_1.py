import argparse
import inspect
import logging
import json
import base64
from collections import namedtuple
from flask import Flask, request
from flask_restx import Api, Resource, fields, abort
from flask_cors import CORS

from indra import get_config
from indra.sources import trips, reach, bel, biopax, eidos, hume, cwms, sofia
from indra.databases import hgnc_client
from indra.statements import stmts_from_json, get_statement_by_name
from indra.assemblers.pysb import PysbAssembler
import indra.assemblers.pysb.assembler as pysb_assembler
from indra.assemblers.cx import CxAssembler
from indra.assemblers.graph import GraphAssembler
from indra.assemblers.cyjs import CyJSAssembler
from indra.assemblers.sif import SifAssembler
from indra.assemblers.english import EnglishAssembler
from indra.tools.assemble_corpus import *
from indra.databases import cbio_client
from indra.sources.indra_db_rest import get_statements
from indra.sources.ndex_cx.api import process_ndex_network
from indra.sources.reach.api import reach_nxml_url, reach_text_url
from indra.belief.wm_scorer import get_eidos_scorer
from indra.preassembler.hierarchy_manager import get_wm_hierarchies
from indra.preassembler.ontology_mapper import OntologyMapper, wm_ontomap
from indra.pipeline import AssemblyPipeline, pipeline_functions
from indra.preassembler.custom_preassembly import *


logger = logging.getLogger('rest_api')
logger.setLevel(logging.DEBUG)


# Create Flask app, api, namespaces, and models
app = Flask(__name__)
api = Api(
    app, title='INDRA REST API', description='REST API for INDRA webservice')
CORS(app)

preassembly_ns = api.namespace('Preassembly', path='/preassembly/')
sofia_ns = api.namespace('Sofia', path='/sofia/')
eidos_ns = api.namespace('Eidos', path='/eidos/')
hume_ns = api.namespace('Hume', path='/hume/')
bel_ns = api.namespace('BEL', path='/bel/')
trips_ns = api.namespace('TRIPS', path='/trips/')
reach_ns = api.namespace('REACH', path='/reach/')
cwms_ns = api.namespace('CWMS', path='/cwms/')
biopax_ns = api.namespace('BioPAX', path='/biopax/')
assemblers_ns = api.namespace('Assemblers', path='/assemblers/')
ndex_ns = api.namespace('NDEx', path='/')
indra_db_rest_ns = api.namespace('INDRA DB REST', path='/indra_db_rest/')
databases_ns = api.namespace('Databases', path='/databases/')

# Models that can be inherited and reused in different namespaces
dict_model = api.model('dict', {})

stmts_model = api.model('Statements', {
    'statements': fields.List(fields.Nested(dict_model))})
bio_text_model = api.model('BioText', {
    'text': fields.String(example='GRB2 binds SHC.')})
wm_text_model = api.model('WMText', {
    'text': fields.String(example='Rainfall causes floods.')})
jsonld_model = api.model('jsonld', {
    'jsonld': fields.Nested(dict_model)})
genes_model = api.model('Genes', {'genes': fields.List(fields.String)})

# Store the arguments by type
int_args = ['poolsize', 'size_cutoff']
float_args = ['score_threshold', 'belief_cutoff']
boolean_args = [
    'do_rename', 'use_adeft', 'do_methionine_offset', 'do_orthology_mapping',
    'do_isoform_mapping', 'use_cache', 'return_toplevel', 'flatten_evidence',
    'normalize_equivalences', 'normalize_opposites', 'invert', 'remove_bound',
    'specific_only', 'allow_families', 'match_suffix', 'update_belief']
list_args = [
    'gene_list', 'name_list', 'values', 'source_apis', 'uuids', 'curations',
    'correct_tags', 'ignores', 'deletions']
dict_args = [
    'grounding_map', 'misgrounding_map', 'whitelist', 'mutations']


def _return_stmts(stmts):
    if stmts:
        stmts_json = stmts_to_json(stmts)
        res = {'statements': stmts_json}
    else:
        res = {'statements': []}
    return res


def _stmts_from_proc(proc):
    if proc and proc.statements:
        stmts = stmts_to_json(proc.statements)
        res = {'statements': stmts}
    else:
        res = {'statements': []}
    return res


# Create Resources in Preassembly Namespace

# Manually add preassembly resources not based on assembly corpus functions
pipeline_model = api.inherit('Pipeline', stmts_model, {
    'pipeline': fields.List(fields.Nested(dict_model))
})


@preassembly_ns.expect(pipeline_model)
@preassembly_ns.route('/pipeline')
class RunPipeline(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """Run an assembly pipeline for a list of Statements."""
        args = request.json
        stmts = stmts_from_json(args.get('statements'))
        pipeline_steps = args.get('pipeline')
        ap = AssemblyPipeline(pipeline_steps)
        stmts_out = ap.run(stmts)
        return _return_stmts(stmts_out)


@preassembly_ns.expect(stmts_model)
@preassembly_ns.route('/map_ontologies')
class MapOntologies(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """Run ontology mapping on a list of INDRA Statements."""
        args = request.json
        stmts = stmts_from_json(args.get('statements'))
        om = OntologyMapper(stmts, wm_ontomap, scored=True, symmetric=False)
        om.map_statements()
        return _return_stmts(stmts)


# Dynamically generate resources for assembly corpus functions
class PreassembleStatements(Resource):
    """Parent Resource for Preassembly resources."""
    func_name = None

    def process_args(self, args_json):
        for arg in args_json:
            if arg == 'stmt_type':
                args_json[arg] = get_statement_by_name(args_json[arg])
            elif arg in ['matches_fun', 'refinement_fun']:
                args_json[arg] = pipeline_functions[args_json[arg]]
            elif arg == 'curations':
                Curation = namedtuple(
                    'Curation', ['pa_hash', 'source_hash', 'tag'])
                args_json[arg] = [
                    Curation(cur['pa_hash'], cur['source_hash'], cur['tag'])
                    for cur in args_json[arg]]
            elif arg == 'belief_scorer':
                if args_json[arg] == 'wm':
                    args_json[arg] = get_eidos_scorer()
                else:
                    args_json[arg] = None
            elif arg == 'hierarchies':
                if args_json[arg] == 'wm':
                    args_json[arg] = get_wm_hierarchies()
                else:
                    args_json[arg] = None
            elif arg == 'whitelist' or arg == 'mutations':
                args_json[arg] = {
                    gene: [tuple(mod) for mod in mods]
                    for gene, mods in args_json[arg].items()}
        return args_json

    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        args = self.process_args(request.json)
        stmts = stmts_from_json(args.pop('statements'))
        stmts_out = pipeline_functions[self.func_name](stmts, **args)
        return _return_stmts(stmts_out)


def make_preassembly_model(func):
    """Create new Flask model with function arguments."""
    args = inspect.signature(func).parameters
    # We can reuse Staetments model if only stmts_in or stmts and **kwargs are
    # arguments of the function
    if ((len(args) == 1 and ('stmts_in' in args or 'stmts' in args)) or
            (len(args) == 2 and 'kwargs' in args and
                ('stmts_in' in args or 'stmts' in args))):
        return stmts_model
    # Inherit a model if there are other arguments
    model_fields = {}
    for arg in args:
        if arg != 'stmts_in' and arg != 'stmts' and arg != 'kwargs':
            default = None
            if args[arg].default is not inspect.Parameter.empty:
                default = args[arg].default
            if arg in boolean_args:
                model_fields[arg] = fields.Boolean(default=default)
            elif arg in int_args:
                model_fields[arg] = fields.Integer(default=default)
            elif arg in float_args:
                model_fields[arg] = fields.Float(default=default)
            elif arg in list_args:
                if arg == 'curations':
                    model_fields[arg] = fields.List(fields.Nested(dict_model))
                else:
                    model_fields[arg] = fields.List(
                        fields.String, default=default)
            elif arg in dict_args:
                model_fields[arg] = fields.Nested(dict_model, default=default)
            else:
                model_fields[arg] = fields.String(default=default)
    new_model = api.inherit(
        ('%s_input' % func.__name__), stmts_model, model_fields)
    return new_model


# Create resources for each of assembly_corpus functions
for func_name, func in pipeline_functions.items():
    if func.__module__ == 'indra.tools.assemble_corpus':
        doc = ''
        # Get the function description from docstring
        if func.__doc__:
            doc = func.__doc__.split('\n')[0]

        new_model = make_preassembly_model(func)

        @preassembly_ns.expect(new_model)
        @preassembly_ns.route(('/%s' % func_name), doc={'description': doc})
        class NewFunction(PreassembleStatements):
            func_name = func_name

            def post(self):
                return super().post()

            post.__doc__ = doc


# Create resources for REACH namespace
reach_text_model = api.inherit('ReachText', bio_text_model, {
    'offline': fields.Boolean(default=False),
    'url': fields.String
})
reach_json_model = api.model('ReachJSON', {'json': fields.Nested(dict_model)})
reach_pmc_model = api.model('ReachPMC', {'pmcid': fields.String})


@reach_ns.expect(reach_text_model)
@reach_ns.route('/process_text')
class ReachProcessText(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """Process text with REACH and return INDRA Statements."""
        args = request.json
        text = args.get('text')
        offline = True if args.get('offline') else False
        given_url = args.get('url')
        config_url = get_config('REACH_TEXT_URL', failure_ok=True)
        # Order: URL given as an explicit argument in the request. Then any URL
        # set in the configuration. Then, unless offline is set, use the
        # default REACH web service URL.
        if 'url' in args:  # This is to take None if explicitly given
            url = given_url
        elif config_url:
            url = config_url
        elif not offline:
            url = reach_text_url
        else:
            url = None
        # If a URL is set, prioritize it over the offline setting
        if url:
            offline = False
        rp = reach.process_text(text, offline=offline, url=url)
        return _stmts_from_proc(rp)


@reach_ns.expect(reach_json_model)
@reach_ns.route('/process_json')
class ReachProcessJson(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """Process REACH json and return INDRA Statements."""
        args = request.json
        json_str = args.get('json')
        rp = reach.process_json_str(json_str)
        return _stmts_from_proc(rp)


@reach_ns.expect(reach_pmc_model)
@reach_ns.route('/process_pmc')
class ReachProcessPmc(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """Process PubMedCentral article and return INDRA Statements."""
        args = request.json
        pmcid = args.get('pmcid')
        offline = True if args.get('offline') else False
        given_url = args.get('url')
        config_url = get_config('REACH_NXML_URL', failure_ok=True)
        # Order: URL given as an explicit argument in the request. Then any URL
        # set in the configuration. Then, unless offline is set, use the
        # default REACH web service URL.
        if 'url' in args:  # This is to take None if explicitly given
            url = given_url
        elif config_url:
            url = config_url
        elif not offline:
            url = reach_nxml_url
        else:
            url = None
        # If a URL is set, prioritize it over the offline setting
        if url:
            offline = False
        rp = reach.process_pmc(pmcid, offline=offline, url=url)
        return _stmts_from_proc(rp)


# Create resources for TRIPS namespace
xml_model = api.model('XML', {'xml_str': fields.String})


@trips_ns.expect(bio_text_model)
@trips_ns.route('/process_text')
class TripsProcessText(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """Process text with TRIPS and return INDRA Statements."""
        args = request.json
        text = args.get('text')
        tp = trips.process_text(text)
        return _stmts_from_proc(tp)


@trips_ns.expect(xml_model)
@trips_ns.route('/process_xml')
class TripsProcessText(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """Process TRIPS EKB XML and return INDRA Statements."""
        args = request.json
        xml_str = args.get('xml_str')
        tp = trips.process_xml(xml_str)
        return _stmts_from_proc(tp)


# Create resources for Sofia namespace
text_auth_model = api.inherit('TextAuth', wm_text_model, {
    'auth': fields.List(fields.String, example=['USER', 'PASS'])})


@sofia_ns.expect(text_auth_model)
@sofia_ns.route('/process_text')
class SofiaProcessText(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """Process text with Sofia and return INDRA Statements."""
        args = request.json
        text = args.get('text')
        auth = args.get('auth')
        sp = sofia.process_text(text, auth=auth)
        return _stmts_from_proc(sp)


# Create resources for Eidos namespace
eidos_text_model = api.inherit('EidosText', wm_text_model, {
    'webservice': fields.String,
    'grounding_ns': fields.String
})
eidos_jsonld_model = api.inherit('EidosJsonld', jsonld_model, {
    'grounding_ns': fields.String
})


@eidos_ns.expect(eidos_text_model)
@eidos_ns.route('/process_text')
class EidosProcessText(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """Process text with EIDOS and return INDRA Statements."""
        args = request.json
        text = args.get('text')
        webservice = args.get('webservice')
        grounding_ns = args.get('grounding_ns')
        if not webservice:
            abort(400, 'No web service address provided.')
        ep = eidos.process_text(text, webservice=webservice,
                                grounding_ns=grounding_ns)
        return _stmts_from_proc(ep)


@eidos_ns.expect(eidos_jsonld_model)
@eidos_ns.route('/process_jsonld')
class EidosProcessJsonld(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """Process an EIDOS JSON-LD and return INDRA Statements."""
        args = request.json
        eidos_json = args.get('jsonld')
        grounding_ns = args.get('grounding_ns')
        ep = eidos.process_json_str(eidos_json, grounding_ns=grounding_ns)
        return _stmts_from_proc(ep)


# Create resources for Hume namespace
@hume_ns.expect(jsonld_model)
@hume_ns.route('/process_jsonld')
class HumeProcessJsonld(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """Process Hume JSON-LD and return INDRA Statements."""
        args = request.json
        jsonld_str = args.get('jsonld')
        jsonld = json.loads(jsonld_str)
        hp = hume.process_jsonld(jsonld)
        return _stmts_from_proc(hp)


# Create resources for CWMS namespace
@cwms_ns.expect(wm_text_model)
@cwms_ns.route('/process_text')
class CwmsProcessText(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """Process text with CWMS and return INDRA Statements."""
        args = request.json
        text = args.get('text')
        cp = cwms.process_text(text)
        return _stmts_from_proc(cp)


# Create resources for BEL namespace
bel_rdf_model = api.model('BelRdf', {'belrdf': fields.String})


@bel_ns.expect(genes_model)
@bel_ns.route('/process_pybel_neighborhood')
class BelProcessNeighborhood(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """Process BEL Large Corpus neighborhood and return INDRA Statements."""
        args = request.json
        genes = args.get('genes')
        bp = bel.process_pybel_neighborhood(genes)
        return _stmts_from_proc(bp)


@bel_ns.expect(bel_rdf_model)
@bel_ns.route('/process_belrdf')
class BelProcessBelRdf(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """Process BEL RDF and return INDRA Statements."""
        args = request.json
        belrdf = args.get('belrdf')
        bp = bel.process_belrdf(belrdf)
        return _stmts_from_proc(bp)


# Create resources for BioPax namespace
source_target_model = api.model('SourceTarget', {
    'source': fields.List(fields.String),
    'target': fields.List(fields.String)
})


@biopax_ns.expect(genes_model)
@biopax_ns.route('/process_pc_pathsbetween')
class BiopaxPathsBetween(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """
        Process PathwayCommons paths between genes, return INDRA Statements.
        """
        args = request.json
        genes = args.get('genes')
        bp = biopax.process_pc_pathsbetween(genes)
        return _stmts_from_proc(bp)


@biopax_ns.expect(source_target_model)
@biopax_ns.route('/process_pc_pathsfromto')
class BiopaxPathsFromTo(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """
        Process PathwayCommons paths from-to genes, return INDRA Statements.
        """
        args = request.json
        source = args.get('source')
        target = args.get('target')
        bp = biopax.process_pc_pathsfromto(source, target)
        return _stmts_from_proc(bp)


@biopax_ns.expect(genes_model)
@biopax_ns.route('/process_pc_neighborhood')
class BiopaxNeighborhood(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """Process PathwayCommons neighborhood, return INDRA Statements."""
        args = request.json
        genes = args.get('genes')
        bp = biopax.process_pc_neighborhood(genes)
        return _stmts_from_proc(bp)


# Create resources for Assemblers namespace
pysb_stmts_model = api.inherit('PysbStatements', stmts_model, {
    'export_format': fields.String
})


@assemblers_ns.expect(pysb_stmts_model)
@assemblers_ns.route('/pysb')
class AssemblePysb(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """Assemble INDRA Statements and return PySB model string."""
        args = request.json
        stmts_json = args.get('statements')
        export_format = args.get('export_format')
        stmts = stmts_from_json(stmts_json)
        pa = PysbAssembler()
        pa.add_statements(stmts)
        pa.make_model()
        try:
            for m in pa.model.monomers:
                pysb_assembler.set_extended_initial_condition(pa.model, m, 0)
        except Exception as e:
            logger.exception(e)

        if not export_format:
            model_str = pa.print_model()
        elif export_format in ('kappa_im', 'kappa_cm'):
            fname = 'model_%s.png' % export_format
            root = os.path.dirname(os.path.abspath(fname))
            graph = pa.export_model(format=export_format, file_name=fname)
            with open(fname, 'rb') as fh:
                data = 'data:image/png;base64,%s' % \
                    base64.b64encode(fh.read()).decode()
                return {'image': data}
        else:
            try:
                model_str = pa.export_model(format=export_format)
            except Exception as e:
                logger.exception(e)
                model_str = ''
        res = {'model': model_str}
        return res


@assemblers_ns.expect(stmts_model)
@assemblers_ns.route('/cx')
class AssembleCx(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """Assemble INDRA Statements and return CX network json."""
        args = request.json
        stmts_json = args.get('statements')
        stmts = stmts_from_json(stmts_json)
        ca = CxAssembler(stmts)
        model_str = ca.make_model()
        res = {'model': model_str}
        return res


@assemblers_ns.expect(stmts_model)
@assemblers_ns.route('/graph')
class AssembleGraph(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """Assemble INDRA Statements and return Graphviz graph dot string."""
        args = request.json
        stmts_json = args.get('statements')
        stmts = stmts_from_json(stmts_json)
        ga = GraphAssembler(stmts)
        model_str = ga.make_model()
        res = {'model': model_str}
        return res


@assemblers_ns.expect(stmts_model)
@assemblers_ns.route('/cyjs')
class AssembleCyjs(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """Assemble INDRA Statements and return Cytoscape JS network."""
        args = request.json
        stmts_json = args.get('statements')
        stmts = stmts_from_json(stmts_json)
        cja = CyJSAssembler(stmts)
        cja.make_model(grouping=True)
        model_str = cja.print_cyjs_graph()
        return json.loads(model_str)


@assemblers_ns.expect(stmts_model)
@assemblers_ns.route('/english')
class AssembleEnglish(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """Assemble each statement into English sentence."""
        args = request.json
        stmts_json = args.get('statements')
        stmts = stmts_from_json(stmts_json)
        sentences = {}
        for st in stmts:
            enga = EnglishAssembler()
            enga.add_statements([st])
            model_str = enga.make_model()
            sentences[st.uuid] = model_str
        res = {'sentences': sentences}
        return res


@assemblers_ns.expect(stmts_model)
@assemblers_ns.route('/sif/loopy')
class AssembleLoopy(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """Assemble INDRA Statements into a Loopy model using SIF Assembler."""
        args = request.json
        stmts_json = args.get('statements')
        stmts = stmts_from_json(stmts_json)
        sa = SifAssembler(stmts)
        sa.make_model(use_name_as_key=True)
        model_str = sa.print_loopy(as_url=True)
        res = {'loopy_url': model_str}
        return res


# Create resources for NDEx namespace
network_model = api.model('Network', {'network_id': fields.String})


@ndex_ns.expect(stmts_model)
@ndex_ns.route('/share_model_ndex')
class ShareModelNdex(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """Upload the model to NDEX"""
        args = request.json
        stmts_json = args.get('statements')
        stmts = stmts_from_json(stmts_json)
        ca = CxAssembler(stmts)
        for n, v in args.items():
            ca.cx['networkAttributes'].append({'n': n, 'v': v, 'd': 'string'})
        ca.make_model()
        network_id = ca.upload_model(private=False)
        return {'network_id': network_id}


@ndex_ns.expect(network_model)
@ndex_ns.route('/fetch_model_ndex')
class FetchModelNdex(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """Download model and associated pieces from NDEX"""
        args = request.json
        network_id = args.get('network_id')
        cx = process_ndex_network(network_id)
        network_attr = [x for x in cx.cx if x.get('networkAttributes')]
        network_attr = network_attr[0]['networkAttributes']
        keep_keys = ['txt_input', 'parser',
                     'model_elements', 'preset_pos', 'stmts',
                     'sentences', 'evidence', 'cell_line', 'mrna', 'mutations']
        stored_data = {}
        for d in network_attr:
            if d['n'] in keep_keys:
                stored_data[d['n']] = d['v']
        return stored_data


# Create resources for INDRA DB REST namespace
stmt_model = api.model('Statement', {'statement': fields.Nested(dict_model)})


@indra_db_rest_ns.expect(stmt_model)
@indra_db_rest_ns.route('/get_evidence')
class GetEvidence(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """Get all evidence for a given INDRA statement."""
        args = request.json
        stmt_json = args.get('statement')
        stmt = Statement._from_json(stmt_json)

        def _get_agent_ref(agent):
            """Get the preferred ref for an agent for db web api."""
            if agent is None:
                return None
            ag_hgnc_id = hgnc_client.get_hgnc_id(agent.name)
            if ag_hgnc_id is not None:
                return ag_hgnc_id + "@HGNC"
            db_refs = agent.db_refs
            for namespace in ['HGNC', 'FPLX', 'CHEBI', 'TEXT']:
                if namespace in db_refs.keys():
                    return '%s@%s' % (db_refs[namespace], namespace)
            return '%s@%s' % (agent.name, 'TEXT')

        def _get_matching_stmts(stmt_ref):
            # Filter by statement type.
            stmt_type = stmt_ref.__class__.__name__
            agent_name_list = [
                _get_agent_ref(ag) for ag in stmt_ref.agent_list()]
            non_binary_statements = (Complex, SelfModification, ActiveForm)
            # TODO: We should look at more than just the agent name.
            # Doing so efficiently may require changes to the web api.
            if isinstance(stmt_ref, non_binary_statements):
                agent_list = [ag_name for ag_name in agent_name_list
                              if ag_name is not None]
                kwargs = {}
            else:
                agent_list = []
                kwargs = {k: v for k, v in zip(['subject', 'object'],
                                               agent_name_list)}
                if not any(kwargs.values()):
                    return []
                print(agent_list)
            stmts = get_statements(agents=agent_list, stmt_type=stmt_type,
                                   simple_response=True, **kwargs)
            return stmts

        stmts_out = _get_matching_stmts(stmt)
        agent_name_list = [ag.name for ag in stmt.agent_list()]
        stmts_out = stmts = ac.filter_concept_names(
            stmts_out, agent_name_list, 'all')
        return _return_stmts(stmts_out)


# Create resources for Databases namespace
cbio_model = api.model('Cbio', {
    'gene_list': fields.List(fields.String),
    'cell_lines': fields.List(fields.String)
})


@databases_ns.expect(cbio_model)
@databases_ns.route('/cbio/get_ccle_mrna')
class CbioMrna(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """Get CCLE mRNA amounts using cBioClient"""
        args = request.json
        gene_list = args.get('gene_list')
        cell_lines = args.get('cell_lines')
        mrna_amounts = cbio_client.get_ccle_mrna(gene_list, cell_lines)
        res = {'mrna_amounts': mrna_amounts}
        return res


@databases_ns.expect(cbio_model)
@databases_ns.route('/cbio/get_ccle_cna')
class CbioCna(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """Get CCLE CNA
        -2 = homozygous deletion
        -1 = hemizygous deletion
        0 = neutral / no change
        1 = gain
        2 = high level amplification
        """
        args = request.json
        gene_list = args.get('gene_list')
        cell_lines = args.get('cell_lines')
        mrna_amounts = cbio_client.get_ccle_cna(gene_list, cell_lines)
        res = {'cna': cna}
        return res


@databases_ns.expect(cbio_model)
@databases_ns.route('/cbio/get_ccle_mutations')
class CbioMutations(Resource):
    @api.doc(False)
    def options(self):
        return {}

    def post(self):
        """Get CCLE mutations
        returns the amino acid changes for a given list of genes and cell lines
        """
        args = request.json
        gene_list = args.get('gene_list')
        cell_lines = args.get('cell_lines')
        mrna_amounts = cbio_client.get_ccle_mutations(gene_list, cell_lines)
        res = {'mutations': mutations}
        return res


if __name__ == '__main__':
    argparser = argparse.ArgumentParser('Run the INDRA REST API')
    argparser.add_argument('--host', default='0.0.0.0')
    argparser.add_argument('--port', default=8081, type=int)
    argparserargs = argparser.parse_args()
    app.run(host=argparserargs.host, port=argparserargs.port)
