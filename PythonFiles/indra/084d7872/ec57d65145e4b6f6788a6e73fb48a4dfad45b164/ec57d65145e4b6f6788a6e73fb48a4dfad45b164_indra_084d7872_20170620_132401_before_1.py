import pickle
from indra.statements import Agent, ModCondition
from indra.biopax import processor as bpc
from indra.biopax import pathway_commons_client as pcc

owl_pattern = '/home/bmg16/data/pathwaycommons/PathwayCommons9.%s.BIOPAX.owl'
dbs = ['psp', 'pid', 'reactome', 'kegg', 'panther']

for db in dbs:
    owl_file = owl_pattern % db
    print('Reading %s...' % owl_file)
    model = pcc.owl_to_model(owl_file)
    mf_class = bpc._bpimpl('ModificationFeature')

    objs = model.getObjects().toArray()

    agents = []
    for obj in objs:
        if not isinstance(obj, mf_class):
            continue
        try:
            res = bpc.BiopaxProcessor._extract_mod_from_feature(obj)
        except Exception as e:
            print('ERROR: ' + str(e))
            continue
        if not res:
            continue
        mod_type, residue, position = res
        if not residue or not position:
            continue
        er  = obj.getEntityFeatureOf()
        if not er:
            continue
        pe = er.getEntityReferenceOf().toArray()
        if not pe:
            continue
        protein = pe[0]
        name = bpc.BiopaxProcessor._get_element_name(protein)
        db_refs = bpc.BiopaxProcessor._get_db_refs(protein)
        agent = Agent(name, mods=[ModCondition(mod_type, residue, position)],
                      db_refs=db_refs)
        agents.append(agent)

    with open('pc_%s_modified_agents.pkl' % db, 'wb') as fh:
        pickle.dump(agents, fh)
