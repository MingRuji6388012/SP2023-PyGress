import pytest

import boost_histogram as bh
from boost_histogram.axis import regular

import numpy as np
from numpy.testing import assert_array_equal, assert_allclose

STORAGES = (bh.storage.int, bh.storage.double, bh.storage.unlimited)
DTYPES = (np.float64, np.float32, np.int64, np.int32)

bins = 100
ranges = (-1, 1)
bins = np.asarray(bins).astype(np.int64)
ranges = np.asarray(ranges).astype(np.float64)

edges = np.linspace(ranges[0], ranges[1], bins + 1)

np.random.seed(42)
vals_core = np.random.normal(size=[100000])
vals = {t: vals_core.astype(t) for t in DTYPES}

answer = {t: np.histogram(vals[t], bins=bins, range=ranges)[0] for t in DTYPES}


@pytest.mark.benchmark(group="1d-fills")
@pytest.mark.parametrize("dtype", vals)
def test_numpy_1d(benchmark, dtype):
    result, _ = benchmark(np.histogram, vals[dtype], bins=bins, range=ranges)
    assert_array_equal(result, answer[dtype])


def make_and_run_hist(flow, storage, vals):
    histo = bh.histogram(
        regular(bins, *ranges, underflow=flow, overflow=flow), storage=storage()
    )
    histo.fill(vals)
    return histo.view()


@pytest.mark.benchmark(group="1d-fills")
@pytest.mark.parametrize("flow", (True, False), ids=["flow", "noflow"])
@pytest.mark.parametrize("dtype", vals)
@pytest.mark.parametrize("storage", STORAGES)
def test_boost_1d(benchmark, flow, storage, dtype):
    result = benchmark(make_and_run_hist, flow, storage, vals[dtype])
    assert_allclose(result[:-1], answer[dtype][:-1], atol=2)
