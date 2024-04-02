# exported from PySB model 'p53_ATM'

from pysb import Model, Monomer, Parameter, Expression, Compartment, Rule, Observable, Initial, MatchOnce, Annotation, ANY, WILD

Model()

Monomer(u'CDKN2A')
Monomer(u'TP53', [u'activity'], {u'activity': [u'inactive', u'active']})
Monomer(u'ATM', [u'activity'], {u'activity': [u'inactive', u'active']})
Monomer(u'HIPK2')
Monomer(u'PPM1D', [u'activity'], {u'activity': [u'inactive', u'active']})
Monomer(u'MDM2', [u'activity'], {u'activity': [u'inactive', u'active']})

Parameter(u'kf_aa_act_1', 5e-06)
Parameter(u'kf_at_act_1', 1e-06)
Parameter(u'kf_tp_act_1', 1e-06)
Parameter(u'kf_tm_act_1', 1e-06)
Parameter(u'kf_pt_act_1', 5e-06)
Parameter(u'kf_pa_act_1', 0.0001)
Parameter(u'kf_mt_act_1', 1e-06)
Parameter(u'kf_hp_act_1', 1e-06)
Parameter(u'kf_cm_act_1', 1e-06)
Parameter(u'CDKN2A_0', 1000.0)
Parameter(u'TP53_0', 1000.0)
Parameter(u'ATM_0', 1000.0)
Parameter(u'HIPK2_0', 1000.0)
Parameter(u'PPM1D_0', 1000.0)
Parameter(u'MDM2_0', 1000.0)
Parameter(u'ATMa_0', 1.0)

Observable('p53_active', TP53(activity=u'active'))
Observable('atm_active', ATM(activity=u'active'))

Rule(u'ATM_activates_ATM_activity', ATM(activity=u'active') + ATM(activity=u'inactive') >> ATM(activity=u'active') + ATM(activity=u'active'), kf_aa_act_1)
Rule(u'ATM_activates_TP53_activity', ATM(activity=u'active') + TP53(activity=u'inactive') >> ATM(activity=u'active') + TP53(activity=u'active'), kf_at_act_1)
Rule(u'TP53_activates_PPM1D_activity', TP53(activity=u'active') + PPM1D(activity=u'inactive') >> TP53(activity=u'active') + PPM1D(activity=u'active'), kf_tp_act_1)
Rule(u'TP53_activates_MDM2_activity', TP53(activity=u'active') + MDM2(activity=u'inactive') >> TP53(activity=u'active') + MDM2(activity=u'active'), kf_tm_act_1)
Rule(u'PPM1D_deactivates_TP53_activity', PPM1D(activity=u'active') + TP53(activity=u'active') >> PPM1D(activity=u'active') + TP53(activity=u'inactive'), kf_pt_act_1)
Rule(u'PPM1D_deactivates_ATM_activity', PPM1D(activity=u'active') + ATM(activity=u'active') >> PPM1D(activity=u'active') + ATM(activity=u'inactive'), kf_pa_act_1)
Rule(u'MDM2_deactivates_TP53_activity', MDM2(activity=u'active') + TP53(activity=u'active') >> MDM2(activity=u'active') + TP53(activity=u'inactive'), kf_mt_act_1)
Rule(u'HIPK2_deactivates_PPM1D_activity', HIPK2() + PPM1D(activity=u'active') >> HIPK2() + PPM1D(activity=u'inactive'), kf_hp_act_1)
Rule(u'CDKN2A_deactivates_MDM2_activity', CDKN2A() + MDM2(activity=u'active') >> CDKN2A() + MDM2(activity=u'inactive'), kf_cm_act_1)

Initial(CDKN2A(), CDKN2A_0)
Initial(TP53(activity=u'inactive'), TP53_0)
Initial(ATM(activity=u'inactive'), ATM_0)
Initial(HIPK2(), HIPK2_0)
Initial(PPM1D(activity=u'inactive'), PPM1D_0)
Initial(MDM2(activity=u'inactive'), MDM2_0)
Initial(ATM(activity=u'active'), ATMa_0)

