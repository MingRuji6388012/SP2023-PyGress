import os
import tempfile

import pingu
from pingu.corpus import assets
from pingu.corpus.subset import subview


def sample_voxforge_response():
    with open(os.path.join(os.path.dirname(__file__), 'voxforge_response.html')) as f:
        return f.read()


def sample_voxforge_file_path():
    return os.path.join(os.path.dirname(__file__), 'voxforge_sample.tgz')


def dummy_wav_path_and_name():
    name = 'test.wav'
    return os.path.join(os.path.dirname(__file__), name), name


def sample_default_ds_path():
    return os.path.join(os.path.dirname(__file__), 'default_ds')


def sample_broadcast_ds_path():
    return os.path.join(os.path.dirname(__file__), 'broadcast_ds')


def sample_gtzan_ds_path():
    return os.path.join(os.path.dirname(__file__), 'gtzan_ds')


def sample_esc50_ds_path():
    return os.path.join(os.path.dirname(__file__), 'esc50_ds')


def sample_kaldi_ds_path():
    return os.path.join(os.path.dirname(__file__), 'kaldi_ds')


def sample_musan_ds_path():
    return os.path.join(os.path.dirname(__file__), 'musan_ds')


def sample_speech_commands_ds_path():
    return os.path.join(os.path.dirname(__file__), 'speech_commands_ds')


def sample_tuda_ds_path():
    return os.path.join(os.path.dirname(__file__), 'tuda_ds')


def get_wav_folder():
    return os.path.join(os.path.dirname(__file__), 'wav_files')


def get_wav_file_path(name):
    return os.path.join(get_wav_folder(), name)


def get_feat_container_path():
    return os.path.join(os.path.dirname(__file__), 'feat_container')


def create_dataset():
    temp_path = tempfile.mkdtemp()

    ds = pingu.Corpus(temp_path)

    wav_1_path = get_wav_file_path('wav_1.wav')
    wav_2_path = get_wav_file_path('wav_2.wav')
    wav_3_path = get_wav_file_path('wav_3.wav')
    wav_4_path = get_wav_file_path('wav_4.wav')

    file_1 = ds.new_file(wav_1_path, file_idx='wav-1')
    file_2 = ds.new_file(wav_2_path, file_idx='wav_2')
    file_3 = ds.new_file(wav_3_path, file_idx='wav_3')
    file_4 = ds.new_file(wav_4_path, file_idx='wav_4')

    issuer_1 = ds.new_issuer('spk-1')
    issuer_2 = ds.new_issuer('spk-2')
    issuer_3 = ds.new_issuer('spk-3')

    utt_1 = ds.new_utterance('utt-1', file_1.idx, issuer_idx=issuer_1.idx)
    utt_2 = ds.new_utterance('utt-2', file_2.idx, issuer_idx=issuer_1.idx)
    utt_3 = ds.new_utterance('utt-3', file_3.idx, issuer_idx=issuer_2.idx, start=0, end=1.5)
    utt_4 = ds.new_utterance('utt-4', file_3.idx, issuer_idx=issuer_2.idx, start=1.5, end=2.5)
    utt_5 = ds.new_utterance('utt-5', file_4.idx, issuer_idx=issuer_3.idx)

    utt_1.set_label_list(assets.LabelList('default', labels=[assets.Label('who am i')]))
    utt_2.set_label_list(assets.LabelList('default', labels=[assets.Label('who are you', meta={'a': 'hey', 'b': 2})]))
    utt_3.set_label_list(assets.LabelList('default', labels=[assets.Label('who is he')]))
    utt_4.set_label_list(assets.LabelList('default', labels=[assets.Label('who are they')]))
    utt_5.set_label_list(assets.LabelList('default', labels=[assets.Label('who is she')]))

    train_filter = subview.MatchingUtteranceIdxFilter(utterance_idxs={'utt-1', 'utt-2', 'utt-3'})
    sv_train = subview.Subview(ds, filter_criteria=[train_filter])

    dev_filter = subview.MatchingUtteranceIdxFilter(utterance_idxs={'utt-4', 'utt-5'})
    sv_dev = subview.Subview(ds, filter_criteria=[dev_filter])

    ds.import_subview('train', sv_train)
    ds.import_subview('dev', sv_dev)

    ds.new_feature_container('mfcc', '/some/dummy/path')
    ds.new_feature_container('mel', '/some/dummy/path_mel')

    return ds


