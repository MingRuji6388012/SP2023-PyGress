import pickle
from indra.statements import *
from pysb import *
from pysb.core import SelfExporter
from pysb.tools import render_reactions
from indra.tools.model_checker import ModelChecker, mp_embeds_into, \
                                      cp_embeds_into, match_lhs, match_rhs, \
                                      positive_path
from indra.assemblers.pysb_assembler import PysbAssembler
from pysb.tools import species_graph
from pysb.bng import generate_equations
from pysb import kappa
from pysb.testing import with_model
import pygraphviz as pgv

@with_model
def test_mp_embedding():
    # Create a PySB model
    Monomer('A', ['b', 'other'], {'other':['u','p']})
    mp1 = A(other='u')
    mp2 = A()
    mp3 = A(other='p')
    assert mp_embeds_into(mp1, mp2)
    assert not mp_embeds_into(mp2, mp1)
    assert mp_embeds_into(mp3, mp2)
    assert not mp_embeds_into(mp2, mp3)
    assert not mp_embeds_into(mp3, mp1)
    assert not mp_embeds_into(mp1, mp3)

@with_model
def test_cp_embedding():
    Monomer('A', ['b', 'other'], {'other':['u','p']})
    Monomer('B', ['b'])
    cp1 = A(b=1, other='p') % B(b=1)
    cp2 = A()
    cp3 = A(b=1, other='u') % B(b=1)
    cp4 = A(other='p')
    cp5 = A(b=1) % B(b=1)
    # FIXME Some tests not performed because ComplexPatterns for second term
    # FIXME are not yet supported
    assert cp_embeds_into(cp1, cp2)
    #assert not cp_embeds_into(cp1, cp3)
    assert cp_embeds_into(cp1, cp4)
    #assert not cp_embeds_into(cp1, cp5)
    #assert not cp_embeds_into(cp2, cp1)
    #assert not cp_embeds_into(cp2, cp3)
    assert not cp_embeds_into(cp2, cp4)
    #assert not cp_embeds_into(cp2, cp5)
    #assert not cp_embeds_into(cp3, cp1)
    assert cp_embeds_into(cp3, cp2)
    assert not cp_embeds_into(cp3, cp4)
    #assert cp_embeds_into(cp3, cp5)
    #assert not cp_embeds_into(cp4, cp1)
    assert cp_embeds_into(cp4, cp2)
    #assert not cp_embeds_into(cp4, cp3)
    #assert not cp_embeds_into(cp4, cp5)
    #assert not cp_embeds_into(cp5, cp1)
    assert cp_embeds_into(cp5, cp2)
    #assert not cp_embeds_into(cp5, cp3)
    assert not cp_embeds_into(cp5, cp4)

@with_model
def test_match_lhs():
    Monomer('A', ['other'], {'other':['u', 'p']})
    Monomer('B', ['T185'], {'T185':['u', 'p']})
    rule = Rule('A_phos_B', A() + B(T185='u') >> A() + B(T185='p'),
                Parameter('k', 1))
    matching_rules = match_lhs(A(), model.rules)
    assert len(matching_rules) == 1
    assert matching_rules[0] == rule
    matching_rules = match_lhs(A(other='u'), model.rules)
    assert len(matching_rules) == 0

@with_model
def test_match_rhs():
    Monomer('A', ['other'], {'other':['u', 'p']})
    Monomer('B', ['T185'], {'T185':['u', 'p']})
    rule = Rule('A_phos_B', A() + B(T185='u') >> A() + B(T185='p'),
                Parameter('k', 1))
    matching_rules = match_rhs(B(T185='p'), model.rules)
    assert len(matching_rules) == 1
    assert matching_rules[0] == rule
    matching_rules = match_rhs(B(T185='u'), model.rules)
    assert len(matching_rules) == 0
    matching_rules = match_rhs(B(), model.rules)
    assert len(matching_rules) == 1
    assert matching_rules[0] == rule

