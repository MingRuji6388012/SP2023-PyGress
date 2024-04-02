from __future__ import absolute_import, print_function, unicode_literals
from builtins import dict, str
import re
import logging
import objectpath
from indra.statements import Influence, Association, Concept, Evidence


logger = logging.getLogger('eidos')


class EidosProcessor(object):
    """This processor extracts INDRA Statements from Eidos JSON-LD output.

    Parameters
    ----------
    json_dict : dict
        A JSON dictionary containing the Eidos extractions in JSON-LD format.

    Attributes
    ----------
    tree : objectpath.Tree
        The objectpath Tree object representing the extractions.
    statements : list[indra.statements.Statement]
        A list of INDRA Statements that were extracted by the processor.
    """
    def __init__(self, json_dict):
        self.tree = objectpath.Tree(json_dict)
        self.statements = []
        self.extractions = []
        self.sentence_dict = {}
        self.entity_dict = {}
        self.coreferences = {}
        self._preprocess_extractions()

    def _preprocess_extractions(self):
        extractions = \
            self.tree.execute("$.extractions[(@.@type is 'Extraction')]")
        if not extractions:
            return
        # Listify for multiple reuse
        self.extractions = list(extractions)

        # Build a dictionary of entities and sentences by ID for convenient
        # lookup
        entities = [e for e in self.extractions if 'Concept' in
                    e.get('labels', [])]
        self.entity_dict = {entity['@id']: entity for entity in entities}

        documents = self.tree.execute("$.documents[(@.@type is 'Document')]")
        self.sentence_dict = {}
        for document in documents:
            sentences = document.get('sentences', [])
            self.sentence_dict = {sent['@id']: sent for sent in sentences}

        # Build a dictionary of coreferences
        for extraction in self.extractions:
            if 'Coreference' in extraction['labels']:
                reference = self.find_arg(extraction, 'reference')
                anchor = self.find_arg(extraction, 'anchor')
                self.coreferences[reference] = anchor

    def get_causal_relations(self):
        """Extract causal relations as Statements."""
        # Get the events that are labeled as directed and causal
        events = [e for e in self.extractions if
                  'DirectedRelation' in e['labels'] and
                  'Causal' in e['labels']]
        for event in events:
            # For now, just take the first source and first destination.
            # Later, might deal with hypergraph representation.
            subj_id = self.find_arg(event, 'source')
            obj_id = self.find_arg(event, 'destination')
            if subj_id is None or obj_id is None:
                continue

            # Resolve coreferences by ID
            subj_id = self.coreferences.get(subj_id, subj_id)
            obj_id = self.coreferences.get(obj_id, obj_id)

            # Get the actual entities
            subj = self.entity_dict[subj_id]
            obj = self.entity_dict[obj_id]

            subj_delta = {'adjectives': self.get_adjectives(subj),
                          'polarity': self.get_polarity(subj)}
            obj_delta = {'adjectives': self.get_adjectives(obj),
                         'polarity': self.get_polarity(obj)}

            evidence = self.get_evidence(event)

            st = Influence(self.get_concept(subj), self.get_concept(obj),
                           subj_delta, obj_delta, evidence=evidence)

            self.statements.append(st)

    def get_correlations(self):
        events = [e for e in self.extractions if
                  'UndirectedRelation' in e['labels'] and
                  'Correlation' in e['labels']]
        for event in events:
            # For now, just take the first source and first destination.
            # Later, might deal with hypergraph representation.
            arg_ids = self.find_args(event, 'argument')
            if len(arg_ids) != 2:
                logger.warning('Skipping correlation with not 2 arguments.')

            # Resolve coreferences by ID
            arg_ids = [self.coreferences.get(arg_id, arg_id)
                       for arg_id in arg_ids]

            # Get the actual entities
            args = [self.entity_dict[arg_id] for arg_id in arg_ids]
            # Make Concepts from the entities
            members = [self.get_concept(arg) for arg in args]
            # Get the evidence
            evidence = self.get_evidence(event)

            st = Association(members, evidence=evidence)
            self.statements.append(st)

    def get_evidence(self, event):
        """Return the Evidence object for the INDRA Statment."""
        provenance = event.get('provenance')

        # First try looking up the full sentence through provenance
        text = None
        time_annot = {}
        if provenance:
            sentence_tag = provenance[0].get('sentence')
            if sentence_tag and '@id' in sentence_tag:
                sentence_id = sentence_tag['@id']
                sentence = self.sentence_dict.get(sentence_id)
                if sentence is not None:
                    text = _sanitize(sentence['text'])
                # Get temporal constraints if available
                timexes = sentence.get('timexes', [])
                if timexes:
                    time_text = timexes[0].get('text')
                    constraint = timexes[0]['intervals'][0]
                    start = None if constraint['start'] == 'Undef' else \
                        constraint['start']
                    end = None if constraint['end'] == 'Undef' else \
                        constraint['end']
                    duration = constraint['duration']
                    time_annot = {'text': time_text, 'start': start,
                                  'end': end, 'duration': duration}

        # If that fails, we can still get the text of the event
        if text is None:
            text = _sanitize(event.get('text'))

        annotations = {'found_by': event.get('rule'),
                       'provenance' : provenance}
        if time_annot:
            annotations['time'] = time_annot
        ev = Evidence(source_api='eidos', text=text, annotations=annotations)
        return [ev]

    @staticmethod
    def get_polarity(entity):
        """Return the polarity of an entity."""
        # The first state corresponds to increase/decrease
        if 'states' not in entity:
            return None
        if entity['states'][0]['type'] == 'DEC':
            return -1
        elif entity['states'][0]['type'] == 'INC':
            return 1
        else:
            return None

    @staticmethod
    def get_adjectives(entity):
        """Return the adjectives of an entity."""
        if 'states' in entity:
            if 'modifiers' in entity['states'][0]:
                return [mod['text'] for mod in
                        entity['states'][0]['modifiers']]
            else:
                return []
        else:
            return []

    @staticmethod
    def get_groundings(entity):
        """Return groundings as db_refs for an entity."""
        def get_grounding_entries(grounding):
            if not grounding:
                return None

            entries = []
            for entry in grounding.get('values', []):
                ont_concept = entry.get('ontologyConcept')
                value = entry.get('value')
                if ont_concept is None or value is None:
                    continue
                entries.append((ont_concept, value))
            return entries

        # Save raw text and Eidos scored groundings as db_refs
        db_refs = {'TEXT': entity['text']}
        for g in entity.get('groundings', []):
            entries = get_grounding_entries(g)
            # Only add these groundings if there are actual values listed
            if entries:
                key = g['name'].upper()
                db_refs[key] = entries
        return db_refs

    @staticmethod
    def get_concept(entity):
        """Return Concept from an Eidos entity."""
        # Use the canonical name as the name of the Concept
        name = entity['canonicalName']
        db_refs = EidosProcessor.get_groundings(entity)
        concept = Concept(name, db_refs=db_refs)
        return concept

    @staticmethod
    def find_arg(event, arg_type):
        """Return ID of the first argument of a given type"""
        obj_ids = EidosProcessor.find_args(event, arg_type)
        if not obj_ids:
            return None
        else:
            return obj_ids[0]

    @staticmethod
    def find_args(event, arg_type):
        """Return IDs of all arguments of a given type"""
        args = event.get('arguments', {})
        obj_tags = [arg for arg in args if arg['type'] == arg_type]
        if obj_tags:
            return [o['value']['@id'] for o in obj_tags]
        else:
            return []


def _sanitize(text):
    """Return sanitized Eidos text field for human readability."""
    d = {'-LRB-': '(', '-RRB-': ')'}
    return re.sub('|'.join(d.keys()), lambda m: d[m.group(0)], text)