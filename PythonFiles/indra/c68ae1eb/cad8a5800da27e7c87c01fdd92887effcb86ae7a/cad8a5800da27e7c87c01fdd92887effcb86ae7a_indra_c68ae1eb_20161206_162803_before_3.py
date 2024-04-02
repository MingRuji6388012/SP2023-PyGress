from __future__ import absolute_import, print_function, unicode_literals
from builtins import dict, str
from indra.assemblers import PysbAssembler
from indra.assemblers import pysb_assembler as pa
from indra.statements import *
from pysb import bng, WILD, Monomer, Annotation
from pysb.testing import with_model

def test_pysb_assembler_complex1():
    member1 = Agent('BRAF')
    member2 = Agent('MEK1')
    stmt = Complex([member1, member2])
    pa = PysbAssembler()
    pa.add_statements([stmt])
    model = pa.make_model()
    assert(len(model.rules)==2)
    assert(len(model.monomers)==2)

def test_pysb_assembler_complex2():
    member1 = Agent('BRAF')
    member2 = Agent('MEK1')
    member3 = Agent('ERK1')
    stmt = Complex([member1, member2, member3])
    pa = PysbAssembler()
    pa.add_statements([stmt])
    model = pa.make_model()
    assert(len(model.rules)==6)
    assert(len(model.monomers)==3)

def test_pysb_assembler_complex3():
    hras = Agent('HRAS')
    member1 = Agent('BRAF', bound_conditions=[BoundCondition(hras, True)])
    member2 = Agent('MEK1')
    stmt = Complex([member1, member2])
    pa = PysbAssembler()
    pa.add_statements([stmt])
    model = pa.make_model()
    assert(len(model.rules)==2)
    assert(len(model.monomers)==3)

def test_pysb_assembler_complex_twostep():
    member1 = Agent('BRAF')
    member2 = Agent('MEK1')
    stmt = Complex([member1, member2])
    pa = PysbAssembler()
    pa.add_statements([stmt])
    model = pa.make_model(policies='two_step')
    assert(len(model.rules)==2)
    assert(len(model.monomers)==2)

def test_pysb_assembler_complex_multiway():
    member1 = Agent('BRAF')
    member2 = Agent('MEK1')
    member3 = Agent('ERK1')
    stmt = Complex([member1, member2, member3])
    pa = PysbAssembler()
    pa.add_statements([stmt])
    model = pa.make_model(policies='multi_way')
    assert(len(model.rules)==2)
    assert(len(model.monomers)==3)

def test_pysb_assembler_actsub():
    stmt = ActiveForm(Agent('BRAF', mutations=[MutCondition('600', 'V', 'E')]),
                      'activity', True)
    pa = PysbAssembler()
    pa.add_statements([stmt])
    model = pa.make_model(policies='two_step')
    assert(len(model.rules)==0)
    assert(len(model.monomers)==1)

def test_pysb_assembler_phos_noenz():
    enz = None
    sub = Agent('MEK1')
    stmt = Phosphorylation(enz, sub, 'serine', '222')
    pa = PysbAssembler()
    pa.add_statements([stmt])
    model = pa.make_model()
    assert(len(model.rules)==0)
    assert(len(model.monomers)==0)

def test_pysb_assembler_dephos_noenz():
    enz = None
    sub = Agent('MEK1')
    stmt = Phosphorylation(enz, sub, 'serine', '222')
    pa = PysbAssembler()
    pa.add_statements([stmt])
    model = pa.make_model()
    assert(len(model.rules)==0)
    assert(len(model.monomers)==0)

def test_pysb_assembler_phos1():
    enz = Agent('BRAF')
    sub = Agent('MEK1')
    stmt = Phosphorylation(enz, sub, 'serine', '222')
    pa = PysbAssembler()
    pa.add_statements([stmt])
    model = pa.make_model()
    assert(len(model.rules)==1)
    assert(len(model.monomers)==2)