@with_model
def test_one_step_phosphorylation():
    # Create the statement
    a = Agent('A', db_refs={'HGNC':'1'})
    b = Agent('B', db_refs={'HGNC':'2'})
    st = Phosphorylation(a, b, 'T', '185')
    # Now create the PySB model
    Monomer('A')
    Monomer('B', ['T185'], {'T185':['u', 'p']})
    Rule('A_phos_B', A() + B(T185='u') >> A() + B(T185='p'),
         Parameter('k', 1))
    Initial(A(), Parameter('A_0', 100))
    Initial(B(T185='u'), Parameter('B_0', 100))
    # Add annotations
    Annotation(A, 'http://identifiers.org/hgnc/HGNC:1')
    Annotation(B, 'http://identifiers.org/hgnc/HGNC:2')
    B.site_annotations = [
        Annotation(('T185', 'p'), 'phosphorylation', 'is_modification'),
        Annotation('T185', 'T', 'is_residue'),
        Annotation('T185', '185', 'is_position'),
    ]
    mc = ModelChecker(model, [st])
    results = mc.check_model()
    assert len(results) == 1
    assert isinstance(results[0], tuple)
    assert results[0][0] == st
    assert results[0][1] == True

@with_model
def test_two_step_phosphorylation():
    # Create the statement
    a = Agent('A', db_refs={'HGNC':'1'})
    b = Agent('B', db_refs={'HGNC':'2'})
    st = Phosphorylation(a, b, 'T', '185')
    # Now create the PySB model
    Monomer('A', ['b', 'other'], {'other':['u','p']})
    Monomer('B', ['b', 'T185'], {'T185':['u', 'p']})
    Rule('A_bind_B', A(b=None) + B(b=None, T185='u') >>
                     A(b=1) % B(b=1, T185='u'), Parameter('kf', 1))
    Rule('A_bind_B_rev', A(b=1) % B(b=1, T185='u') >>
                         A(b=None) + B(b=None, T185='u'), Parameter('kr', 1))
    Rule('A_phos_B', A(b=1) % B(b=1, T185='u') >>
                     A(b=None) + B(b=None, T185='p'),
                 Parameter('kcat', 1))
    Initial(A(b=None, other='p'), Parameter('Ap_0', 100))
    Initial(A(b=None, other='u'), Parameter('Au_0', 100))
    Initial(B(b=None, T185='u'), Parameter('B_0', 100))
    # Add annotations
    Annotation(A, 'http://identifiers.org/hgnc/HGNC:1')
    Annotation(B, 'http://identifiers.org/hgnc/HGNC:2')
    B.site_annotations = [
        Annotation(('T185', 'p'), 'phosphorylation', 'is_modification'),
        Annotation('T185', 'T', 'is_residue'),
        Annotation('T185', '185', 'is_position'),
    ]
    #with open('model_rxn.dot', 'w') as f:
    #    f.write(render_reactions.run(model))
    #with open('species_2step.dot', 'w') as f:
    #    f.write(species_graph.run(model))
    #im = kappa.influence_map(model)
    #im.draw('im_2step.pdf', prog='dot')
    #generate_equations(model)
    # Now check the model
    mc = ModelChecker(model, [st])
    results = mc.check_model()
    assert len(results) == 1
    assert isinstance(results[0], tuple)
    assert results[0][0] == st
    assert results[0][1] == True

def test_pysb_assembler_phospho_policies():
    a = Agent('A', db_refs={'HGNC': '1'})
    b = Agent('B', db_refs={'HGNC': '2'})
    st = Phosphorylation(a, b, 'T', '185')
    pa = PysbAssembler()
    pa.add_statements([st])
    # Try two step
    pa.make_model(policies='two_step')
    mc = ModelChecker(pa.model, [st])
    results = mc.check_model()
    assert len(results) == 1
    assert isinstance(results[0], tuple)
    assert results[0][0] == st
    assert results[0][1] == True
    # Try one step
    pa.make_model(policies='one_step')
    mc = ModelChecker(pa.model, [st])
    results = mc.check_model()
    assert len(results) == 1
    assert isinstance(results[0], tuple)
    assert results[0][0] == st
    assert results[0][1] == True
    # Try interactions_only
    pa.make_model(policies='interactions_only')
    mc = ModelChecker(pa.model, [st])
    results = mc.check_model()
    assert len(results) == 1
    assert isinstance(results[0], tuple)
    assert results[0][0] == st
    assert results[0][1] == False

