import json
from indra.statements import *
from indra.literature import id_lookup
from indra.databases import hgnc_client, uniprot_client, chebi_client

global_submitter = 'cure'

class IndexCardAssembler(object):
    def __init__(self, statements=None):
        if statements is None:
            self.statements =  []
        else:
            self.statements = statements
        self.cards = []

    def add_statements(self, statements):
        self.statements.extend(statements)

    def make_model(self):
        for stmt in self.statements:
            if isinstance(stmt, Modification):
                card = assemble_modification(stmt)
                if card is not None:
                    self.cards.append(card)
            if isinstance(stmt, SelfModification):
                card = assemble_selfmodification(stmt)
                if card is not None:
                    self.cards.append(card)
            elif isinstance(stmt, Complex):
                card = assemble_complex(stmt)
                if card is not None:
                    self.cards.append(card)
            else:
                continue

    def print_model(self):
        cards = [c.card for c in self.cards]
        # If there is only one card, print it as a single
        # card not as a list
        if len(cards) == 1:
            cards = cards[0]
        return json.dumps(cards, indent=1)

    def save_model(self, file_name='index_cards.json'):
        with open(file_name, 'wt') as fh:
            fh.write(self.print_model())

class IndexCard(object):
    def __init__(self):
        self.card  = {
            'pmc_id': None,
            'submitter': None,
            'interaction': {
                'negative_information': False,
                'interaction_type': None,
                'participant_a': {
                    'entity_type': None,
                    'entity_text': None,
                    'identifier': None
                    },
                'participant_b': {
                    'entity_type': None,
                    'entity_text': None,
                    'identifier': None
                    }
                }
            }

    def get_string(self):
        return json.dumps(self.card)

def assemble_complex(stmt):
    card = IndexCard()
    card.card['pmc_id'] = get_pmc_id(stmt)
    card.card['submitter'] = global_submitter
    card.card['evidence'] = get_evidence_text(stmt)
    card.card['interaction']['interaction_type'] = 'complexes_with'
    card.card['interaction'].pop('participant_b', None)
    # NOTE: fill out entity_text
    card.card['interaction']['participant_a']['entity_type'] = 'complex'
    card.card['interaction']['participant_a']['entity_text'] = ['']
    card.card['interaction']['participant_a'].pop('identifier', None)
    card.card['interaction']['participant_a']['entities'] = []
    for m in stmt.members:
        p = get_participant(m)
        card.card['interaction']['participant_a']['entities'].append(p)
    return card

def assemble_modification(stmt):
    card = IndexCard()
    card.card['pmc_id'] = get_pmc_id(stmt)
    card.card['submitter'] = global_submitter
    card.card['evidence'] = get_evidence_text(stmt)

    mod_type = stmt.__class__.__name__.lower()
    interaction = {}
    interaction['negative_information'] = False
    if mod_type.startswith('de'):
        interaction['interaction_type'] = 'removes_modification'
        mod_type = stmt.__class__.__name__.lower()[2:]
    else:
        interaction['interaction_type'] = 'adds_modification'
        mod_type = stmt.__class__.__name__.lower()

    interaction['modifications'] = [{
                'feature_type': 'modification_feature',
                'modification_type': mod_type,
                }]
    if stmt.position is not None:
        pos = int(stmt.position)
        interaction['modifications'][0]['location'] = pos
    if stmt.residue is not None:
        interaction['modifications'][0]['aa_code'] =  stmt.residue

    # If the statement is direct or there is no enzyme
    if get_is_direct(stmt) or stmt.enz is None:
        interaction['participant_a'] = get_participant(stmt.enz)
        interaction['participant_b'] = get_participant(stmt.sub)
        card.card['interaction'] = interaction
    # If the statement is indirect, we generate an index card:
    # SUB increases (GENERIC adds_modification ENZ)
    else:
        interaction['participant_a'] = get_participant(None)
        interaction['participant_b'] = get_participant(stmt.sub)
        card.card['interaction']['interaction_type'] = 'increases'
        card.card['interaction']['negative_information'] = False
        card.card['interaction']['participant_a'] = get_participant(stmt.enz)
        card.card['interaction']['participant_b'] = interaction

    return card

