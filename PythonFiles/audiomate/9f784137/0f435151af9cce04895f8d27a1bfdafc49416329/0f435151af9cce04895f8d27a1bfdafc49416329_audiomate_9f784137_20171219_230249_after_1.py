class Issuer(object):
    """
    The issuer represents a person, object or something that produced an utterance.
    Technically the issuer can be used to group utterances which came from the same source.

    Args:
        idx (str): An unique identifier for this issuer within a dataset.
        info (dict): Any additional infos for this issuer as dict.

    Attributes:
        utterances (list): List of utterances that this issuer owns.
    """

    def __init__(self, idx, info={}):
        self.idx = idx
        self.info = info
        self.utterances = set()