"""
def test_ras_220_network():
    ras_220_results_path = os.path.join('../../models/ras_220_genes'
                                        '/ras_220_gn_related2_stmts.pkl')
    #ras_220_results_path = 'braf_dusp6_stmts.pkl'
    #ras_220_results_path = 'braf_dusp6_small.pkl'
    with open(ras_220_results_path, 'rb') as f:
        ras220_stmts = pickle.load(f)
    ras220_stmts = [s for s in ras220_stmts
                      if isinstance(s, Modification) or
                         isinstance(s, ActiveForm)]
    print("Done loading")
    # Build a PySB model from the Ras 220 statements
    pa = PysbAssembler()
    pa.add_statements(ras220_stmts)
    pa.make_model(policies='one_step')
    # Now create an indirect statement to check the model against
    egfr = Agent('EGFR')
    braf = Agent('BRAF')
    dusp6 = Agent('DUSP6')
    stmt1 = Phosphorylation(braf, dusp6, 'S', '159')
    stmt2 = Phosphorylation(egfr, dusp6, 'S', '159')
    # Check model
    stmts = [stmt1, stmt2]
    mc = ModelChecker(pa.model, stmts)
    checks = mc.check_model()
    assert len(checks) == 2
    assert isinstance(checks[0], tuple)
    assert checks[0][0] == stmt1
    assert checks[0][1] == True
    assert checks[1][0] == stmt2
    assert checks[1][1] == False
    # Now try again, with a two_step policy
    # Skip this, building the influence map takes a very long time
    #pa.make_model(policies='two_step')
    #mc = ModelChecker(pa.model, [stmt1, stmt2])
    #checks = mc.check_model()
    #print checks
    #assert len(checks) == 2
    #assert isinstance(checks[0], tuple)
    #assert checks[0][0] == stmt1
    #assert checks[0][1] == True
    #assert checks[1][0] == stmt2
    #assert checks[1][1] == False
    # Now with an interactions_only policy
    pa.make_model(policies='interactions_only')
    mc = ModelChecker(pa.model, [stmt1, stmt2])
    checks = mc.check_model()
    assert len(checks) == 2
    assert isinstance(checks[0], tuple)
    assert checks[0][0] == stmt1
    assert checks[0][1] == False
    assert checks[1][0] == stmt2
    assert checks[1][1] == False
"""

def test_path_polarity():
    im = pgv.AGraph('im_polarity.dot')
    path1 = ['BRAF_phospho_MAPK1_T185_1', 'MAPK1_phospho_DUSP6_S159_1']
    path2 = ['BRAF_phospho_MAPK1_T185_1', 'BRAF_phospho_MAPK1_T185_3',
             'MAPK1_phospho_DUSP6_S159_1']
    assert positive_path(im, path1)
    assert not positive_path(im, path2)