def create_multi_label_corpus():
    ds = pingu.Corpus()

    wav_1_path = get_wav_file_path('wav_1.wav')
    wav_2_path = get_wav_file_path('wav_2.wav')
    wav_3_path = get_wav_file_path('wav_3.wav')
    wav_4_path = get_wav_file_path('wav_4.wav')

    file_1 = ds.new_file(wav_1_path, file_idx='wav-1')
    file_2 = ds.new_file(wav_2_path, file_idx='wav_2')
    file_3 = ds.new_file(wav_3_path, file_idx='wav_3')
    file_4 = ds.new_file(wav_4_path, file_idx='wav_4')

    issuer_1 = ds.new_issuer('spk-1')
    issuer_2 = ds.new_issuer('spk-2')
    issuer_3 = ds.new_issuer('spk-3')

    utt_1 = ds.new_utterance('utt-1', file_1.idx, issuer_idx=issuer_1.idx)
    utt_2 = ds.new_utterance('utt-2', file_2.idx, issuer_idx=issuer_1.idx)
    utt_3 = ds.new_utterance('utt-3', file_3.idx, issuer_idx=issuer_2.idx, start=0, end=15)
    utt_4 = ds.new_utterance('utt-4', file_3.idx, issuer_idx=issuer_2.idx, start=15, end=25)
    utt_5 = ds.new_utterance('utt-5', file_3.idx, issuer_idx=issuer_2.idx, start=25, end=40)
    utt_6 = ds.new_utterance('utt-6', file_4.idx, issuer_idx=issuer_3.idx, start=0, end=15)
    utt_7 = ds.new_utterance('utt-7', file_4.idx, issuer_idx=issuer_3.idx, start=15, end=25)
    utt_8 = ds.new_utterance('utt-8', file_4.idx, issuer_idx=issuer_3.idx, start=25, end=40)

    utt_1.set_label_list(assets.LabelList(labels=[
        assets.Label('music', 0, 5),
        assets.Label('speech', 5, 12),
        assets.Label('music', 13, 15)
    ]))

    utt_2.set_label_list(assets.LabelList(labels=[
        assets.Label('music', 0, 5),
        assets.Label('speech', 5, 12),
        assets.Label('music', 13, 15)
    ]))

    utt_3.set_label_list(assets.LabelList(labels=[
        assets.Label('music', 0, 1),
        assets.Label('speech', 2, 6)
    ]))

    utt_4.set_label_list(assets.LabelList(labels=[
        assets.Label('music', 0, 5),
        assets.Label('speech', 5, 12),
        assets.Label('music', 13, 15)
    ]))

    utt_5.set_label_list(assets.LabelList(labels=[
        assets.Label('speech', 0, 7)
    ]))

    utt_6.set_label_list(assets.LabelList(labels=[
        assets.Label('music', 0, 5),
        assets.Label('speech', 5, 12),
        assets.Label('music', 13, 15)
    ]))

    utt_7.set_label_list(assets.LabelList(labels=[
        assets.Label('music', 0, 5),
        assets.Label('speech', 5, 11)
    ]))

    utt_8.set_label_list(assets.LabelList(labels=[
        assets.Label('music', 0, 10)
    ]))

    train_filter = subview.MatchingUtteranceIdxFilter(utterance_idxs={'utt-4', 'utt-5', 'utt-6'})
    sv_train = subview.Subview(ds, filter_criteria=[train_filter])

    dev_filter = subview.MatchingUtteranceIdxFilter(utterance_idxs={'utt-7', 'utt-8'})
    sv_dev = subview.Subview(ds, filter_criteria=[dev_filter])

    ds.import_subview('train', sv_train)
    ds.import_subview('dev', sv_dev)

    ds.new_feature_container('mfcc', '/some/dummy/path/secondmfcc')
    ds.new_feature_container('energy', '/some/dummy/path/energy')

    return ds


def create_single_label_corpus():
    ds = pingu.Corpus()

    wav_1_path = get_wav_file_path('wav_1.wav')
    wav_2_path = get_wav_file_path('wav_2.wav')
    wav_3_path = get_wav_file_path('wav_3.wav')
    wav_4_path = get_wav_file_path('wav_4.wav')

    file_1 = ds.new_file(wav_1_path, file_idx='wav-1')
    file_2 = ds.new_file(wav_2_path, file_idx='wav_2')
    file_3 = ds.new_file(wav_3_path, file_idx='wav_3')
    file_4 = ds.new_file(wav_4_path, file_idx='wav_4')

    issuer_1 = ds.new_issuer('spk-1')
    issuer_2 = ds.new_issuer('spk-2')
    issuer_3 = ds.new_issuer('spk-3')

    utt_1 = ds.new_utterance('utt-1', file_1.idx, issuer_idx=issuer_1.idx)
    utt_2 = ds.new_utterance('utt-2', file_2.idx, issuer_idx=issuer_1.idx)
    utt_3 = ds.new_utterance('utt-3', file_3.idx, issuer_idx=issuer_2.idx, start=0, end=15)
    utt_4 = ds.new_utterance('utt-4', file_3.idx, issuer_idx=issuer_2.idx, start=15, end=25)
    utt_5 = ds.new_utterance('utt-5', file_3.idx, issuer_idx=issuer_2.idx, start=25, end=40)
    utt_6 = ds.new_utterance('utt-6', file_4.idx, issuer_idx=issuer_3.idx, start=0, end=15)
    utt_7 = ds.new_utterance('utt-7', file_4.idx, issuer_idx=issuer_3.idx, start=15, end=25)
    utt_8 = ds.new_utterance('utt-8', file_4.idx, issuer_idx=issuer_3.idx, start=25, end=40)

    utt_1.set_label_list(assets.LabelList(labels=[
        assets.Label('music')
    ]))

    utt_2.set_label_list(assets.LabelList(labels=[
        assets.Label('music')
    ]))

    utt_3.set_label_list(assets.LabelList(labels=[
        assets.Label('speech')
    ]))

    utt_4.set_label_list(assets.LabelList(labels=[
        assets.Label('music')
    ]))

    utt_5.set_label_list(assets.LabelList(labels=[
        assets.Label('speech')
    ]))

    utt_6.set_label_list(assets.LabelList(labels=[
        assets.Label('music')
    ]))

    utt_7.set_label_list(assets.LabelList(labels=[
        assets.Label('speech')
    ]))

    utt_8.set_label_list(assets.LabelList(labels=[
        assets.Label('music')
    ]))

    return ds
