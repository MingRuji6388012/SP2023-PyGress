import collections
import heapq
from functools import total_ordering


@total_ordering
class Label(object):
    """
    Represents a label that describes some part of an utterance.

    Parameters:
        value (str): The text of the label.
        start (float): Start of the label within the utterance in seconds. (default: 0)
        end (float): End of the label within the utterance in seconds. (default: -1) (-1 defines
                     the end of the utterance)
        label_list (LabelList): The label-list this label is belonging to.
    """
    __slots__ = ['value', 'start', 'end', 'label_list']

    def __init__(self, value, start=0, end=-1):
        self.value = value
        self.start = start
        self.end = end
        self.label_list = None

    def __eq__(self, other):
        return (self.start, self.end, self.value.lower()) == (other.start, other.end, other.value.lower())

    def __lt__(self, other):
        self_end = float('inf') if self.end == -1 else self.end
        other_end = float('inf') if other.end == -1 else other.end

        return (self.start, self_end, self.value.lower()) < (other.start, other_end, other.value.lower())

    def __repr__(self) -> str:
        return 'Label({}, {}, {})'.format(self.value, self.start, self.end)


class LabelList(object):
    """
    Represents a list of labels which describe an utterance.
    An utterance can have multiple label-lists.

    Args:
        idx (str): An unique identifier for the label-list within a corpus for one utterance.
        labels (list): The list containing the :py:class:`pingu.corpus.assets.Label`.

    Attributes:
        utterance (Utterance): The utterance this label-list is belonging to.

    Example::

        >>> label_list = LabelList(idx='transcription', labels=[
        >>>     Label('this', 0, 2),
        >>>     Label('is', 2, 4),
        >>>     Label('timmy', 4, 8)
        >>> ])
    """

    __slots__ = ['idx', 'labels', 'utterance']

    def __init__(self, idx='default', labels=[]):
        self.idx = idx
        self.utterance = None

        self.labels = []
        self.extend(labels)

    def append(self, label):
        """
        Add a label to the end of the list.

        Args:
            label (Label): The label to add.
        """
        label.label_list = self
        self.labels.append(label)

    def extend(self, labels):
        """
        Add a list of labels to the end of the list.

        Args:
            labels (list): Labels to add.
        """
        for label in labels:
            self.append(label)

    def ranges(self, yield_ranges_without_labels=False, include_labels=None):
        """
        Generate all ranges of the label-list. A range is defined as a part of the label-list for
        which the same labels are defined.

        Args:
            yield_ranges_without_labels (bool): If True also yields ranges for which no labels are
                                                defined.
            include_labels (list): If not empty, only the label values in the list will be
                                   considered.

        Returns:
            generator: A generator which yields one range (tuple start/end/list-of-labels) at a
                       time.

        Example:
            >>> ll = LabelList(labels=[
            >>>     Label('a', 3.2, 4.5),
            >>>     Label('b', 5.1, 8.9),
            >>>     Label('c', 7.2, 10.5),
            >>>     Label('d', 10.5, 14)
            >>> ])
            >>> ranges = ll.ranges()
            >>> next(ranges)
            (3.2, 4.5, [<pingu.corpus.assets.label.Label at 0x1090527c8>])
            >>> next(ranges)
            (4.5, 5.1, [])
            >>> next(ranges)
            (5.1, 7.2, [<pingu.corpus.assets.label.Label at 0x1090484c8>])
        """

        # all label start events
        events = [(l.start, 1, l) for l in self.labels]
        labels_to_end = False
        heapq.heapify(events)

        current_range_labels = []
        current_range_start = -123

        while len(events) > 0:
            next_event = heapq.heappop(events)
            label = next_event[2]

            # Return current range if its not the first event and not the same time as the previous
            # event
            if -1 < current_range_start < next_event[0]:

                if len(current_range_labels) > 0 or yield_ranges_without_labels:
                    yield (current_range_start, next_event[0], list(current_range_labels))

            # Update labels and add the "end" event
            if next_event[1] == 1:
                if include_labels is None or label.value in include_labels:
                    current_range_labels.append(label)

                    if label.end == -1:
                        labels_to_end = True
                    else:
                        heapq.heappush(events, (label.end, -1, label))
            else:
                current_range_labels.remove(label)

            current_range_start = next_event[0]

        if labels_to_end and len(current_range_labels) > 0:
            yield (current_range_start, -1, list(current_range_labels))

    def label_values(self):
        """
        Return a list of all occuring label values.

        Returns:
            list: Lexicographically sorted list (str) of label values.

        Example:
            >>> ll = LabelList(labels=[
            >>>     Label('a', 3.2, 4.5),
            >>>     Label('b', 5.1, 8.9),
            >>>     Label('c', 7.2, 10.5),
            >>>     Label('d', 10.5, 14),
            >>>     Label('d', 15, 18)
            >>> ])
            >>> ll.label_values()
            ['a', 'b', 'c', 'd']
        """

        all_labels = set([l.value for l in self])
        return sorted(all_labels)

    def label_count(self):
        """
        Return for each label the number of occurrences within the list.

        Returns:
            dict: A dictionary container for every label-value (key) the number of occurrences
                  (value).

        Example:
            >>> ll = LabelList(labels=[
            >>>     Label('a', 3.2, 4.5),
            >>>     Label('b', 5.1, 8.9),
            >>>     Label('a', 7.2, 10.5),
            >>>     Label('b', 10.5, 14),
            >>>     Label('a', 15, 18)
            >>> ])
            >>> ll.label_count()
            {'a': 3 'b': 2}
        """

        occurrences = collections.defaultdict(int)

        for label in self:
            occurrences[label.value] += 1

        return occurrences

    def apply(self, fn):
        """
        Apply the given function `fn` to every label in this label list. `fn` is a function of one argument that
        receives the current label which can then be edited in place.

        Args:
            fn (func): Function to apply to every label

        Example:
            >>> ll = LabelList(labels=[
            ...     Label('a_label', 1.0, 2.0),
            ...     Label('another_label', 2.0, 3.0)
            ... ])
            >>> def shift_labels(label):
            ...     label.start += 1.0
            ...     label.end += 1.0
            ...
            >>> ll.apply(shift_labels)
            >>> ll.labels
            [Label(a_label, 2.0, 3.0), Label(another_label, 3.0, 4.0)]
        """
        for label in self.labels:
            fn(label)

    def __getitem__(self, item):
        return self.labels.__getitem__(item)

    def __iter__(self):
        return self.labels.__iter__()

    def __len__(self):
        return self.labels.__len__()