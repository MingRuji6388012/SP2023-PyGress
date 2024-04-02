"""This REST service allows real-time curation and belief updates for
a corpus of INDRA Statements."""
import yaml
import pickle
import logging
import argparse
from flask import Flask, request, jsonify, abort, Response
from indra.belief import BeliefEngine
from indra.statements import stmts_from_json_file
from indra.belief.wm_scorer import get_eidos_bayesian_scorer
from indra.preassembler.hierarchy_manager import YamlHierarchyManager
from indra.preassembler.make_eidos_hume_ontologies import eidos_ont_url, \
    load_yaml_from_url, rdf_graph_from_yaml


logger = logging.getLogger('live_curation')
app = Flask(__name__)
corpora = {}


class Corpus(object):
    """Represent a corpus of statements with curation.

    Parameters
    ----------
    statements : list[indra.statement.Statement]
        A list of INDRA Statements to embed in the corpus.

    Attributes
    ----------
    statements : dict
        A dict of INDRA Statements keyed by UUID.
    curations : dict
        A dict keeping track of the curations submitted so far for Statement
        UUIDs in the corpus.
    """
    def __init__(self, statements):
        self.statements = {st.uuid: st for st in statements}
        self.curations = {}

    def __str__(self):
        return 'Corpus(%s -> %s)' % (str(self.statements), str(self.curations))

    def __repr__(self):
        return str(self)


class InvalidCorpusError(Exception):
    pass


class LiveCurator(object):
    """Class coordinating the real-time curation of a corpus of Statements.

    Parameters
    ----------
    scorer : indra.belief.BeliefScorer
        A scorer object to use for the curation
    corpora : dict[str, Corpus]
        A dictionary mapping corpus IDs to Corpus objects.
    """

    def __init__(self, scorer=None, corpora=None):
        self.scorer = scorer if scorer else get_eidos_bayesian_scorer()
        self.corpora = corpora if corpora else {}

    # TODO: generalize this to other kinds of scorers
    def reset_scorer(self):
        """Reset the scorer used for couration."""
        self.scorer = get_eidos_bayesian_scorer()
        for corpus_id, corpus in self.corpora.items():
            corpus.curations = {}

    def get_corpus(self, corpus_id):
        """Return a corpus given an ID.

        If the corpus ID cannot be found, an InvalidCorpusError is raised.

        Parameters
        ----------
        corpus_id : str
            The ID of the corpus to return.

        Returns
        -------
        Corpus
            The corpus with the given ID.
        """
        try:
            corpus = self.corpora[corpus_id]
            return corpus
        except KeyError:
            raise InvalidCorpusError

    def submit_curation(self, corpus_id, curations):
        """Submit correct/incorrect curations fo a given corpus.

        Parameters
        ----------
        corpus_id : str
            The ID of the corpus to which the curations apply.
        curations : dict
            A dict of curations with keys corresponding to Statement UUIDs and
            values corresponding to correct/incorrect feedback.
        """
        corpus = self.get_corpus(corpus_id)
        # Start tabulating the curation counts
        prior_counts = {}
        subtype_counts = {}
        # Take each curation from the input
        for uuid, correct in curations.items():
            # Save the curation in the corpus
            # TODO: handle already existing curation
            stmt = corpus.statements.get(uuid)
            if stmt is None:
                logger.warning('%s is not in the corpus.' % uuid)
                continue
            corpus.curations[uuid] = correct
            # Now take all the evidences of the statement and assume that
            # they follow the correctness of the curation and contribute to
            # counts for their sources
            for ev in stmt.evidence:
                # Make the index in the curation count list
                idx = 0 if correct else 1
                extraction_rule = ev.annotations.get('found_by')
                # If there is no extraction rule then we just score the source
                if not extraction_rule:
                    try:
                        prior_counts[ev.source_api][idx] += 1
                    except KeyError:
                        prior_counts[ev.source_api] = [0, 0]
                        prior_counts[ev.source_api][idx] += 1
                # Otherwise we score the specific extraction rule
                else:
                    try:
                        subtype_counts[ev.source_api][extraction_rule][idx] \
                            += 1
                    except KeyError:
                        if ev.source_api not in subtype_counts:
                            subtype_counts[ev.source_api] = {}
                        subtype_counts[ev.source_api][extraction_rule] = [0, 0]
                        subtype_counts[ev.source_api][extraction_rule][idx] \
                            += 1
        # Finally, we update the scorer with the new curation counts
        self.scorer.update_counts(prior_counts, subtype_counts)

    def update_beliefs(self, corpus_id):
        """Return updated belief scores for a given corpus.

        Parameters
        ----------
        corpus_id : str
            The ID of the corpus for which beliefs are to be updated.

        Returns
        -------
        dict
            A dictionary of belief scores with keys corresponding to Statement
            UUIDs and values to new belief scores.
        """
        corpus = self.get_corpus(corpus_id)
        be = BeliefEngine(self.scorer)
        stmts = list(corpus.statements.values())
        be.set_prior_probs(stmts)
        # Here we set beliefs based on actual curation
        for uuid, correct in corpus.curations.items():
            stmt = corpus.statements.get(uuid)
            if stmt is None:
                logger.warning('%s is not in the corpus.' % uuid)
                continue
            stmt.belief = correct
        belief_dict = {st.uuid: st.belief for st in stmts}
        return belief_dict