def assemble_selfmodification(stmt):
    card = IndexCard()
    card.card['pmc_id'] = get_pmc_id(stmt)
    card.card['submitter'] = global_submitter
    card.card['evidence'] = get_evidence_text(stmt)

    mod_type = stmt.__class__.__name__.lower()
    if mod_type.endswith('phosphorylation'):
        mod_type = 'phosphorylation'
    else:
        return None

    interaction = {}
    interaction['negative_information'] = False
    interaction['interaction_type'] = 'adds_modification'

    interaction['modifications'] = [{
                'feature_type': 'modification_feature',
                'modification_type': mod_type,
                }]
    if stmt.position is not None:
        pos = int(stmt.position)
        interaction['modifications'][0]['location'] = pos
    if stmt.residue is not None:
        interaction['modifications'][0]['aa_code'] =  stmt.residue

    # If the statement is direct or there is no enzyme
    if get_is_direct(stmt) or stmt.enz is None:
        interaction['participant_a'] = get_participant(stmt.enz)
        interaction['participant_b'] = get_participant(stmt.enz)
        card.card['interaction'] = interaction

    return card

def get_participant(agent):
    # Handle missing Agent as generic protein
    if agent is None:
        participant = {
            'entity_text': [''],
            'entity_type': 'protein',
            'identifier': 'GENERIC'
            }
        return participant
    # The Agent is not missing
    participant = {}
    participant['entity_text'] = [agent.name]
    hgnc_id = agent.db_refs.get('HGNC')
    uniprot_id = agent.db_refs.get('UP')
    chebi_id = agent.db_refs.get('CHEBI')
    # If HGNC grounding is available, that is the first choice
    if hgnc_id:
        uniprot_id = hgnc_client.get_uniprot_id(hgnc_id)
    if uniprot_id:
        uniprot_mnemonic = str(uniprot_client.get_mnemonic(uniprot_id))
        participant['identifier'] = 'UNIPROT:%s' % uniprot_mnemonic
        participant['entity_type'] = 'protein'
    elif chebi_id:
        pubchem_id = chebi_client.get_pubchem_id(chebi_id)
        participant['identifier'] = 'PUBCHEM:%s' % pubchem_id
        participant['entity_type'] = 'chemical'
    else:
        participant['identifier'] = ''
        participant['entity_type'] = 'protein'

    features = []
    not_features = []
    # Binding features
    for bc in agent.bound_conditions:
        feature = {
            'feature_type': 'binding_feature',
            'bound_to': {
                # NOTE: get type and identifier for bound to protein
                'entity_type': 'protein',
                'entity_text': [bc.agent.name],
                'identifier': ''
                }
            }
        if bc.is_bound:
            features.append(feature)
        else:
            not_features.append(feature)
    # Modification features
    for mc in agent.mods:
        feature = {
            'feature_type': 'modification_feature',
            'modification_type': mc.mod_type.lower(),
            }
        if mc.position is not None:
            pos = int(mc.position)
            feature['location'] = pos
        if mc.residue is not None:
            feature['aa_code'] = mc.residue
        if mc.is_modified:
            features.append(feature)
        else:
            not_features.append(feature)
    # Mutation features
    for mc in agent.mutations:
        feature = {
            'feature_type': 'mutation_feature',
            'from_aa': mc.residue_from,
            'to_aa': mc.residue_to
            }
        if mc.position is not None:
            pos = int(mc.position)
            feature['location'] = pos
        features.append(feature)
    if features:
        participant['features'] = features
    if not_features:
        participant['not_features'] = not_features
    return participant

def get_pmc_id(stmt):
    pmc_id = ''
    for ev in stmt.evidence:
        pmc_id = id_lookup(ev.pmid)['pmcid']
        if pmc_id is not None:
            if not pmc_id.startswith('PMC'):
                pmc_id = 'PMC' + pmc_id
        else:
            pmc_id = ''
    return pmc_id

def get_evidence_text(stmt):
    ev_txts = [ev.text for ev in stmt.evidence]
    return ev_txts

def get_is_direct(stmt):
    '''Returns true if there is evidence that the statement is a direct
    interaction. If any of the evidences associated with the statement
    indicates a direct interatcion then we assume the interaction
    is direct. If there is no evidence for the interaction being indirect
    then we default to direct.'''
    any_indirect = False
    for ev in stmt.evidence:
        if ev.epistemics.get('direct') is True:
            return True
        elif ev.epistemics.get('direct') is False:
            # This guarantees that we have seen at least
            # some evidence that the statement is indirect
            any_indirect = True
    if any_indirect:
        return False
    return True