@with_model
def test_consumption_rule():
    pvd = Agent('Pervanadate', db_refs={'HGNC': '1'})
    erk = Agent('MAPK1', db_refs={'HGNC': '2'})
    stmt = Phosphorylation(pvd, erk, 'T', '185')
    # Now make the model
    Monomer('Pervanadate', ['b'])
    Monomer('DUSP', ['b'])
    Monomer('MAPK1', ['b', 'T185'], {'T185': ['u', 'p']})
    Rule('Pvd_binds_DUSP',
         Pervanadate(b=None) + DUSP(b=None) >>
         Pervanadate(b=1) % DUSP(b=1),
         Parameter('k1', 1))
    Rule('Pvd_binds_DUSP_rev',
         Pervanadate(b=1) % DUSP(b=1) >>
         Pervanadate(b=None) + DUSP(b=None),
         Parameter('k2', 1))
    Rule('DUSP_binds_MAPK1_phosT185',
         DUSP(b=None) + MAPK1(b=None, T185='p') >>
         DUSP(b=1) % MAPK1(b=1, T185='p'),
         Parameter('k3', 1))
    Rule('DUSP_binds_MAPK1_phosT185_rev',
         DUSP(b=1) % MAPK1(b=1, T185='p') >>
         DUSP(b=None) + MAPK1(b=None, T185='p'),
         Parameter('k4', 1))
    Rule('DUSP_dephos_MAPK1_at_T185',
         DUSP(b=1) % MAPK1(b=1, T185='p') >>
         DUSP(b=None) % MAPK1(b=None, T185='u'),
         Parameter('k5', 1))
    Annotation(Pervanadate, 'http://identifiers.org/hgnc/HGNC:1')
    Annotation(MAPK1, 'http://identifiers.org/hgnc/HGNC:2')
    MAPK1.site_annotations = [
            Annotation(('T185', 'p'), 'phosphorylation', 'is_modification'),
            Annotation('T185', 'T', 'is_residue'),
            Annotation('T185', '185', 'is_position'),
        ]
    # Now check the model against the statement
    mc = ModelChecker(model, [stmt])
    checks = mc.check_model()
    assert len(checks) == 1
    assert isinstance(checks[0], tuple)
    assert checks[0][0] == stmt
    assert checks[0][1] == True

def test_dephosphorylation():
    dusp = Agent('DUSP6', db_refs={'HGNC':'1'})
    mapk1 = Agent('MAPK1', db_refs={'HGNC':'2'})
    stmt = Dephosphorylation(dusp, mapk1, 'T', '185')
    def check_policy(policy, result):
        pysba = PysbAssembler()
        pysba.add_statements([stmt])
        pysba.make_model(policies=policy)
        mc = ModelChecker(pysba.model, [stmt])
        checks = mc.check_model()
        #im = mc.get_im()
        #im.draw('test_dephosphorylation.pdf', prog='dot')
        assert len(checks) == 1
        assert isinstance(checks[0], tuple)
        assert checks[0][0] == stmt
        assert checks[0][1] == result
    check_policy('one_step', True)
    check_policy('two_step', True)
    check_policy('interactions_only', False)

@with_model
def test_invalid_modification():
     # Override the shutoff of self export in psyb_assembler
     # Create the statement
     a = Agent('A')
     b = Agent('B')
     st = Phosphorylation(a, b, 'T', '185')
     # Now create the PySB model
     Monomer('A')
     Monomer('B', ['Y187'], {'Y187':['u', 'p']})
     Rule('A_phos_B', A() + B(Y187='u') >> A() + B(Y187='p'),
          Parameter('k', 1))
     #Initial(A(), Parameter('A_0', 100))
     #Initial(B(T187='u'), Parameter('B_0', 100))
     #with open('model_rxn.dot', 'w') as f:
     #    f.write(render_reactions.run(model))
     #with open('species_1step.dot', 'w') as f:
     #    f.write(species_graph.run(model))
     # Now check the model
     mc = ModelChecker(model, [st])
     results = mc.check_model()
     #assert len(results) == 1
     #assert isinstance(results[0], tuple)
     #assert results[0][0] == st
     #assert results[0][1] == True

def _path_polarity_stmt_list():
    a = Agent('A', db_refs={'HGNC': '1'})
    b = Agent('B', db_refs={'HGNC': '2'})
    c = Agent('C', db_refs={'HGNC': '3'})
    st1 = Phosphorylation(a, c, 'T', '185')
    st2 = Dephosphorylation(a, c, 'T', '185')
    st3 = Phosphorylation(None, c, 'T', '185')
    st4 = Dephosphorylation(None, c, 'T', '185')

    return [st1, st2, st3, st4]

