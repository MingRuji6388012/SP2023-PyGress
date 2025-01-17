import os
import json

import pingu
from pingu.formats import audacity
from pingu.utils import textfile
from . import base
from . import default

FILES_FILE_NAME = 'files.txt'
UTTERANCE_FILE_NAME = 'utterances.txt'
UTT_ISSUER_FILE_NAME = 'utt_issuers.txt'
LABEL_FILE = 'labels.txt'
FEAT_CONTAINER_FILE_NAME = 'features.txt'


def extract_meta_from_label_value(label):
    meta_match = default.META_PATTERN.match(label.value)

    if meta_match is not None:
        meta_json = meta_match.group(2)
        label.meta = json.loads(meta_json)
        label.value = meta_match.group(1)


class BroadcastReader(base.CorpusReader):
    """
    Reads corpora in the Broadcast format.
    """

    @classmethod
    def type(cls):
        return 'broadcast'

    def _check_for_missing_files(self, path):
        necessary_files = [FILES_FILE_NAME, UTTERANCE_FILE_NAME]
        missing_files = []

        for file_name in necessary_files:
            file_path = os.path.join(path, file_name)

            if not os.path.isfile(file_path):
                missing_files.append(file_name)

        return missing_files

    def _load(self, path):
        file_path = os.path.join(path, FILES_FILE_NAME)
        utt_issuer_path = os.path.join(path, UTT_ISSUER_FILE_NAME)
        utterance_path = os.path.join(path, UTTERANCE_FILE_NAME)
        feat_path = os.path.join(path, FEAT_CONTAINER_FILE_NAME)

        corpus = pingu.Corpus(path=path)

        default.DefaultReader.read_files(file_path, corpus)
        utt_id_to_issuer = default.DefaultReader.read_utt_to_issuer_mapping(utt_issuer_path, corpus)
        default.DefaultReader.read_utterances(utterance_path, corpus, utt_id_to_issuer)
        BroadcastReader.read_labels(path, corpus)
        default.DefaultReader.read_feature_containers(feat_path, corpus)

        return corpus

    @staticmethod
    def read_labels(path, corpus):
        label_reference_file = os.path.join(path, LABEL_FILE)
        label_references = textfile.read_separated_lines(label_reference_file, separator=' ', max_columns=3)

        for record in label_references:
            utt_idx = record[0]
            label_path = os.path.join(path, record[1])
            label_idx = None

            if len(record) > 2:
                label_idx = record[2]

            ll = audacity.read_label_list(label_path)
            ll.idx = label_idx
            ll.apply(extract_meta_from_label_value)

            corpus.utterances[utt_idx].set_label_list(ll)
