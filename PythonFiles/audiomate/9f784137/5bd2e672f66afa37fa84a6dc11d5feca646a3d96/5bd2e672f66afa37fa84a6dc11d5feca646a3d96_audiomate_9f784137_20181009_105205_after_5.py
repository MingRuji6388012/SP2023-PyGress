import unittest

import pytest

import audiomate
from audiomate.corpus import assets

from tests import resources


class CorpusViewTest(unittest.TestCase):
    def setUp(self):
        self.ds = resources.create_multi_label_corpus()

    def test_all_label_values(self):
        assert self.ds.all_label_values() == {'music', 'speech'}

    def test_label_count(self):
        assert self.ds.label_count() == {'music': 11, 'speech': 7}

    def test_stats(self):
        ds = audiomate.Corpus.load(resources.sample_corpus_path('default'), reader='default')
        stats = ds.stats()

        assert stats.min == pytest.approx(-1.0)
        assert stats.max == pytest.approx(0.99996948)
        assert stats.mean == pytest.approx(-0.00013355668)
        assert stats.var == pytest.approx(0.015060359)

    def test_stats_per_utterance(self):
        ds = audiomate.Corpus.load(resources.sample_corpus_path('default'), reader='default')
        stats = ds.stats_per_utterance()

        assert set(list(stats.keys())) == {'utt-1', 'utt-2', 'utt-3', 'utt-4', 'utt-5'}

        assert stats['utt-1'].min == pytest.approx(-1.0)
        assert stats['utt-1'].max == pytest.approx(0.99996948)
        assert stats['utt-1'].mean == pytest.approx(-0.00023601724)
        assert stats['utt-1'].var == pytest.approx(0.017326673)
        assert stats['utt-1'].num == 118240

        assert stats['utt-3'].min == pytest.approx(-0.92578125)
        assert stats['utt-3'].max == pytest.approx(0.99996948)
        assert stats['utt-3'].mean == pytest.approx(-0.00041901905)
        assert stats['utt-3'].var == pytest.approx(0.017659103)
        assert stats['utt-3'].num == 24000

    def test_label_duration(self):
        durations = self.ds.label_durations()

        assert durations['music'] == pytest.approx(44.0)
        assert durations['speech'] == pytest.approx(45.0)

    def test_duration(self):
        duration = self.ds.total_duration

        assert duration == pytest.approx(85.190375)

    def test_all_tokens(self):
        corpus = resources.create_dataset()
        assert corpus.all_tokens() == {'who', 'am', 'i', 'are', 'is', 'he', 'you', 'she', 'they'}

    def test_all_tokens_returns_only_from_selected_label_lists(self):
        corpus = resources.create_dataset()
        ll = assets.LabelList(idx='test', labels=[assets.Label('what can he do')])
        corpus.utterances['utt-1'].set_label_list(ll)

        target_lls = [audiomate.corpus.LL_WORD_TRANSCRIPT]
        expected_tokens = {'who', 'am', 'i', 'are', 'is', 'he', 'you', 'she', 'they'}
        assert corpus.all_tokens(label_list_ids=target_lls) == expected_tokens

    def test_all_tokens_with_custom_delimiter(self):
        corpus = resources.create_dataset()
        ll = assets.LabelList(idx='test', labels=[assets.Label('a, b, a, c')])
        corpus.utterances['utt-1'].set_label_list(ll)

        target_lls = ['test']
        expected_tokens = {'a', 'b', 'c'}
        assert corpus.all_tokens(delimiter=',', label_list_ids=target_lls) == expected_tokens
