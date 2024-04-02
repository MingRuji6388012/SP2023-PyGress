# exported from PySB model 'p53_ATR'

from pysb import Model, Monomer, Parameter, Expression, Compartment, Rule, Observable, Initial, MatchOnce, Annotation, ANY, WILD

Model()

Monomer(u'PPM1D', [u'activity'], {u'activity': [u'inactive', u'active']})
Monomer(u'TP53', [u'activity'], {u'activity': [u'inactive', u'active']})
Monomer(u'HIPK2')
Monomer(u'CDKN2A')
Monomer(u'ATR', [u'activity'], {u'activity': [u'inactive', u'active']})
Monomer(u'MDM2', [u'activity'], {u'activity': [u'inactive', u'active']})

Parameter(u'kf_aa_act_1', 5e-06)
Parameter(u'kf_at_act_1', 1e-06)
Parameter(u'kf_tp_act_1', 1e-06)
Parameter(u'kf_tm_act_1', 1e-06)
Parameter(u'kf_pt_act_1', 5e-06)
Parameter(u'kf_mt_act_1', 1e-06)
Parameter(u'kf_hp_act_1', 1e-06)
Parameter(u'kf_cm_act_1', 1e-06)
Parameter(u'PPM1D_0', 1000.0)
Parameter(u'TP53_0', 1000.0)
Parameter(u'HIPK2_0', 1000.0)
Parameter(u'CDKN2A_0', 1000.0)
Parameter(u'ATR_0', 1000.0)
Parameter(u'MDM2_0', 1000.0)
Parameter(u'ATRa_0', 1.0)

Observable('p53_active', TP53(activity=u'active'))
Observable('atr_active', ATR(activity=u'active'))

Rule(u'ATR_activates_ATR_activity', ATR(activity=u'active') + ATR(activity=u'inactive') >> ATR(activity=u'active') + ATR(activity=u'active'), kf_aa_act_1)
Rule(u'ATR_activates_TP53_activity', ATR(activity=u'active') + TP53(activity=u'inactive') >> ATR(activity=u'active') + TP53(activity=u'active'), kf_at_act_1)
Rule(u'TP53_activates_PPM1D_activity', TP53(activity=u'active') + PPM1D(activity=u'inactive') >> TP53(activity=u'active') + PPM1D(activity=u'active'), kf_tp_act_1)
Rule(u'TP53_activates_MDM2_activity', TP53(activity=u'active') + MDM2(activity=u'inactive') >> TP53(activity=u'active') + MDM2(activity=u'active'), kf_tm_act_1)
Rule(u'PPM1D_deactivates_TP53_activity', PPM1D(activity=u'active') + TP53(activity=u'active') >> PPM1D(activity=u'active') + TP53(activity=u'inactive'), kf_pt_act_1)
Rule(u'MDM2_deactivates_TP53_activity', MDM2(activity=u'active') + TP53(activity=u'active') >> MDM2(activity=u'active') + TP53(activity=u'inactive'), kf_mt_act_1)
Rule(u'HIPK2_deactivates_PPM1D_activity', HIPK2() + PPM1D(activity=u'active') >> HIPK2() + PPM1D(activity=u'inactive'), kf_hp_act_1)
Rule(u'CDKN2A_deactivates_MDM2_activity', CDKN2A() + MDM2(activity=u'active') >> CDKN2A() + MDM2(activity=u'inactive'), kf_cm_act_1)

Initial(PPM1D(activity=u'inactive'), PPM1D_0)
Initial(TP53(activity=u'inactive'), TP53_0)
Initial(HIPK2(), HIPK2_0)
Initial(CDKN2A(), CDKN2A_0)
Initial(ATR(activity=u'inactive'), ATR_0)
Initial(MDM2(activity=u'inactive'), MDM2_0)
Initial(ATR(activity=u'active'), ATRa_0)

Annotation(PPM1D, u'http://identifiers.org/hgnc/HGNC:9277', u'is')
Annotation(PPM1D, u'http://identifiers.org/uniprot/O15297', u'is')
Annotation(TP53, u'http://identifiers.org/hgnc/HGNC:11998', u'is')
Annotation(TP53, u'http://identifiers.org/uniprot/P04637', u'is')
Annotation(HIPK2, u'http://identifiers.org/uniprot/Q9H2X6', u'is')
Annotation(HIPK2, u'http://identifiers.org/hgnc/HGNC:14402', u'is')
Annotation(CDKN2A, u'http://identifiers.org/uniprot/Q8N726', u'is')
Annotation(ATR, u'http://identifiers.org/hgnc/HGNC:882', u'is')
Annotation(ATR, u'http://identifiers.org/uniprot/Q13535', u'is')
Annotation(MDM2, u'http://identifiers.org/uniprot/Q00987', u'is')
Annotation(MDM2, u'http://identifiers.org/hgnc/HGNC:6973', u'is')
Annotation(ATR_activates_ATR_activity, u'ATR', u'rule_has_subject')
Annotation(ATR_activates_ATR_activity, u'ATR', u'rule_has_object')
Annotation(ATR_activates_ATR_activity, u'5622ff5e-fcee-49b7-ac88-0f19b5724c84', u'from_indra_statement')
Annotation(ATR_activates_TP53_activity, u'ATR', u'rule_has_subject')
Annotation(ATR_activates_TP53_activity, u'TP53', u'rule_has_object')
Annotation(ATR_activates_TP53_activity, u'893eed58-f18a-494e-8ba8-163652055288', u'from_indra_statement')
Annotation(TP53_activates_PPM1D_activity, u'TP53', u'rule_has_subject')
Annotation(TP53_activates_PPM1D_activity, u'PPM1D', u'rule_has_object')
Annotation(TP53_activates_PPM1D_activity, u'260efc77-5ba9-4a49-ab22-9d36bf3e5df6', u'from_indra_statement')
Annotation(TP53_activates_MDM2_activity, u'TP53', u'rule_has_subject')
Annotation(TP53_activates_MDM2_activity, u'MDM2', u'rule_has_object')
Annotation(TP53_activates_MDM2_activity, u'72787386-de3a-433a-98d3-24aa611a0951', u'from_indra_statement')
Annotation(PPM1D_deactivates_TP53_activity, u'PPM1D', u'rule_has_subject')
Annotation(PPM1D_deactivates_TP53_activity, u'TP53', u'rule_has_object')
Annotation(PPM1D_deactivates_TP53_activity, u'55993328-319a-4f07-aa66-fc45d6fde9c5', u'from_indra_statement')
Annotation(MDM2_deactivates_TP53_activity, u'MDM2', u'rule_has_subject')
Annotation(MDM2_deactivates_TP53_activity, u'TP53', u'rule_has_object')
Annotation(MDM2_deactivates_TP53_activity, u'4adee749-6c05-41b7-9d7f-28cda8885ef0', u'from_indra_statement')
Annotation(HIPK2_deactivates_PPM1D_activity, u'HIPK2', u'rule_has_subject')
Annotation(HIPK2_deactivates_PPM1D_activity, u'PPM1D', u'rule_has_object')
Annotation(HIPK2_deactivates_PPM1D_activity, u'8f4f29e9-19ee-44c5-9f95-82ffd1193128', u'from_indra_statement')
Annotation(CDKN2A_deactivates_MDM2_activity, u'CDKN2A', u'rule_has_subject')
Annotation(CDKN2A_deactivates_MDM2_activity, u'MDM2', u'rule_has_object')
Annotation(CDKN2A_deactivates_MDM2_activity, u'5f3a664a-146c-4498-86d4-79a82e36dcec', u'from_indra_statement')
