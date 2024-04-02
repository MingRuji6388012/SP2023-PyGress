"""tests the code found in the documentation

Any code changed in here needs to be updated in their place in the
documentation and vice versa, since we are copy pasting code between its
occurence to the tests.

In general, try to separate tests one test per chunk of code that is
interdependent.
"""
from .test_live_curation import _make_corpus

corpus = _make_corpus()


def _get_gene_network_stmts():
    from indra.tools.gene_network import GeneNetwork
    gn = GeneNetwork(['BRCA1'])
    return gn.get_statements()


gn_stmts = _get_gene_network_stmts()

wm_raw_stmts = corpus.raw_statements
wm_stmts = corpus.statements


# CODE IN README.md #

# From stmt assembly pipeline description in README.md
def test_readme_pipeline():
    stmts = gn_stmts  # Added only here, not in docs
    from indra.tools import assemble_corpus as ac
    stmts = ac.filter_no_hypothesis(stmts)
    stmts = ac.map_grounding(stmts)
    stmts = ac.filter_grounded_only(stmts)
    stmts = ac.filter_human_only(stmts)
    stmts = ac.map_sequence(stmts)
    stmts = ac.run_preassembly(stmts, return_toplevel=False)
    stmts = ac.filter_belief(stmts, 0.8)
    assert stmts, 'Update example to yield statements list of non-zero length'


# From description of wm stmt assembly pipeline in README.md
def test_readme_wm_pipeline():
    from indra.tools import assemble_corpus as ac
    from indra.belief.wm_scorer import get_eidos_scorer
    from indra.preassembler.hierarchy_manager import get_wm_hierarchies
    stmts = wm_raw_stmts
    stmts = ac.filter_grounded_only(stmts)
    hierarchies = get_wm_hierarchies()
    belief_scorer = get_eidos_scorer()
    stmts = ac.run_preassembly(stmts,
                               return_toplevel=False,
                               belief_scorer=belief_scorer,
                               hierarchies=hierarchies,
                               normalize_opposites=True,
                               normalize_ns='WM')
    stmts = ac.filter_belief(stmts, 0.8)    # Apply belief cutoff of e.g., 0.8
    # assert stmts, 'Update example to yield statements list of non-zero
    # length'


# From 1st example under "Using INDRA"
def test_readme_using_indra1():
    from indra.sources import trips
    from indra.assemblers.pysb import PysbAssembler
    pa = PysbAssembler()
    # Process a natural language description of a mechanism
    trips_processor = trips.process_text(
        'MEK2 phosphorylates ERK1 at Thr-202 and Tyr-204')
    # Collect extracted mechanisms in PysbAssembler
    pa.add_statements(trips_processor.statements)
    # Assemble the model
    model = pa.make_model(policies='two_step')


# From 2nd example under "Using INDRA"
def test_readme_using_indra2():
    from indra.sources import reach
    # Process the neighborhood of BRAF and MAP2K1
    reach_processor = reach.process_pmc('3717945')


# From 3rd example under "Using INDRA"
def test_readme_using_indra3():
    from indra.sources import reach
    from indra.literature import pubmed_client
    # Search for 10 most recent abstracts in PubMed on 'BRAF'
    pmids = pubmed_client.get_ids('BRAF', retmax=10)
    all_statements = []
    for pmid in pmids:
        abs = pubmed_client.get_abstract(pmid)
        if abs is not None:
            reach_processor = reach.process_text(abs)
            if reach_processor is not None:
                all_statements += reach_processor.statements


# From 4th example under "Using INDRA"
def test_readme_using_indra4():
    from indra.sources import bel
    # Process the neighborhood of BRAF and MAP2K1
    bel_processor = bel.process_pybel_neighborhood(['BRAF', 'MAP2K1'])


# From 5th example under "Using INDRA"
def test_readme_using_indra5():
    from indra.sources import biopax
    # Process the neighborhood of BRAF and MAP2K1
    biopax_processor = biopax.process_pc_pathsfromto(['BRAF', 'RAF1'],
                                                     ['MAP2K1', 'MAP2K2'])


