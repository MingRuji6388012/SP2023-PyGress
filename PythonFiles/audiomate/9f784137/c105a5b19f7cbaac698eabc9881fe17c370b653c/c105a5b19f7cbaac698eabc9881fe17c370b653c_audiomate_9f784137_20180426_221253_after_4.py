import unittest

import numpy as np

from pingu.corpus.utils import label_encoding
from pingu.utils import units

from tests import resources


class TestFrameOneHotEncoder(unittest.TestCase):

    def test_encode_full_utterance(self):
        ds = resources.create_multi_label_corpus()
        enc = label_encoding.FrameOneHotEncoder(['music', 'speech', 'noise'],
                                                frame_settings=units.FrameSettings(32000, 16000),
                                                sr=16000)

        actual = enc.encode(ds.utterances['utt-6'])
        expected = np.array([
            [1, 0, 0],
            [1, 0, 0],
            [1, 0, 0],
            [1, 0, 0],
            [1, 1, 0],
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 0],
            [1, 0, 0],
            [1, 0, 0],
        ]).astype(np.float32)

        assert np.array_equal(expected, actual)