@with_model
def test_distinguish_path_polarity1():
    """Test the ability to distinguish a positive from a negative regulation."""
    Monomer('A')
    Monomer('B', ['act'], {'act' :['y', 'n']})
    Monomer('C', ['T185'], {'T185':['u', 'p']})
    Parameter('k', 1)
    Rule('A_activate_B', A() + B(act='n') >> A() + B(act='y'), k)
    Rule('B_dephos_C', B(act='y') + C(T185='p') >>
                       B(act='y') + C(T185='u'), k)
    Initial(A(), k)
    Initial(B(act='y'), k)
    Initial(C(T185='p'), k)
    Annotation(A, 'http://identifiers.org/hgnc/HGNC:1')
    Annotation(B, 'http://identifiers.org/hgnc/HGNC:2')
    Annotation(C, 'http://identifiers.org/hgnc/HGNC:3')
    C.site_annotations = [
            Annotation(('T185', 'p'), 'phosphorylation', 'is_modification'),
            Annotation('T185', 'T', 'is_residue'),
            Annotation('T185', '185', 'is_position'),
        ]
    # Create the model checker
    stmts = _path_polarity_stmt_list()
    mc = ModelChecker(model, stmts)
    results = mc.check_model()
    im = mc.get_im()
    im.draw('dist_pp_im1.pdf', prog='dot')
    assert len(results) ==  len(stmts)
    assert isinstance(results[0], tuple)
    assert results[0][1] == False
    assert results[1][1] == True
    assert results[2][1] == False
    assert results[3][1] == True

@with_model
def test_distinguish_path_polarity2():
    """Test the ability to distinguish a positive from a negative regulation."""
    Monomer('A')
    Monomer('B', ['act'], {'act' :['y', 'n']})
    Monomer('C', ['T185'], {'T185':['u', 'p']})
    Parameter('k', 1)
    Rule('A_inhibit_B', A() + B(act='y') >> A() + B(act='n'), k)
    Rule('B_dephos_C', B(act='y') + C(T185='p') >>
                       B(act='y') + C(T185='u'), k)
    Initial(A(), k)
    Initial(B(act='y'), k)
    Initial(C(T185='p'), k)
    Annotation(A, 'http://identifiers.org/hgnc/HGNC:1')
    Annotation(B, 'http://identifiers.org/hgnc/HGNC:2')
    Annotation(C, 'http://identifiers.org/hgnc/HGNC:3')
    C.site_annotations = [
            Annotation(('T185', 'p'), 'phosphorylation', 'is_modification'),
            Annotation('T185', 'T', 'is_residue'),
            Annotation('T185', '185', 'is_position'),
        ]
    # Create the model checker
    stmts = _path_polarity_stmt_list()
    mc = ModelChecker(model, stmts)
    results = mc.check_model()
    im = mc.get_im()
    im.draw('dist_pp_im2.pdf', prog='dot')
    assert len(results) ==  len(stmts)
    assert isinstance(results[0], tuple)
    assert results[0][1] == True
    assert results[1][1] == False
    assert results[2][1] == True
    assert results[3][1] == True

@with_model
def test_check_activation():
    a = Agent('A')
    b = Agent('B')
    c = Agent('C')
    st1 = Activation(a, 'activity', b, 'activity', True)
    st2 = Activation(b, 'activity', c, 'kinase', False)
    stmts = [st1, st2]
    # Create the model
    pa = PysbAssembler()
    pa.add_statements(stmts)
    pa.make_model(policies='one_step')
    mc = ModelChecker(pa.model, stmts)
    results = mc.check_model()
    assert len(results) ==  len(stmts)
    assert isinstance(results[0], tuple)
    assert results[0][1] == True
    assert results[1][1] == True