# CODE IN nl_modeling.rst #
def test_nl_modeling():
    # 1 code chunk
    from indra.sources import trips
    model_text = 'MAP2K1 phosphorylates MAPK1 and DUSP6 dephosphorylates MAPK1.'
    tp = trips.process_text(model_text)

    # 2nd code chunk
    for st in tp.statements:
        assert st.evidence[0].text  # Replaces a print statement in the doc

    # 3rd code chunk
    from indra.assemblers.pysb import PysbAssembler
    pa = PysbAssembler()
    pa.add_statements(tp.statements)
    pa.make_model(policies='two_step')

    # 4th code chunk
    for monomer in pa.model.monomers:
        assert monomer  # This replaces a print statements in the doc

    # 5th code chunk
    for rule in pa.model.rules:
        assert rule  # This replaces a print statements in the doc

    # 6th code chunk
    for parameter in pa.model.parameters:
        assert parameter  # This replaces a print statements in the doc

    # 7th code chunk
    for annotation in pa.model.annotations:
        assert annotation  # This replaces a print statements in the doc

    # 8th code chunk (this code is currently in a commented out section)
    pa.set_context('A375_SKIN')
    for monomer_pattern, parameter in pa.model.initial_conditions:
        assert monomer_pattern
        assert parameter.value

    # 9th code chunk
    _ = pa.export_model('sbml')
    assert _
    _ = pa.export_model('bngl')
    assert _

    # 10th code chunk
    # pa.export_model('sbml', 'example_model.sbml')  # Don't save file


# CODE IN gene_network.rst
def test_gene_network():
    # Chunk 1: this is tested in _get_gene_network_stmts
    # from indra.tools.gene_network import GeneNetwork
    # gn = GeneNetwork(['BRCA1'])
    # biopax_stmts = gn.get_biopax_stmts()
    # bel_stmts = gn.get_bel_stmts()

    # Chunk 2
    from indra import literature
    pmids = literature.pubmed_client.get_ids_for_gene('BRCA1')

    # Chunk 3
    from indra import literature
    paper_contents = {}
    for pmid in pmids:
        content, content_type = literature.get_full_text(pmid, 'pmid')
        if content_type == 'abstract':
            paper_contents[pmid] = content
        if len(paper_contents) == 10:
            break

    # Chunk 4
    import requests
    from indra import literature
    from indra.sources import reach
    from indra.statements import stmts_from_json
    indra_api = 'http://api.indra.bio:8000/reach/process_text'

    # Chunk 5
    literature_stmts = []
    for pmid, content in paper_contents.items():
        res = requests.post(url=indra_api, json={'text': content})

        if res.status_code == 200:
            print('Got %d statements from abstract for pmid %s' %
                (len(res.json()['statements']), pmid))
            literature_stmts += stmts_from_json(res.json()['statements'])
        else:
            print('Got status code %d for pmid %s.' % (res.status_code, pmid))
    assert literature_stmts  # replaces a print statements

    # Chunk 6
    from indra.tools import assemble_corpus
    # stmts = biopax_stmts + bel_stmts + literature_stmts  # tested elsewhere
    stmts = gn_stmts + literature_stmts
    stmts = assemble_corpus.map_grounding(stmts)
    stmts = assemble_corpus.map_sequence(stmts)
    stmts = assemble_corpus.run_preassembly(stmts)

    # Chunk 7
    from indra.assemblers.cx import CxAssembler
    from indra.databases import ndex_client
    cxa = CxAssembler(stmts)
    cx_str = cxa.make_model()
    assert cx_str  # Added to check output

    # Chunk 8
    # ndex_cred = {'user': 'myusername', 'password': 'xxx'}
    # network_id = ndex_client.create_network(cx_str, ndex_cred)
    # print(network_id)

    # Chunk 9
    from indra.assemblers.indranet import IndraNetAssembler
    indranet_assembler = IndraNetAssembler(statements=stmts)
    indranet = indranet_assembler.make_model()

    # Chunk 10
    import networkx as nx
    paths = nx.single_source_shortest_path(G=indranet, source='BRCA1',
                                           cutoff=1)
    assert paths

    # Chunk 11
    from indra.assemblers.pysb import PysbAssembler
    pysb = PysbAssembler(statements=stmts)
    pysb_model = pysb.make_model()