# From here on, a Flask app built around a LiveCurator is implemented

def _make_un_ontology():
    return YamlHierarchyManager(load_yaml_from_url(eidos_ont_url),
                                rdf_graph_from_yaml)

curator = LiveCurator(corpora=corpora)
ont_manager = _make_un_ontology()


@app.route('/reset_curation', methods=['POST'])
def reset_curation():
    """Reset the curations submitted until now."""
    if request.json is None:
        abort(Response('Missing application/json header.', 415))
    curator.reset_scorer()
    return jsonify({})


@app.route('/submit_curation', methods=['POST'])
def submit_curation():
    """Submit curations for a given corpus.

    The submitted curations are handled to update the probability model but
    there is no return value here. The update_belief function can be called
    separately to calculate update belief scores.

    Parameters
    ----------
    corpus_id : str
        The ID of the corpus for which the curation is submitted.
    curations : dict
        A set of curations where each key is a Statement UUID in the given
        corpus and each key is 0 or 1 with 0 corresponding to incorrect and
        1 corresponding to correct.
    """
    if request.json is None:
        abort(Response('Missing application/json header.', 415))
    # Get input parameters
    corpus_id = request.json.get('corpus_id')
    curations = request.json.get('curations', {})
    try:
        curator.submit_curation(corpus_id, curations)
    except InvalidCorpusError:
        abort(Response('The corpus_id "%s" is unknown.' % corpus_id, 400))
        return
    return jsonify({})


@app.route('/update_beliefs', methods=['POST'])
def update_beliefs():
    """Return updated beliefs based on current probability model."""
    if request.json is None:
        abort(Response('Missing application/json header.', 415))
    # Get input parameters
    corpus_id = request.json.get('corpus_id')
    try:
        belief_dict = curator.update_beliefs(corpus_id)
    except InvalidCorpusError:
        abort(Response('The corpus_id "%s" is unknown.' % corpus_id, 400))
        return
    return jsonify(belief_dict)


@app.route('/add_ontology_entry', methods=['POST'])
def add_ontology_entry():
    if request.json is None:
        abort(Response('Missing application/json header.', 415))

    # Get input parameters
    entry = request.json.get('entry')
    examples = request.json.get('examples', [])
    # Add the entry and examples to the in-memory representation
    # of the onotology
    ont_manager.add_entry(entry, examples)
    return jsonify({})


@app.route('/reset_ontology', methods=['POST'])
def reset_ontology():
    if request.json is None:
        abort(Response('Missing application/json header.', 415))

    # Reload the original ontology
    global ont_manager
    ont_manager = _make_un_ontology()

    return jsonify({})


@app.route('/update_groundings', methods=['POST'])
def update_groundings():
    if request.json is None:
        abort(Response('Missing application/json header.', 415))

    # Get input parameters
    corpus_id = request.json.get('corpus_id')

    # Send the latest ontology and list of concept texts to Eidos
    yaml_str = yaml.dump(ont_manager.yaml_root)
    concepts = []
    for uuid, stmt in corpora.get(corpus_id).items():
        for concept in stmt.agent_list():
            concept_txt = concept.db_refs['TEXT']
            concepts.append(concept_txt)
    # TODO: call Eidos here with yaml_str and concepts to get
    # actual groundings
    groundings = []
    # Update the corpus with new groundings
    


    return jsonify({})


@app.route('/run_assembly', methods=['POST'])
def run_assembly():
    if request.json is None:
        abort(Response('Missing application/json header.', 415))

    # Get input parameters
    corpus_id = request.json.get('corpus_id')

    # Run preassembly

    # Return assembled statement corpus
    return jsonify({})


if __name__ == '__main__':
    # Process arguments
    parser = argparse.ArgumentParser(
        description='Choose a corpus for live curation.')
    parser.add_argument('--json')
    parser.add_argument('--pickle')
    parser.add_argument('--corpus_id', default='1')
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', default=8001, type=int)
    args = parser.parse_args()

    # Load the corpus
    if args.json:
        stmts = stmts_from_json_file(args.json)
    elif args.pickle:
        with open(args.pickle, 'rb') as fh:
            stmts = pickle.load(fh)
    logger.info('Loaded corpus %s with %d statements.' %
                (args.corpus_id, len(stmts)))
    curator.corpora[args.corpus_id] = Corpus(stmts)

    # Run the app
    app.run(host=args.host, port=args.port)