@with_model
def test_none_phosphorylation_stmt():
    # Create the statement
    b = Agent('B', db_refs={'HGNC':'2'})
    st1 = Phosphorylation(None, b, 'T', '185')
    st2 = Phosphorylation(None, b, 'Y', '187')
    stmts = [st1, st2]
    # Now create the PySB model
    Monomer('A')
    Monomer('B', ['T185', 'Y187'], {'T185':['u', 'p'], 'Y187': ['u', 'p']})
    Rule('A_phos_B', A() + B(T185='u') >> A() + B(T185='p'),
         Parameter('k', 1))
    Initial(A(), Parameter('A_0', 100))
    Initial(B(T185='u', Y187='p'), Parameter('B_0', 100))
    Annotation(A, 'http://identifiers.org/hgnc/HGNC:1')
    Annotation(B, 'http://identifiers.org/hgnc/HGNC:2')
    B.site_annotations = [
        Annotation(('T185', 'p'), 'phosphorylation', 'is_modification'),
        Annotation('T185', 'T', 'is_residue'),
        Annotation('T185', '185', 'is_position'),
        Annotation(('Y187', 'p'), 'phosphorylation', 'is_modification'),
        Annotation('Y187', 'Y', 'is_residue'),
        Annotation('Y187', '187', 'is_position'),
    ]
    mc = ModelChecker(model, stmts)
    results = mc.check_model()
    assert len(results) == 2
    assert isinstance(results[0], tuple)
    assert results[0][0] == st1
    assert results[0][1] == True
    assert results[1][0] == st2
    assert results[1][1] == False

@with_model
def test_phosphorylation_annotations():
    # Override the shutoff of self export in psyb_assembler
    # Create the statement
    a = Agent('MEK1', db_refs={'HGNC': '6840'})
    b = Agent('ERK2', db_refs={'HGNC': '6871'})
    st1 = Phosphorylation(a, b, 'T', '185')
    st2 = Phosphorylation(a, b, None, None)
    st3 = Phosphorylation(a, b, 'Y', '187')
    # Now create the PySB model
    Monomer('A_monomer')
    Monomer('B_monomer', ['Thr185', 'Y187'],
            {'Thr185':['un', 'phos'], 'Y187': ['u', 'p']})
    Rule('A_phos_B', A_monomer() + B_monomer(Thr185='un') >>
                     A_monomer() + B_monomer(Thr185='phos'),
         Parameter('k', 1))
    Initial(A_monomer(), Parameter('A_0', 100))
    Initial(B_monomer(Thr185='un', Y187='u'), Parameter('B_0', 100))
    # Add agent grounding
    Annotation(A_monomer, 'http://identifiers.org/hgnc/HGNC:6840')
    Annotation(B_monomer, 'http://identifiers.org/hgnc/HGNC:6871')
    # Add annotations to the sites/states of the Monomer itself
    B_annot = [
        Annotation('Thr185', 'T', 'is_residue'),
        Annotation('Thr185', '185', 'is_position'),
        Annotation(('Thr185', 'phos'), 'phosphorylation', 'is_modification'),
        Annotation('Y187', 'Y', 'is_residue'),
        Annotation('Y187', '187', 'is_position'),
        Annotation(('Y187', 'p'), 'phosphorylation', 'is_modification'),
    ]
    B_monomer.site_annotations = B_annot
    mc = ModelChecker(model, [st1, st2, st3])
    results = mc.check_model()
    assert len(results) == 3
    assert isinstance(results[0], tuple)
    assert results[0][0] == st1
    assert results[0][1] == True
    assert results[1][0] == st2
    assert results[1][1] == True
    assert results[2][0] == st3
    assert results[2][1] == False


"""
def test_ubiquitination():
    xiap = Agent('XIAP')
    casp3 = Agent('CASP3')
    stmt = Ubiquitination(xiap, casp3)
    pysba = PysbAssembler()
    pysba.add_statements([stmt])
    pysba.make_model(policies='one_step')
    mc = ModelChecker(pysba.model, [stmt])
    checks = mc.check_model()
    assert len(checks) == 1
    assert isinstance(checks[0], tuple)
    assert checks[0][0] == stmt
    assert checks[0][1] == True
"""


