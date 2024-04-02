import abc
import collections


class CorpusView(metaclass=abc.ABCMeta):
    """
    This class defines the basic interface of a corpus. It is not meant to be instantiated directly.
    It only describes the methods for accessing data of the corpus.

    Notes:
        All paths to files should be held as absolute paths in memory.
    """

    @property
    @abc.abstractmethod
    def name(self):
        """ Return the name of the dataset (Equals basename of the path, if not None). """
        return 'undefined'

    #
    #   Files
    #

    @property
    @abc.abstractmethod
    def files(self):
        """
        Return the files in the corpus.

        Returns:
            dict: A dictionary containing :py:class:`pingu.corpus.assets.File` objects with the
            file-idx as key.
        """
        return {}

    @property
    def num_files(self):
        """ Return number of files. """
        return len(self.files)

    #
    #   Utterances
    #

    @property
    @abc.abstractmethod
    def utterances(self):
        """
        Return the utterances in the corpus.

        Returns:
            dict: A dictionary containing :py:class:`pingu.corpus.assets.Utterance` objects with the
            utterance-idx as key.
        """
        return {}

    @property
    def num_utterances(self):
        """ Return number of utterances. """
        return len(self.utterances)

    #
    #   Issuers
    #

    @property
    @abc.abstractmethod
    def issuers(self):
        """
        Return the issuers in the corpus.

        Returns:
            dict: A dictionary containing :py:class:`pingu.corpus.assets.Issuer` objects with the
            issuer-idx as key.
        """
        return {}

    @property
    def num_issuers(self):
        """ Return the number of issuers in the corpus. """
        return len(self.issuers)

    #
    #   Feature Container
    #

    @property
    @abc.abstractmethod
    def feature_containers(self):
        """
        Return the feature-containers in the corpus.

        Returns:
            dict: A dictionary containing :py:class:`pingu.corpus.assets.FeatureContainer` objects
            with the feature-idx as key.
        """
        return {}

    @property
    def num_feature_containers(self):
        """ Return the number of feature-containers in the corpus. """
        return len(self.feature_containers)

    #
    #   Subviews
    #

    @property
    def subviews(self):
        """
        Return the subviews of the corpus.

        Returns:
             dict: A dictionary containing :py:class:`pingu.corpus.Subview` objects with the subview-idx as key.
        """
        return {}

    @property
    def num_subviews(self):
        """ Return the number of subviews in the corpus. """
        return len(self.subviews)

    #
    #   Labels
    #

    def all_label_values(self, label_list_ids=None):
        """
        Return a set of all label-values occurring in this corpus.

        Args:
            label_list_ids (list): If not None, only labels from label-lists with an id contained in this list
                                   are considered.

        Returns:
             set: A set of distinct label-values.
        """
        values = set()

        for utterance in self.utterances.values():
            values = values.union(utterance.all_label_values(label_list_ids=label_list_ids))

        return values

    def label_count(self, label_list_ids=None):
        """
        Return a dictionary containing the number of times, every label-value in this corpus is occurring.

        Args:
            label_list_ids (list): If not None, only labels from label-lists with an id contained in this list
                                   are considered.

        Returns:
            dict: A dictionary containing the number of occurrences with the label-value as key.
        """
        count = collections.defaultdict(int)

        for utterance in self.utterances.values():
            for label_value, utt_count in utterance.label_count(label_list_ids=label_list_ids).items():
                count[label_value] += utt_count

        return count