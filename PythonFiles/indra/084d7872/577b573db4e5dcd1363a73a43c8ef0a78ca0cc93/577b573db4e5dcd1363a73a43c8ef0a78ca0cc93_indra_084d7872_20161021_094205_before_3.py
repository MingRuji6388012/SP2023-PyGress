# exported from PySB model 'None'

from pysb import Model, Monomer, Parameter, Expression, Compartment, Rule, Observable, Initial, MatchOnce, Annotation, ANY, WILD

Model()

Monomer('CDKN2A', ['act'], {'act': ['inactive', 'active']})
Monomer('TP53', ['act'], {'act': ['inactive', 'active']})
Monomer('PROTEASE', ['act'], {'act': ['inactive', 'active']})
Monomer('PPM1D', ['act'], {'act': ['inactive', 'active']})
Monomer('ATR', ['act'], {'act': ['inactive', 'active']})
Monomer('MDM2', ['act'], {'act': ['inactive', 'active']})

Parameter('kf_aa_act_1', 5e-06)
Parameter('kf_at_act_1', 1e-06)
Parameter('kf_tp_act_1', 1e-06)
Parameter('kf_tm_act_1', 1e-06)
Parameter('kf_pt_act_1', 1e-05)
Parameter('kf_mt_act_1', 1e-06)
Parameter('kf_pp_act_1', 1e-06)
Parameter('kf_cm_act_1', 1e-06)
Parameter('CDKN2A_0', 0)
Parameter('TP53_0', 100.0)
Parameter('PROTEASE_0', 0)
Parameter('PPM1D_0', 100.0)
Parameter('ATR_0', 99.0)
Parameter('MDM2_0', 100.0)
Parameter('CDKN2A_act_0', 100.0)
Parameter('PROTEASE_act_0', 100.0)
Parameter('ATRa_0', 1.0)

Observable('P53_active', TP53(act='active'))

Rule('ATR_activity_activates_ATR_activity', ATR(act='active') + ATR(act='inactive') >> ATR(act='active') + ATR(act='active'), kf_aa_act_1)
Rule('ATR_activity_activates_TP53_activity', ATR(act='active') + TP53(act='inactive') >> ATR(act='active') + TP53(act='active'), kf_at_act_1)
Rule('TP53_activity_activates_PPM1D_activity', TP53(act='active') + PPM1D(act='inactive') >> TP53(act='active') + PPM1D(act='active'), kf_tp_act_1)
Rule('TP53_activity_activates_MDM2_activity', TP53(act='active') + MDM2(act='inactive') >> TP53(act='active') + MDM2(act='active'), kf_tm_act_1)
Rule('PPM1D_activity_activates_TP53_activity', PPM1D(act='active') + TP53(act='active') >> PPM1D(act='active') + TP53(act='inactive'), kf_pt_act_1)
Rule('MDM2_activity_activates_TP53_activity', MDM2(act='active') + TP53(act='active') >> MDM2(act='active') + TP53(act='inactive'), kf_mt_act_1)
Rule('PROTEASE_activity_activates_PPM1D_activity', PROTEASE(act='active') + PPM1D(act='active') >> PROTEASE(act='active') + PPM1D(act='inactive'), kf_pp_act_1)
Rule('CDKN2A_activity_activates_MDM2_activity', CDKN2A(act='active') + MDM2(act='active') >> CDKN2A(act='active') + MDM2(act='inactive'), kf_cm_act_1)

Initial(CDKN2A(act='inactive'), CDKN2A_0)
Initial(TP53(act='inactive'), TP53_0)
Initial(PROTEASE(act='inactive'), PROTEASE_0)
Initial(PPM1D(act='inactive'), PPM1D_0)
Initial(ATR(act='inactive'), ATR_0)
Initial(MDM2(act='inactive'), MDM2_0)
Initial(PROTEASE(act='active'), PROTEASE_act_0)
Initial(CDKN2A(act='active'), CDKN2A_act_0)
Initial(ATR(act='active'), ATRa_0)

Annotation(CDKN2A, 'http://identifiers.org/uniprot/Q8N726', 'is')
Annotation(CDKN2A, 'http://identifiers.org/hgnc/HGNC:1787', 'is')
Annotation(TP53, 'http://identifiers.org/pfam/PF11619.6', 'is')
Annotation(TP53, 'http://identifiers.org/uniprot/P04637', 'is')
Annotation(TP53, 'http://identifiers.org/hgnc/HGNC:11998', 'is')
Annotation(PROTEASE, 'http://identifiers.org/pfam/PF00770', 'is')
Annotation(PROTEASE, 'http://identifiers.org/uniprot/P30202', 'is')
Annotation(PPM1D, 'http://identifiers.org/uniprot/O15297', 'is')
Annotation(PPM1D, 'http://identifiers.org/hgnc/HGNC:9277', 'is')
Annotation(ATR, 'http://identifiers.org/hgnc/HGNC:882', 'is')
Annotation(ATR, 'http://identifiers.org/uniprot/Q13535', 'is')
Annotation(MDM2, 'http://identifiers.org/uniprot/Q00987', 'is')
Annotation(MDM2, 'http://identifiers.org/hgnc/HGNC:6973', 'is')