def test_pysb_assembler_phos2():
    hras = Agent('HRAS')
    enz = Agent('BRAF', bound_conditions=[BoundCondition(hras, True)])
    sub = Agent('MEK1')
    stmt = Phosphorylation(enz, sub, 'serine', '222')
    pa = PysbAssembler()
    pa.add_statements([stmt])
    model = pa.make_model()
    assert(len(model.rules)==1)
    assert(len(model.monomers)==3)

def test_pysb_assembler_phos3():
    hras = Agent('HRAS')
    erk1 = Agent('ERK1')
    enz = Agent('BRAF', bound_conditions=[BoundCondition(hras, True)])
    sub = Agent('MEK1', bound_conditions=[BoundCondition(erk1, True)])
    stmt = Phosphorylation(enz, sub, 'serine', '222')
    pa = PysbAssembler()
    pa.add_statements([stmt])
    model = pa.make_model()
    assert(len(model.rules)==1)
    assert(len(model.monomers)==4)

def test_pysb_assembler_phos4():
    hras = Agent('HRAS')
    erk1 = Agent('ERK1')
    enz = Agent('BRAF', bound_conditions=[BoundCondition(hras, True)])
    sub = Agent('MEK1', bound_conditions=[BoundCondition(erk1, False)])
    stmt = Phosphorylation(enz, sub, 'serine', '222')
    pa = PysbAssembler()
    pa.add_statements([stmt])
    model = pa.make_model()
    assert(len(model.rules)==1)
    assert(len(model.monomers)==4)

def test_pysb_assembler_autophos1():
    enz = Agent('MEK1')
    stmt = Autophosphorylation(enz, 'serine', '222')
    pa = PysbAssembler()
    pa.add_statements([stmt])
    model = pa.make_model()
    assert(len(model.rules)==1)
    assert(len(model.monomers)==1)

def test_pysb_assembler_autophos2():
    raf1 = Agent('RAF1')
    enz = Agent('MEK1', bound_conditions=[BoundCondition(raf1, True)])
    stmt = Autophosphorylation(enz, 'serine', '222')
    pa = PysbAssembler()
    pa.add_statements([stmt])
    model = pa.make_model()
    assert(len(model.rules)==1)
    assert(len(model.monomers)==2)

def test_pysb_assembler_autophos3():
    egfr = Agent('EGFR')
    enz = Agent('EGFR', bound_conditions=[BoundCondition(egfr, True)])
    stmt = Autophosphorylation(enz, 'tyrosine')
    pa = PysbAssembler()
    pa.add_statements([stmt])
    model = pa.make_model()
    assert(len(model.rules)==1)
    assert(len(model.monomers)==1)

def test_pysb_assembler_transphos1():
    egfr = Agent('EGFR')
    enz = Agent('EGFR', bound_conditions=[BoundCondition(egfr, True)])
    stmt = Transphosphorylation(enz, 'tyrosine')
    pa = PysbAssembler()
    pa.add_statements([stmt])
    model = pa.make_model()
    assert(len(model.rules)==1)
    assert(len(model.monomers)==1)

def test_pysb_assembler_act1():
    egfr = Agent('EGFR')
    subj = Agent('GRB2', bound_conditions=[BoundCondition(egfr, True)])
    obj = Agent('SOS1')
    stmt = Activation(subj, 'activity', obj, 'activity', True)
    pa = PysbAssembler()
    pa.add_statements([stmt])
    model = pa.make_model()
    assert(len(model.rules)==1)
    assert(len(model.monomers)==3)

def test_pysb_assembler_dephos1():
    phos = Agent('PP2A')
    sub = Agent('MEK1')
    stmt = Dephosphorylation(phos, sub, 'serine', '222')
    pa = PysbAssembler()
    pa.add_statements([stmt])
    model = pa.make_model()
    assert(len(model.rules)==1)
    assert(len(model.monomers)==2)