Annotation(CDKN2A, u'http://identifiers.org/uniprot/Q8N726', u'is')
Annotation(TP53, u'http://identifiers.org/hgnc/HGNC:11998', u'is')
Annotation(TP53, u'http://identifiers.org/uniprot/P04637', u'is')
Annotation(ATM, u'http://identifiers.org/hgnc/HGNC:795', u'is')
Annotation(ATM, u'http://identifiers.org/uniprot/Q13315', u'is')
Annotation(HIPK2, u'http://identifiers.org/uniprot/Q9H2X6', u'is')
Annotation(HIPK2, u'http://identifiers.org/hgnc/HGNC:14402', u'is')
Annotation(PPM1D, u'http://identifiers.org/hgnc/HGNC:9277', u'is')
Annotation(PPM1D, u'http://identifiers.org/uniprot/O15297', u'is')
Annotation(MDM2, u'http://identifiers.org/uniprot/Q00987', u'is')
Annotation(MDM2, u'http://identifiers.org/hgnc/HGNC:6973', u'is')
Annotation(ATM_activates_ATM_activity, u'ATM', u'rule_has_subject')
Annotation(ATM_activates_ATM_activity, u'ATM', u'rule_has_object')
Annotation(ATM_activates_ATM_activity, u'af38d042-49d3-497c-8c51-2a359206a15c', u'from_indra_statement')
Annotation(ATM_activates_TP53_activity, u'ATM', u'rule_has_subject')
Annotation(ATM_activates_TP53_activity, u'TP53', u'rule_has_object')
Annotation(ATM_activates_TP53_activity, u'254da2f0-9a9a-4309-ab9d-e2fe638002ca', u'from_indra_statement')
Annotation(TP53_activates_PPM1D_activity, u'TP53', u'rule_has_subject')
Annotation(TP53_activates_PPM1D_activity, u'PPM1D', u'rule_has_object')
Annotation(TP53_activates_PPM1D_activity, u'036ead6f-2c66-4be1-9864-0830a123e169', u'from_indra_statement')
Annotation(TP53_activates_MDM2_activity, u'TP53', u'rule_has_subject')
Annotation(TP53_activates_MDM2_activity, u'MDM2', u'rule_has_object')
Annotation(TP53_activates_MDM2_activity, u'63e0499c-58fd-4269-a9a2-89d466f21270', u'from_indra_statement')
Annotation(PPM1D_deactivates_TP53_activity, u'PPM1D', u'rule_has_subject')
Annotation(PPM1D_deactivates_TP53_activity, u'TP53', u'rule_has_object')
Annotation(PPM1D_deactivates_TP53_activity, u'b2d65a5c-9d53-4db9-bf41-6ba6563f4b16', u'from_indra_statement')
Annotation(PPM1D_deactivates_ATM_activity, u'PPM1D', u'rule_has_subject')
Annotation(PPM1D_deactivates_ATM_activity, u'ATM', u'rule_has_object')
Annotation(PPM1D_deactivates_ATM_activity, u'b5ef56a9-b8b6-41e8-9844-29e5506769d2', u'from_indra_statement')
Annotation(MDM2_deactivates_TP53_activity, u'MDM2', u'rule_has_subject')
Annotation(MDM2_deactivates_TP53_activity, u'TP53', u'rule_has_object')
Annotation(MDM2_deactivates_TP53_activity, u'1286b4c3-a989-4612-b5bf-06450827d323', u'from_indra_statement')
Annotation(HIPK2_deactivates_PPM1D_activity, u'HIPK2', u'rule_has_subject')
Annotation(HIPK2_deactivates_PPM1D_activity, u'PPM1D', u'rule_has_object')
Annotation(HIPK2_deactivates_PPM1D_activity, u'a3adb843-40d6-48a8-9f1d-6cb0e131415d', u'from_indra_statement')
Annotation(CDKN2A_deactivates_MDM2_activity, u'CDKN2A', u'rule_has_subject')
Annotation(CDKN2A_deactivates_MDM2_activity, u'MDM2', u'rule_has_object')
Annotation(CDKN2A_deactivates_MDM2_activity, u'c5eb110d-a083-470f-8e56-8030cefdcbfe', u'from_indra_statement')
