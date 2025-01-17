import abc

from audiomate.corpus import assets


class Encoder(metaclass=abc.ABCMeta):
    """
    Base class for an encoder. The goal of an encoder is to extract encoded targets for an utterance.
    The base class provides functionality to perform encoding for a full corpus.
    A concrete encoder just has to provide the method to encode a single utterance via ``encode_utterance``.

    For example for training a frame-classifier, an encoder extracts one-hot encoded vectors from a label-list.
    """

    def encode_corpus(self, corpus, output_path):
        """
        Encode all utterances of the given corpus and store them in a :class:`audiomate.corpus.assets.Container`.

        Args:
            corpus (Corpus): The corpus to process.
            output_path (str): The path to store the container with the encoded data.

        Returns:
            Container: The container with the encoded data.
        """

        container = assets.Container(output_path)
        container.open()

        for utterance in corpus.utterances.values():
            data = self.encode_utterance(utterance, corpus=corpus)
            container.set(utterance.idx, data)

        container.close()
        return container

    @abc.abstractmethod
    def encode_utterance(self, utterance, corpus=None):
        """
        Encode the given utterance.

        Args:
            utterance (Utterance): The utterance to encode.
            corpus (Corpus): The corpus the utterance is from.

        Returns:
            np.ndarray: Encoded data.
        """
        pass