def test_pysb_assembler_dephos2():
    phos = Agent('PP2A')
    raf1 = Agent('RAF1')
    sub = Agent('MEK1', bound_conditions=[BoundCondition(raf1, True)])
    stmt = Dephosphorylation(phos, sub, 'serine', '222')
    pa = PysbAssembler()
    pa.add_statements([stmt])
    model = pa.make_model()
    assert(len(model.rules)==1)
    assert(len(model.monomers)==3)

def test_pysb_assembler_rasgef1():
    gef = Agent('SOS1')
    ras = Agent('HRAS')
    stmt = RasGef(gef, 'catalytic', ras)
    pa = PysbAssembler()
    pa.add_statements([stmt])
    model = pa.make_model()
    assert(len(model.rules)==1)
    assert(len(model.monomers)==2)

def test_pysb_assembler_rasgap1():
    gap = Agent('NF1')
    ras = Agent('HRAS')
    stmt = RasGap(gap, 'catalytic', ras)
    pa = PysbAssembler()
    pa.add_statements([stmt])
    model = pa.make_model()
    assert(len(model.rules)==1)
    assert(len(model.monomers)==2)

def test_pysb_assembler_actmod1():
    mek = Agent('MEK')
    erk = Agent('ERK')
    stmts = []
    mc1 = ModCondition('phosphorylation', 'serine', '218')
    mc2 = ModCondition('phosphorylation', 'serine', '222')
    stmts.append(ActiveForm(Agent('MEK', mods=[mc1, mc2]), 'activity', True))
    stmts.append(Phosphorylation(mek, erk, 'threonine', '185'))
    stmts.append(Phosphorylation(mek, erk, 'tyrosine', '187'))
    pa = PysbAssembler()
    pa.add_statements(stmts)
    model = pa.make_model()
    assert(len(model.rules)==2)
    assert(len(model.monomers)==2)

def test_pysb_assembler_actmod2():
    mek = Agent('MEK')
    erk = Agent('ERK')
    stmts = []
    stmts.append(ActiveForm(Agent('MEK',
                    mods=[ModCondition('phosphorylation', 'serine', '218')]),
                    'activity', True))
    stmts.append(ActiveForm(Agent('MEK',
                    mods=[ModCondition('phosphorylation', 'serine', '222')]),
                    'activity', True))
    stmts.append(Phosphorylation(mek, erk, 'threonine', '185'))
    stmts.append(Phosphorylation(mek, erk, 'tyrosine', '187'))
    pa = PysbAssembler()
    pa.add_statements(stmts)
    model = pa.make_model()
    assert(len(model.rules)==4)
    assert(len(model.monomers)==2)

def test_pysb_assembler_phos_twostep1():
    enz = Agent('BRAF')
    sub = Agent('MEK1')
    stmt = Phosphorylation(enz, sub, 'serine', '222')
    pa = PysbAssembler(policies='two_step')
    pa.add_statements([stmt])
    model = pa.make_model()
    assert(len(model.rules)==3)
    assert(len(model.monomers)==2)

def test_pysb_assembler_twostep_mixed():
    member1 = Agent('BRAF')
    member2 = Agent('RAF1')
    st1 = Complex([member1, member2])
    st2 = Phosphorylation(Agent('MAP2K1'), Agent('MAPK3'))
    pa = PysbAssembler()
    pa.add_statements([st1, st2])
    pa.make_model(policies='two_step')
    assert(len(pa.model.rules)==5)
    assert(len(pa.model.monomers)==4)

def test_pysb_assembler_phos_twostep_local():
    enz = Agent('BRAF')
    sub = Agent('MEK1')
    stmt = Phosphorylation(enz, sub, 'serine', '222')
    pa = PysbAssembler()
    pa.add_statements([stmt])
    model = pa.make_model(policies='two_step')
    assert(len(model.rules)==3)
    assert(len(model.monomers)==2)