# TODO Add tests for autophosphorylation
# TODO Add test for transphosphorylation
# TODO Add test for dephosphorylation

# Goal: Be able to check generic phosphorylations against specific rules
# and vice versa.
# 1. Need PySB assembler to generate appropriate annotations for
#    sites/states
# 1b. Add test making sure modifications can be checked from pysb_assembled
#     model
# 2. Need to be able to annotate specific site/state combinations as
#    active forms
# 3. Need to make grounded_mp generation work with MutConditions and
#    bound conditions (bound conditions would need to check for bonds to
# 4. Grounded monomer patterns for check_activation
#
# Issues--if a rule activity isn't contingent on a particular mod,
# then were will be no causal connection between any upstream modifying
# rules and the downstream rule.

# Active Form vs. Conditions on enzymes
# Identify conflicting ModConditions?
# Refactor out active forms as a preassembly step

# Add "active" into assembled Pysb models as a requirement of every enzyme,
# and add ActiveForms in as rules in the model. This has the advantage of
# working when the activeform is not known (allows tying together activation
# and mods). Problem is what to do with the rules that have mod conditions
# already--add active in? Active flag approach has the advantage of a single
# role for a each substrate, which (I think) would prevent an explosion of
# paths

# Simplest thing: take any rule where the enzyme has no conditions on it
# and replace it with a comparable rule for each activeform.

# Create rules for each active form

# So what's needed is an assembly procedure where an active form is applied
# across all rules for which that protein is the enzyme.

# Need to know which agent is the "enzyme" in rules, so that these can
# be prioritized, and activeforms applied

# Apply weights based on evidence/belief scores;
# Apply weights based on positive

# Another issue--doesn't know that RAF1(phospho='p') should be satisfied
# by RAF1(S259='p'). A big problem, even after pre-assembly--because longer
# paths where a 'phospho' is the observable will never be satisfied.

# Does this mean that we need a PySB ComplexPattern -> Agent mapping, that
# we can subsequently use for refinements?

# Why is

# Need to handle complex statements. Would show that one_step approach
# would not satisfy constraint, but two-step approach could, where the
# Complex information was specified.
# Can probably handle all modifications in a generic function.
# Then need to handle: Complex, Dephosphorylation.
# Then RasGef/RasGap?
# Then Activation/ActiveForm.
# Get the stuff from databases involving the canonical proteins,
# and show that a simple model satisfies it.
# Try to build the model using natural language?
#
# By tying molecules to biological processes, we can even check that
# these types of high-level observations are satisfied.
#
# Need to handle case where Phosphorylation site is not specified by
# statement, but is actually handled in the model (i.e., need to know
# that a particular site name and state corresponds to a phosphorylation.
# Points to need to have an additional data structure annotating agents,
# sites, states.
#
# Need to handle embeddings of complex patterns where sites can have both
# modification state and bonds
#
# Need to handle reversible rules!
#
# Should probably build in some way of returning the paths found
#
# Save all the paths that a particular rule is on--then if you're wondering
# why it's in the model, you look at all of the statements for which that
# rule provides a path.
#
# When Ras machine finds a new finding, it can be checked to see if it's
# satisfied by the model.
if __name__ == '__main__':
    #test_phosphorylation_annotations()
    #test_check_activation()
    #test_none_phosphorylation_stmt()
    #test_distinguish_path_polarity1()
    #test_distinguish_path_polarity2()
    #test_distinguish_path_polarity_none_stmt()
    #test_pysb_assembler_phospho_policies()
    #test_invalid_modification()
    #test_ras_220_network()
    #test_path_polarity()
    #test_consumption_rule()
    test_dephosphorylation()
    #test_check_ubiquitination()
