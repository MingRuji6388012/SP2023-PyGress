import unittest

import pytest

from pingu.corpus import assets

from tests import resources


class FeatureContainerTest(unittest.TestCase):
    def setUp(self):
        self.container = assets.FeatureContainer(resources.get_feat_container_path())
        self.container.open()

    def tearDown(self):
        self.container.close()

    def test_frame_size(self):
        assert self.container.frame_size == 400

    def test_hop_size(self):
        assert self.container.hop_size == 160

    def test_sampling_rate(self):
        assert self.container.sampling_rate == 16000

    def test_stats_per_utterance(self):
        utt_stats = self.container.stats_per_utterance()

        assert utt_stats['utt-1'].min == pytest.approx(0.0071605651933048797)
        assert utt_stats['utt-1'].max == pytest.approx(0.9967182746569494)
        assert utt_stats['utt-1'].mean == pytest.approx(0.51029100520776705)
        assert utt_stats['utt-1'].var == pytest.approx(0.079222738766221268)
        assert utt_stats['utt-1'].num == 100

        assert utt_stats['utt-2'].min == pytest.approx(0.01672865642756316)
        assert utt_stats['utt-2'].max == pytest.approx(0.99394433783429104)
        assert utt_stats['utt-2'].mean == pytest.approx(0.46471979908661543)
        assert utt_stats['utt-2'].var == pytest.approx(0.066697466410977804)
        assert utt_stats['utt-2'].num == 65

        assert utt_stats['utt-3'].min == pytest.approx(0.014999482706963607)
        assert utt_stats['utt-3'].max == pytest.approx(0.99834417857609881)
        assert utt_stats['utt-3'].mean == pytest.approx(0.51042690965262705)
        assert utt_stats['utt-3'].var == pytest.approx(0.071833200069641057)
        assert utt_stats['utt-3'].num == 220

    def test_stats_per_utterance_not_open(self):
        self.container.close()

        with pytest.raises(ValueError):
            self.container.stats_per_utterance()

    def test_stats(self):
        stats = self.container.stats()

        assert stats.min == pytest.approx(0.0071605651933048797)
        assert stats.max == pytest.approx(0.99834417857609881)
        assert stats.mean == pytest.approx(0.50267482489606408)
        assert stats.var == pytest.approx(0.07317811077366114)

    def test_stats_not_open(self):
        self.container.close()

        with pytest.raises(ValueError):
            self.container.stats()