def test_pysb_assembler_phos_twostep_local_to_global():
    enz = Agent('BRAF')
    sub = Agent('MEK1')
    stmt = Phosphorylation(enz, sub, 'serine', '222')
    pa = PysbAssembler()
    pa.add_statements([stmt])
    model = pa.make_model(policies='two_step')
    # This call should have reverted to default policy
    model = pa.make_model()
    assert(len(model.rules)==1)
    assert(len(model.monomers)==2)

def test_pysb_assembler_dephos_twostep1():
    phos = Agent('PP2A')
    sub = Agent('MEK1')
    stmt = Dephosphorylation(phos, sub, 'serine', '222')
    pa = PysbAssembler(policies='two_step')
    pa.add_statements([stmt])
    model = pa.make_model()
    assert(len(model.rules)==3)
    assert(len(model.monomers)==2)

def test_statement_specific_policies():
    enz = Agent('BRAF')
    sub = Agent('MEK1')
    phos = Agent('PP2A')
    stmt1 = Phosphorylation(enz, sub, 'serine', '222')
    stmt2 = Dephosphorylation(phos, sub, 'serine', '222')
    policies = {'Phosphorylation': 'two_step',
                'Dephosphorylation': 'interactions_only'}
    pa = PysbAssembler(policies=policies)
    pa.add_statements([stmt1, stmt2])
    model = pa.make_model()
    assert(len(model.rules)==4)
    assert(len(model.monomers)==3)

def test_unspecified_statement_policies():
    enz = Agent('BRAF')
    sub = Agent('MEK1')
    phos = Agent('PP2A')
    stmt1 = Phosphorylation(enz, sub, 'serine', '222')
    stmt2 = Dephosphorylation(phos, sub, 'serine', '222')
    policies = {'Phosphorylation': 'two_step',
                'other': 'interactions_only'}
    pa = PysbAssembler(policies=policies)
    pa.add_statements([stmt1, stmt2])
    model = pa.make_model()
    assert(len(model.rules)==4)
    assert(len(model.monomers)==3)

def test_activity_activity():
    subj = Agent('KRAS')
    obj = Agent('BRAF')
    stmt = Activation(subj, 'activity', obj, 'activity', True)
    pa = PysbAssembler(policies='interactions_only')
    pa.add_statements([stmt])
    model = pa.make_model()
    assert(len(model.rules)==1)
    assert(len(model.monomers)==2)

def test_activity_activity2():
    subj = Agent('KRAS')
    obj = Agent('BRAF')
    stmt = Activation(subj, 'activity', obj, 'activity', True)
    pa = PysbAssembler(policies='one_step')
    pa.add_statements([stmt])
    model = pa.make_model()
    assert(len(model.rules)==1)
    assert(len(model.monomers)==2)

def test_activity_activity2():
    subj = Agent('Vemurafenib')
    obj = Agent('BRAF')
    stmt = Activation(subj, None, obj, 'activity', False)
    pa = PysbAssembler(policies='interactions_only')
    pa.add_statements([stmt])
    model = pa.make_model()
    assert(len(model.rules)==1)
    assert(len(model.monomers)==2)

def test_activity_activity3():
    subj = Agent('Vemurafenib')
    obj = Agent('BRAF')
    stmt = Activation(subj, None, obj, 'activity', False)
    pa = PysbAssembler(policies='one_step')
    pa.add_statements([stmt])
    model = pa.make_model()
    assert(len(model.rules)==1)
    assert(len(model.monomers)==2)

def test_rule_name_str_1():
    s = pa.get_agent_rule_str(Agent('BRAF'))
    assert(s == 'BRAF')

def test_rule_name_str_2():
    a = Agent('GRB2',
              bound_conditions=[BoundCondition(Agent('EGFR'), True)])
    s = pa.get_agent_rule_str(a)
    assert(s == 'GRB2_EGFR')

