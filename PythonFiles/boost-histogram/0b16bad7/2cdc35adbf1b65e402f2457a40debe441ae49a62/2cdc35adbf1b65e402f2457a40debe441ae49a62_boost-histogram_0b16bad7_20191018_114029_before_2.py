import pytest

import boost_histogram as bh
import numpy as np
from numpy.testing import assert_array_equal, assert_allclose

methods = [bh.core.hist._any_double, bh.core.hist._any_unlimited, bh.core.hist._any_int]


@pytest.mark.parametrize("hist_func", methods)
def test_1D_fill_int(hist_func):
    bins = 10
    ranges = (0, 1)

    vals = (0.15, 0.25, 0.25)

    hist = hist_func([bh.axis.regular(bins, *ranges)])
    hist.fill(vals)

    H = np.array([0, 1, 2, 0, 0, 0, 0, 0, 0, 0])

    assert_array_equal(np.asarray(hist), H)
    assert_array_equal(hist.view(flow=False), H)
    assert_array_equal(hist.view(flow=True)[1:-1], H)

    assert hist.axis(0).size == bins
    assert hist.axis(0).extent == bins + 2


@pytest.mark.parametrize("hist_func", methods)
def test_2D_fill_int(hist_func):
    bins = (10, 15)
    ranges = ((0, 3), (0, 2))

    vals = ((0.15, 0.25, 0.25), (0.35, 0.45, 0.45))

    hist = hist_func(
        [bh.axis.regular(bins[0], *ranges[0]), bh.axis.regular(bins[1], *ranges[1])]
    )
    hist.fill(*vals)

    H = np.histogram2d(*vals, bins=bins, range=ranges)[0]

    assert_array_equal(np.asarray(hist), H)
    assert_array_equal(hist.view(flow=True)[1:-1, 1:-1], H)
    assert_array_equal(hist.view(flow=False), H)

    assert hist.axis(0).size == bins[0]
    assert hist.axis(0).extent == bins[0] + 2

    assert hist.axis(1).size == bins[1]
    assert hist.axis(1).extent == bins[1] + 2


def test_edges_histogram():
    edges = (1, 12, 22, 79)
    hist = bh.core.hist._any_int([bh.axis.variable(edges)])

    vals = (13, 15, 24, 29)
    hist.fill(vals)

    bins = np.asarray(hist)
    assert_array_equal(bins, [0, 2, 2])
    assert_array_equal(hist.view(flow=True), [0, 0, 2, 2, 0])
    assert_array_equal(hist.view(flow=False), [0, 2, 2])


def test_int_histogram():
    hist = bh.core.hist._any_int([bh.axis.integer(3, 7)])

    vals = (1, 2, 3, 4, 5, 6, 7, 8, 9)
    hist.fill(vals)

    bins = np.asarray(hist)
    assert_array_equal(bins, [1, 1, 1, 1])
    assert_array_equal(hist.view(flow=False), [1, 1, 1, 1])
    assert_array_equal(hist.view(flow=True), [2, 1, 1, 1, 1, 3])


def test_str_categories_histogram():
    hist = bh.core.hist._any_int([bh.axis.category(["a", "b", "c"])])

    vals = ["a", "b", "b", "c"]
    # Can't fill yet


def test_growing_histogram():
    hist = bh.core.hist._any_int([bh.axis.regular(10, 0, 1, growth=True)])

    hist.fill(1.45)

    assert hist.size == 17


def test_numpy_flow():
    h = bh.core.hist._any_int([bh.axis.regular(10, 0, 1), bh.axis.regular(5, 0, 1)])

    for i in range(10):
        for j in range(5):
            x, y = h.axis(0).centers[i], h.axis(1).centers[j]
            v = i + j * 10 + 1
            h.fill([x] * v, [y] * v)

    flow_true = h.to_numpy(True)[0][1:-1, 1:-1]
    flow_false = h.to_numpy(False)[0]

    assert_array_equal(flow_true, flow_false)

    view_flow_true = h.view(flow=True)
    view_flow_false = h.view(flow=False)
    view_flow_default = h.view()

    assert_array_equal(view_flow_true[1:-1, 1:-1], view_flow_false)
    assert_array_equal(view_flow_default, view_flow_false)


def test_numpy_compare():
    h = bh.core.hist._any_int([bh.axis.regular(10, 0, 1), bh.axis.regular(5, 0, 1)])

    xs = []
    ys = []
    for i in range(10):
        for j in range(5):
            x, y = h.axis(0).centers[i], h.axis(1).centers[j]
            v = i + j * 10 + 1
            xs += [x] * v
            ys += [y] * v

    h.fill(xs, ys)

    H, E1, E2 = h.to_numpy()

    nH, nE1, nE2 = np.histogram2d(xs, ys, bins=(10, 5), range=((0, 1), (0, 1)))

    assert_array_equal(H, nH)
    assert_allclose(E1, nE1)
    assert_allclose(E2, nE2)


def test_project():
    h = bh.core.hist._any_int([bh.axis.regular(10, 0, 1), bh.axis.regular(5, 0, 1)])
    h0 = bh.core.hist._any_int([bh.axis.regular(10, 0, 1)])
    h1 = bh.core.hist._any_int([bh.axis.regular(5, 0, 1)])

    for x, y in (
        (0.3, 0.3),
        (0.7, 0.7),
        (0.5, 0.6),
        (0.23, 0.92),
        (0.15, 0.32),
        (0.43, 0.54),
    ):
        h.fill(x, y)
        h0.fill(x)
        h1.fill(y)

    assert h.project(0, 1) == h
    assert h.project(0) == h0
    assert h.project(1) == h1

    assert_array_equal(h.project(0, 1), h)
    assert_array_equal(h.project(0), h0)
    assert_array_equal(h.project(1), h1)


def test_sums():
    h = bh.histogram(bh.axis.regular(4, 0, 1))
    h.fill([0.1, 0.2, 0.3, 10])

    assert h.sum() == 3
    assert h.sum(flow=True) == 4


def test_int_cat_hist():
    h = bh.core.hist._any_int([bh.axis.category([1, 2, 3])])

    h.fill(1)
    h.fill(2)
    h.fill(3)

    assert_array_equal(h.view(), [1, 1, 1])
    assert h.sum() == 3

    with pytest.raises(RuntimeError):
        h.fill(0.5)