def test_rule_name_str_3():
    a = Agent('GRB2',
              bound_conditions=[BoundCondition(Agent('EGFR'), False)])
    s = pa.get_agent_rule_str(a)
    assert(s == 'GRB2_nEGFR')

def test_rule_name_str_4():
    a = Agent('BRAF', mods=[ModCondition('phosphorylation', 'serine')])
    s = pa.get_agent_rule_str(a)
    assert(s == 'BRAF_phosphoS')

def test_rule_name_str_5():
    a = Agent('BRAF', mods=[ModCondition('phosphorylation', 'serine', '123')])
    s = pa.get_agent_rule_str(a)
    assert(s == 'BRAF_phosphoS123')

def test_neg_act_mod():
    mc = ModCondition('phosphorylation', 'serine', '123', False)
    st1 = ActiveForm(Agent('BRAF', mods=[mc]), 'active', True)
    st2 = Phosphorylation(Agent('BRAF'), Agent('MAP2K2'))
    pa = PysbAssembler(policies='one_step')
    pa.add_statements([st1, st2])
    pa.make_model()
    assert(len(pa.model.rules) == 1)
    r = pa.model.rules[0]
    braf = r.reactant_pattern.complex_patterns[0].monomer_patterns[0]
    assert(braf.monomer.name == 'BRAF')
    assert(braf.site_conditions == {'S123': ('u', WILD)})

def test_pos_agent_mod():
    mc = ModCondition('phosphorylation', 'serine', '123', True)
    st = Phosphorylation(Agent('BRAF', mods=[mc]), Agent('MAP2K2'))
    pa = PysbAssembler(policies='one_step')
    pa.add_statements([st])
    pa.make_model()
    assert(len(pa.model.rules) == 1)
    r = pa.model.rules[0]
    braf = r.reactant_pattern.complex_patterns[0].monomer_patterns[0]
    assert(braf.monomer.name == 'BRAF')
    assert(braf.site_conditions == {'S123': ('p', WILD)})

def test_neg_agent_mod():
    mc = ModCondition('phosphorylation', 'serine', '123', False)
    st = Phosphorylation(Agent('BRAF', mods=[mc]), Agent('MAP2K2'))
    pa = PysbAssembler(policies='one_step')
    pa.add_statements([st])
    pa.make_model()
    assert(len(pa.model.rules) == 1)
    r = pa.model.rules[0]
    braf = r.reactant_pattern.complex_patterns[0].monomer_patterns[0]
    assert(braf.monomer.name == 'BRAF')
    assert(braf.site_conditions == {'S123': ('u', WILD)})

def test_mut():
    mut = MutCondition('600', 'V', 'E')
    st = Phosphorylation(Agent('BRAF', mutations=[mut]), Agent('MEK'))
    pa = PysbAssembler()
    pa.add_statements([st])
    pa.make_model()
    assert(len(pa.model.rules) == 1)
    r = pa.model.rules[0]
    braf = r.reactant_pattern.complex_patterns[0].monomer_patterns[0]
    assert(braf.monomer.name == 'BRAF')
    assert(braf.site_conditions == {'V600': 'E'})

def test_agent_loc():
    st = Phosphorylation(Agent('BRAF', location='cytoplasm'), Agent('MEK'))
    pa = PysbAssembler()
    pa.add_statements([st])
    pa.make_model()
    assert(len(pa.model.rules) == 1)
    r = pa.model.rules[0]
    braf = r.reactant_pattern.complex_patterns[0].monomer_patterns[0]
    assert(braf.site_conditions == {'loc': 'cytoplasm'})

def test_translocation():
    st = Translocation(Agent('FOXO3A'), 'nucleus', 'cytoplasm')
    pa = PysbAssembler()
    pa.add_statements([st])
    pa.make_model()
    assert(len(pa.model.rules) == 1)
    r = pa.model.rules[0]
    f1 = r.reactant_pattern.complex_patterns[0].monomer_patterns[0]
    assert(f1.site_conditions == {'loc': 'nucleus'})
    f2 = r.product_pattern.complex_patterns[0].monomer_patterns[0]
    assert(f2.site_conditions == {'loc': 'cytoplasm'})
    assert(r.rate_forward.name == 'kf_foxo3a_nucleus_cytoplasm_1')

def test_phos_atpdep():
    st = Phosphorylation(Agent('BRAF'), Agent('MEK'), 'S', '222')
    pa = PysbAssembler()
    pa.add_statements([st])
    pa.make_model(policies='atp_dependent')
    assert(len(pa.model.rules) == 5)

def test_set_context():
    st = Phosphorylation(Agent('MAP2K1'), Agent('MAPK3'))
    pa = PysbAssembler()
    pa.add_statements([st])
    pa.make_model()
    assert(pa.model.parameters['MAP2K1_0'].value < 1000)
    assert(pa.model.parameters['MAPK3_0'].value < 1000)
    pa.set_context('A375_SKIN')
    assert(pa.model.parameters['MAP2K1_0'].value > 10000)
    assert(pa.model.parameters['MAPK3_0'].value > 10000)

def test_set_context_monomer_notfound():
    st = Phosphorylation(Agent('MAP2K1'), Agent('XYZ'))
    pa = PysbAssembler()
    pa.add_statements([st])
    pa.make_model()
    assert(pa.model.parameters['MAP2K1_0'].value < 1000)
    assert(pa.model.parameters['XYZ_0'].value < 1000)
    pa.set_context('A375_SKIN')
    assert(pa.model.parameters['MAP2K1_0'].value > 10000)
    assert(pa.model.parameters['XYZ_0'].value < 1000)

def test_set_context_celltype_notfound():
    st = Phosphorylation(Agent('MAP2K1'), Agent('MAPK3'))
    pa = PysbAssembler()
    pa.add_statements([st])
    pa.make_model()
    pa.set_context('XYZ')

def test_annotation():
    st = Phosphorylation(Agent('BRAF', db_refs = {'UP': 'P15056'}),
                         Agent('MAP2K2', db_refs = {'HGNC': '6842'}))
    pa = PysbAssembler()
    pa.add_statements([st])
    pa.make_model()
    assert(len(pa.model.annotations) == 2)

def test_print_model():
    st = Phosphorylation(Agent('MAP2K1'), Agent('MAPK3'))
    pa = PysbAssembler()
    pa.add_statements([st])
    pa.make_model()
    pa.save_model('/dev/null')

def test_save_rst():
    st = Phosphorylation(Agent('MAP2K1'), Agent('MAPK3'))
    pa = PysbAssembler()
    pa.add_statements([st])
    pa.make_model()
    pa.save_rst('/dev/null')

def test_name_standardize():
    n = pa._n('.*/- ^&#@$')
    assert(isinstance(n, str))
    assert(n == '__________')
    n = pa._n('14-3-3')
    assert(isinstance(n, str))
    assert(n == 'p14_3_3')
    n = pa._n('\U0001F4A9bar')
    assert(isinstance(n, str))
    assert(n == 'bar')

def test_generate_equations():
    st = Phosphorylation(Agent('MAP2K1'), Agent('MAPK3'))
    pa = PysbAssembler()
    pa.add_statements([st])
    pa.make_model()
    bng.generate_equations(pa.model)

def test_non_python_name_phos():
    st = Phosphorylation(Agent('14-3-3'), Agent('BRAF kinase'))
    pa = PysbAssembler()
    pa.add_statements([st])
    pa.make_model()
    names = [m.name for m in pa.model.monomers]
    assert('BRAF_kinase' in names)
    assert('p14_3_3' in names)
    bng.generate_equations(pa.model)

def test_non_python_name_bind():
    st = Complex([Agent('14-3-3'), Agent('BRAF kinase')])
    pa = PysbAssembler()
    pa.add_statements([st])
    pa.make_model()
    bng.generate_equations(pa.model)

def test_degradation_one_step():
    subj = Agent('KRAS')
    obj = Agent('BRAF')
    st1 = Degradation(subj, obj)
    st2 = Degradation(None, obj)
    pa = PysbAssembler(policies='one_step')
    pa.add_statements([st1, st2])
    model = pa.make_model()
    assert(len(model.rules)==2)
    assert(len(model.monomers)==2)

def test_degradation_interactions_only():
    subj = Agent('KRAS')
    obj = Agent('BRAF')
    st1 = Degradation(subj, obj)
    st2 = Degradation(None, obj)
    pa = PysbAssembler(policies='interactions_only')
    pa.add_statements([st1, st2])
    model = pa.make_model()
    assert(len(model.rules)==1)
    assert(len(model.monomers)==2)

def test_synthesis_one_step():
    subj = Agent('KRAS')
    obj = Agent('BRAF')
    st1 = Synthesis(subj, obj)
    st2 = Synthesis(None, obj)
    pa = PysbAssembler(policies='one_step')
    pa.add_statements([st1, st2])
    model = pa.make_model()
    assert(len(model.rules)==2)
    assert(len(model.monomers)==2)

def test_synthesis_monomer_pattern():
    subj = Agent('KRAS')
    obj = Agent('BRAF')
    st1 = Activation(subj, 'activity', obj, 'activity', True)
    st2 = Synthesis(subj, obj)
    pa = PysbAssembler(policies='one_step')
    pa.add_statements([st1, st2])
    model = pa.make_model()
    assert(len(model.rules)==2)
    assert(len(model.monomers)==2)
    # This ensures that the synthesized BRAF monomer
    # is in its fully specified "base" state
    bng.generate_equations(model)

def test_synthesis_interactions_only():
    subj = Agent('KRAS')
    obj = Agent('BRAF')
    st1 = Synthesis(subj, obj)
    st2 = Synthesis(None, obj)
    pa = PysbAssembler(policies='interactions_only')
    pa.add_statements([st1, st2])
    model = pa.make_model()
    assert(len(model.rules)==1)
    assert(len(model.monomers)==2)

def test_missing_catalytic_default_site():
    c8 = Agent('CASP8')
    c3 = Agent('CASP3')
    stmt = Activation(c8, 'catalytic', c3, 'catalytic', True)
    # Interactions only
    pa = PysbAssembler(policies='interactions_only')
    pa.add_statements([stmt])
    model = pa.make_model()
    # One step
    pa = PysbAssembler(policies='one_step')
    pa.add_statements([stmt])
    model = pa.make_model()
    # Two step
    pa = PysbAssembler(policies='two_step')
    pa.add_statements([stmt])
    model = pa.make_model()

def test_missing_transcription_default_site():
    p53 = Agent('TP53')
    bax = Agent('BAX')
    stmt = Activation(p53, 'transcription', bax, 'activity', True)
    # Interactions only
    pa = PysbAssembler(policies='interactions_only')
    pa.add_statements([stmt])
    model = pa.make_model()
    # One step
    pa = PysbAssembler(policies='one_step')
    pa.add_statements([stmt])
    model = pa.make_model()
    # Two step
    pa = PysbAssembler(policies='two_step')
    pa.add_statements([stmt])
    model = pa.make_model()

def test_translocation_loc_special_char():
    st = Translocation(Agent('KSR1'), 'cytoplasm', 'cell surface')
    pa = PysbAssembler()
    pa.add_statements([st])
    pa.make_model()
    assert(len(pa.model.rules) == 1)
    r = pa.model.rules[0]
    f1 = r.reactant_pattern.complex_patterns[0].monomer_patterns[0]
    assert(f1.site_conditions == {'loc': 'cytoplasm'})
    f2 = r.product_pattern.complex_patterns[0].monomer_patterns[0]
    assert(f2.site_conditions == {'loc': 'cell_surface'})
    assert(r.rate_forward.name == 'kf_ksr1_cytoplasm_cell_surface_1')

def test_parse_identifiers_url():
    url1 = 'http://identifiers.org/foo/bar'
    url2 = 'http://identifiers.org/hgnc/12345'
    url3 = 'http://identifiers.org/hgnc/HGNC:12345'
    url4 = 'http://identifiers.org/uniprot/12345'
    url5 = 'http://identifiers.org/chebi/12345'
    url6 = 'http://identifiers.org/interpro/12345'
    url7 = 'http://identifiers.org/pfam/12345'
    (ns, id) = pa.parse_identifiers_url(url1)
    assert ns is None and id is None
    (ns, id) = pa.parse_identifiers_url(url2)
    assert ns is None and id is None
    (ns, id) = pa.parse_identifiers_url(url3)
    assert ns == 'HGNC' and id == '12345'
    (ns, id) = pa.parse_identifiers_url(url4)
    assert ns == 'UP' and id == '12345'
    (ns, id) = pa.parse_identifiers_url(url5)
    assert ns == 'CHEBI' and id == '12345'
    (ns, id) = pa.parse_identifiers_url(url6)
    assert ns == 'IP' and id == '12345'
    (ns, id) = pa.parse_identifiers_url(url7)
    assert ns == 'XFAM' and id == '12345'

@with_model
def test_get_mp_with_grounding():
    foo = Agent('Foo', db_refs={'HGNC': 'foo'})
    a = Agent('A', db_refs={'HGNC': '6840'})
    b = Agent('B', db_refs={'HGNC': '6871'})
    Monomer('A_monomer')
    Monomer('B_monomer')
    Annotation(A_monomer, 'http://identifiers.org/hgnc/HGNC:6840')
    Annotation(B_monomer, 'http://identifiers.org/hgnc/HGNC:6871')
    mps = list(pa.grounded_monomer_patterns(model, foo))
    assert len(mps) == 0
    mps = list(pa.grounded_monomer_patterns(model, a))
    assert len(mps) == 1
    assert mps[0].monomer == A_monomer
    mps = list(pa.grounded_monomer_patterns(model, b))
    assert len(mps) == 1
    assert mps[0].monomer == B_monomer

@with_model
def test_get_mp_with_grounding_2():
    a1 = Agent('A', mods=[ModCondition('phosphorylation', None, None)],
                db_refs={'HGNC': '6840'})
    a2 = Agent('A', mods=[ModCondition('phosphorylation', 'Y', '187')],
                db_refs={'HGNC': '6840'})
    Monomer('A_monomer', ['phospho', 'T185', 'Y187'],
            {'phospho': 'y', 'T185':['u', 'p'], 'Y187':['u','p']})
    Annotation(A_monomer, 'http://identifiers.org/hgnc/HGNC:6840')
    A_monomer.site_annotations = [
        Annotation(('phospho', 'y'), 'phosphorylation', 'is_modification'),
        Annotation(('T185', 'p'), 'phosphorylation', 'is_modification'),
        Annotation(('Y187', 'p'), 'phosphorylation', 'is_modification'),
        Annotation('T185', 'T', 'is_residue'),
        Annotation('T185', '185', 'is_position'),
        Annotation('Y187', 'Y', 'is_residue'),
        Annotation('Y187', '187', 'is_position')
    ]
    mps_1 = list(pa.grounded_monomer_patterns(model, a1))
    assert len(mps_1) == 3
    mps_2 = list(pa.grounded_monomer_patterns(model, a2))
    assert len(mps_2) == 1
    mp = mps_2[0]
    assert mp.monomer == A_monomer
    assert mp.site_conditions == {'Y187': 'p'}
    # TODO Add test for unmodified agent!
    # TODO Add test involving multiple (possibly degenerate) modifications!

if __name__ == '__main__':
    test_get_mp_with_grounding()
    test_get_mp_with_grounding_2()