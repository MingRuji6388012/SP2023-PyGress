import pytest
from pytest import approx


from boost.histogram import histogram
from boost.histogram.axis import (regular_uoflow, regular_noflow,
                                  regular_log, regular_sqrt,
                                  regular_pow, circular,
                                  variable, integer_uoflow,
                                  integer_noflow, integer_growth,
                                  category_int as category)
import boost.histogram as bh

import numpy as np
from numpy.testing import assert_array_equal

try:
    import cPickle as pickle
except ImportError:
    import pickle

# histogram -> boost.histogram
# histogram -> make_histogram
# .dim -> .rank()

def test_init():
    histogram()
    histogram(integer_uoflow(-1, 1))
    with pytest.raises(RuntimeError):
        histogram(1)
    with pytest.raises(RuntimeError):
        histogram("bla")
    with pytest.raises(RuntimeError):
        histogram([])
    with pytest.raises(RuntimeError):
        histogram(regular_uoflow)
    with pytest.raises(TypeError):
        histogram(regular_uoflow())
    with pytest.raises(RuntimeError):
        histogram([integer_uoflow(-1, 1)])
     # TODO: Should fail
     # CLASSIC: with pytest.raises(ValueError):
    histogram(integer_uoflow(-1, 1), unknown_keyword="nh")

    h = histogram(integer_uoflow(-1, 2))
    assert h.rank() == 1
    assert h.axis(0) == integer_uoflow(-1, 2)
    assert h.axis(0).size(flow=True) == 5
    assert h.axis(0).size() == 3
    assert h != histogram(regular_uoflow(1, -1, 1))
    assert h != histogram(integer_uoflow(-1, 1, metadata="ia"))


def test_copy():
    a = histogram(integer_uoflow(-1, 1))
    import copy
    b = copy.copy(a)
    assert a == b
    assert id(a) != id(b)

    c = copy.deepcopy(b)
    assert b == c
    assert id(b) != id(c)


def test_fill_int_1d():

    h = histogram(integer_uoflow(-1, 2))
    assert isinstance(h, bh.hist.any_int)
    assert isinstance(h, histogram)

    with pytest.raises(ValueError):
        h()
    with pytest.raises(ValueError):
        h(1, 2)
    for x in (-10, -1, -1, 0, 1, 1, 1, 10):
        h(x)
    assert h.sum() == 6
    assert h.sum(flow=True) == 8
    assert h.axis(0).size(flow=True) == 5

    with pytest.raises(TypeError):
        h.at(0, foo=None)
    with pytest.raises(ValueError):
        h.at(0, 1)
    with pytest.raises(TypeError):
        h[0, 1]

    for get in (lambda h, arg: h.at(arg),):
               # lambda h, arg: h[arg]):
        assert get(h, 0) == 2
        assert get(h, 1) == 1
        assert get(h, 2) == 3
        #assert get(h, 0).variance == 2
        #assert get(h, 1).variance == 1
        #assert get(h, 2).variance == 3

        assert get(h, -1) == 1
        assert get(h, 3) == 1


@pytest.mark.parametrize("flow", [True, False])
def test_fill_1d(flow):
    h = histogram(regular_uoflow(3, -1, 2) if flow else regular_noflow(3, -1, 2))
    with pytest.raises(ValueError):
        h()
    with pytest.raises(ValueError):
        h(1, 2)
    for x in (-10, -1, -1, 0, 1, 1, 1, 10):
        h(x)

    assert h.sum() == 6
    assert h.sum(flow=True) == 6 + 2*flow
    assert h.axis(0).size(flow=True) == 3 + 2*flow

    with pytest.raises(TypeError):
        h.at(0, foo=None)
    with pytest.raises(ValueError):
        h.at(0, 1)
    with pytest.raises(TypeError):
        h[0, 1]

    for get in (lambda h, arg: h.at(arg),):
               # lambda h, arg: h[arg]):
        assert get(h, 0) == 2
        assert get(h, 1) == 1
        assert get(h, 2) == 3
        #assert get(h, 0).variance == 2
        #assert get(h, 1).variance == 1
        #assert get(h, 2).variance == 3

    if flow is True:
        assert get(h, -1) == 1
        assert get(h, 3) == 1

def test_growth():
    h = histogram(integer_uoflow(-1, 2))
    h(-1)
    h(1)
    h(1)
    for i in range(255):
        h(0)
    h(0)
    for i in range(1000 - 256):
        h(0)
    assert h.at(-1) == 0
    assert h.at(0) == 1
    assert h.at(1) == 1000
    assert h.at(2) == 2
    assert h.at(3) == 0


@pytest.mark.parametrize("flow", [True, False])
def test_fill_2d(flow):
    h = histogram((integer_uoflow if flow else integer_noflow)(-1, 2),
                  (regular_uoflow if flow else regular_noflow)(4, -2, 2))
    h(-1, -2)
    h(-1, -1)
    h(0, 0)
    h(0, 1)
    h(1, 0)
    h(3, -1)
    h(0, -3)

    with pytest.raises(Exception):
        h(1)
    with pytest.raises(Exception):
        h(1, 2, 3)

    m = [[1, 1, 0, 0, 0, 0],
         [0, 0, 1, 1, 0, 1],
         [0, 0, 1, 0, 0, 0],
         [0, 1, 0, 0, 0, 0],
         [0, 0, 0, 0, 0, 0]]

    for get in (lambda h, x, y: h.at(x, y),):
                # lambda h, x, y: h[x, y]):
        for i in range(-flow, h.axis(0).size() + flow):
            for j in range(-flow, h.axis(1).size() + flow):
                assert get(h, i, j) == m[i][j]


@pytest.mark.parametrize("flow", [True, False])
def test_add_2d(flow):
    h = histogram((integer_uoflow if flow else integer_noflow)(-1, 2),
                  (regular_uoflow if flow else regular_noflow)(4, -2, 2))
    assert isinstance(h, histogram)

    h(-1, -2)
    h(-1, -1)
    h(0, 0)
    h(0, 1)
    h(1, 0)
    h(3, -1)
    h(0, -3)

    m = [[1, 1, 0, 0, 0, 0],
         [0, 0, 1, 1, 0, 1],
         [0, 0, 1, 0, 0, 0],
         [0, 1, 0, 0, 0, 0],
         [0, 0, 0, 0, 0, 0]]

    h += h

    for i in range(-flow, h.axis(0).size() + flow):
        for j in range(-flow, h.axis(1).size() + flow):
            assert h.at(i, j) == 2 * m[i][j]

def test_add_2d_bad():
    a = histogram(integer_uoflow(-1, 1))
    b = histogram(regular_uoflow(3, -1, 1))

    with pytest.raises(TypeError):
        a += b

# WEIGHTED FILLS NOT SUPPORTED YET
# CLASSIC
@pytest.mark.skip()
@pytest.mark.parametrize("flow", [True, False])
def test_add_2d_w(flow):
    h = histogram((integer_uoflow if flow else integer_noflow)(-1, 2),
                  (regular_uoflow if flow else regular_noflow)(4, -2, 2))
    h(-1, -2)
    h(-1, -1)
    h(0, 0)
    h(0, 1)
    h(1, 0)
    h(3, -1)
    h(0, -3)

    m = [[1, 1, 0, 0, 0, 0],
         [0, 0, 1, 1, 0, 1],
         [0, 0, 1, 0, 0, 0],
         [0, 1, 0, 0, 0, 0],
         [0, 0, 0, 0, 0, 0]]

    h2 = histogram((integer_uoflow if flow else integer_noflow)(-1, 2),
                  (regular_uoflow if flow else regular_noflow)(4, -2, 2))
    h2(0, 0, weight=0)

    h2 += h
    h2 += h
    h += h
    assert h == h2

    for i in range(-flow, h.axis(0).size() + flow):
        for j in range(-flow, h.axis(1).size() + flow):
            assert h.at(i, j) == 2 * m[i][j]

def test_repr():
    h = histogram(regular_uoflow(10, 0, 1), integer_uoflow(0, 1))
    hr = repr(h)
    assert hr == '''histogram(
  regular(10, 0, 1, options=underflow | overflow),
  integer(0, 1, options=underflow | overflow)
)'''

def test_axis():
    axes = (regular_uoflow(10, 0, 1), integer_uoflow(0, 1))
    h = histogram(*axes)
    for i, a in enumerate(axes):
        assert h.axis(i) == a
    with pytest.raises(IndexError):
        h.axis(2)
    assert h.axis(-1) == axes[-1]
    assert h.axis(-2) == axes[-2]
    with pytest.raises(IndexError):
            h.axis(-3)

# CLASSIC: This used to only fail when accessing, now fails in creation
def test_overflow():
    with pytest.raises(RuntimeError):
        h = histogram(*[regular_uoflow(1, 0, 1) for i in range(50)])


def test_out_of_range():
    h = histogram(regular_uoflow(3, 0, 1))
    h(-1)
    h(2)
    assert h.at(-1) == 1
    assert h.at(3) == 1
    with pytest.raises(IndexError):
        h.at(-2)
    with pytest.raises(IndexError):
        h.at(4)
    #with pytest.raises(IndexError):
    #    h.at(-2).variance
    #with pytest.raises(IndexError):
    #    h.at(4).variance

# CLASSIC: This used to have variance
def test_operators():
    h = histogram(integer_uoflow(0, 2))
    h(0)
    h += h
    assert h.at(0) == 2
    assert h.at(1) == 0
    h *= 2
    assert h.at(0) == 4
    assert h.at(1) == 0
    assert (h + h).at(0) == (h * 2).at(0)
    assert (h + h).at(0) == (2 * h).at(0)
    h2 = histogram(regular_uoflow(2, 0, 2))
    with pytest.raises(TypeError):
        h + h2

# CLASSIC: reduce is not yet supported
@pytest.mark.skip(message="Reductions not yet supported")
def test_reduce_to(self):
    h = histogram(integer_uoflow(0, 2), integer_uoflow(1, 4))
    h(0, 1)
    h(0, 2)
    h(1, 3)

    h0 = h.reduce_to(0)
    assert h0.rank() == 1
    assert h0.axis() == integer_uoflow(0, 2)
    assert [h0.at(i) for i in range(2)] == [2, 1]

    h1 = h.reduce_to(1)
    assert h1.rank() == 1
    assert h1.axis() == integer_uoflow(1, 4)
    assert [h1.at(i) for i in range(3)] == [1, 1, 1]

    with pytest.raises(ValueError):
        h.reduce_to(*range(100))

    with pytest.raises(ValueError):
        h.reduce_to(2, 1)


# CLASSIC: This used to have metadata too, but that does not compare equal
def test_pickle_0():
    a = histogram(category([0, 1, 2]),
                  integer_uoflow(0, 20),
                  regular_noflow(20, 0.0, 20.0),
                  variable([0.0, 1.0, 2.0]),
                  circular(4, 2*np.pi))
    for i in range(a.axis(0).size(flow=True)):
        a(i, 0, 0, 0, 0)
        for j in range(a.axis(1).size(flow=True)):
            a(i, j, 0, 0, 0)
            for k in range(a.axis(2).size(flow=True)):
                a(i, j, k, 0, 0)
                for l in range(a.axis(3).size(flow=True)):
                    a(i, j, k, l, 0)
                    for m in range(a.axis(4).size(flow=True)):
                        a(i, j, k, l, m * 0.5 * np.pi)

    io = pickle.dumps(a,-1)
    b = pickle.loads(io)

    assert id(a) != id(b)
    assert a.rank() == b.rank()
    assert a.axis(0) == b.axis(0)
    assert a.axis(1) == b.axis(1)
    assert a.axis(2) == b.axis(2)
    assert a.axis(3) == b.axis(3)
    assert a.axis(4) == b.axis(4)
    assert a.sum() == b.sum()
    assert a == b

@pytest.mark.skip(message="Requires weighted fills / type")
def test_pickle_1():
    a = histogram(category([0, 1, 2]),
                  integer_uoflow(0, 3, metadata='ia'),
                  regular_noflow(4, 0.0, 4.0),
                  variable([0.0, 1.0, 2.0]))
    assert isinstance(a, bh.hist.any_int)
    assert isinstance(a, histogram)

    for i in range(a.axis(0).size(flow=True)):
        a(i, 0, 0, 0, weight=3)
        for j in range(a.axis(1).size(flow=True)):
            a(i, j, 0, 0, weight=10)
            for k in range(a.axis(2).size(flow=True)):
                a(i, j, k, 0, weight=2)
                for l in range(a.axis(3).size(flow=True)):
                    a(i, j, k, l, weight=5)

    io = BytesIO()
    pickle.dump(a, io)
    io.seek(0)
    b = pickle.load(io)

    assert id(a) != id(b)
    assert a.dim, b.dim
    assert a.axis(0) == b.axis(0)
    assert a.axis(1) == b.axis(1)
    assert a.axis(2) == b.axis(2)
    assert a.axis(3) == b.axis(3)
    assert a.sum() == b.sum()
    assert a == b # Note: metadata may be an issue here

# Numpy tests

def test_numpy_conversion_0():
    a = histogram(integer_noflow(0, 3))
    a(0)
    for i in range(5):
        a(1)
    c = np.array(a)  # a copy
    v = np.asarray(a)  # a view

    for t in (c, v):
        assert t.dtype == np.uint64 # CLASSIC: np.uint8
        assert_array_equal(t, (1, 5, 0))

    for i in range(10):
        a(2)
    # copy does not change, but view does
    assert_array_equal(c, (1, 5, 0))
    assert_array_equal(v, (1, 5, 10))

    for i in range(255):
        a(1)
    c = np.array(a)

    assert c.dtype == np.uint64 # CLASSIC: np.uint16
    assert_array_equal(c, (1, 260, 10))
    # view does not follow underlying switch in word size
    # assert not np.all(c, v)

@pytest.mark.skip(message="Requires weighted fills / type")
def test_numpy_conversion_1():
    a = histogram(integer_uoflow(0, 3))
    for i in range(10):
        a(1, weight=3)
    c = np.array(a)  # a copy
    v = np.asarray(a)  # a view
    assert c.dtype == np.float64
    assert_array_equal(c, np.array(((0, 30, 0, 0, 0), (0, 90, 0, 0, 0))))
    assert_array_equal(v, c)

def test_numpy_conversion_2():
    a = histogram(integer_noflow(0, 2),
                  integer_noflow(0, 3),
                  integer_noflow(0, 4))
    r = np.zeros((2, 3, 4), dtype=np.int8)
    for i in range(a.axis(0).size(flow=True)):
        for j in range(a.axis(1).size(flow=True)):
            for k in range(a.axis(2).size(flow=True)):
                for m in range(i + j + k):
                    a(i, j, k)
                r[i, j, k] = i + j + k

    d = np.zeros((2, 3, 4), dtype=np.int8)
    for i in range(a.axis(0).size(flow=True)):
        for j in range(a.axis(1).size(flow=True)):
            for k in range(a.axis(2).size(flow=True)):
                d[i, j, k] = a.at(i, j, k)

    assert_array_equal(d, r)

    c = np.array(a)  # a copy
    v = np.asarray(a)  # a view

    assert_array_equal(c, r)
    assert_array_equal(v, r)

@pytest.mark.skip(message="Requires weighted fills / type")
def test_numpy_conversion_3():
    a = histogram(integer_uoflow(0, 2),
                  integer_uoflow(0, 3),
                  integer_uoflow(0, 4))
    r = np.zeros((2, 4, 5, 6))
    for i in range(a.axis(0).size(flow=True)):
        for j in range(a.axis(1).size(flow=True)):
            for k in range(a.axis(2).size(flow=True)):
                a(i, j, k, weight=i + j + k)
                r[0, i, j, k] = i + j + k
                r[1, i, j, k] = (i + j + k)**2
    c = np.array(a)  # a copy
    v = np.asarray(a)  # a view

    c2 = np.zeros((2, 4, 5, 6))
    for i in range(a.axis(0).size(flow=True)):
        for j in range(a.axis(1).size(flow=True)):
            for k in range(a.axis(2).size(flow=True)):
                c2[0, i, j, k] = a.at(i, j, k)

    assert_array_equal(c, c2)
    assert_array_equal(c, r)
    assert_array_equal(v, r)

def test_numpy_conversion_4():
    a = histogram(integer_noflow(0, 2),
                  integer_noflow(0, 4))
    a1 = np.asarray(a)
    assert a1.dtype == np.uint64 # CLASSIC: np.uint8
    assert a1.shape == (2, 4)

    b = histogram()
    b1 = np.asarray(b)
    assert b1.shape == ()
    assert np.sum(b1) == 0

    # Compare sum methods
    assert b.sum() == np.asarray(b).sum()

@pytest.mark.skip(message="This require multiprecision storage")
def test_numpy_conversion_5():
    a = histogram(integer_noflow(0, 3),
                  integer_noflow(0, 2))
    a(0, 0)
    for i in range(80):
        a = a + a
    # a now holds a multiprecision type
    a(1, 0)
    for i in range(2):
        a(2, 0)
    for i in range(3):
        a(0, 1)
    for i in range(4):
        a(1, 1)
    for i in range(5):
        a(2, 1)
    a1 = np.asarray(a)
    assert a1.shape == (3, 2)
    assert a1[0, 0] == float(2 ** 80)
    assert a1[1, 0] == 1
    assert a1[2, 0] == 2
    assert a1[0, 1] == 3
    assert a1[1, 1] == 4
    assert a1[2, 1] == 5

def test_numpy_conversion_6():
    a = integer_uoflow(0, 2)
    b = regular_uoflow(2, 0, 2)
    c = variable([0, 1, 2])
    ref = np.array((0., 1., 2.))
    assert_array_equal(a.bins(), [0, 1])
    assert_array_equal(b.edges(), ref)
    assert_array_equal(c.edges(), ref)

    d = circular(4, 0, 2*np.pi)
    ref = np.array((0., 0.5 * np.pi, np.pi, 1.5 * np.pi, 2.0 * np.pi))
    assert_array_equal(d.edges(), ref)
    e = category([1, 2])
    ref = np.array((1, 2))
    assert_array_equal(e.bins(), ref)


def test_fill_with_numpy_array_0():
    def ar(*args):
        return np.array(args, dtype=float)
    a = histogram(integer_noflow(0, 3))
    a(ar(-1, 0, 1, 2, 1))
    a((4, -1, 0, 1, 2))
    assert a.at(0) == 2
    assert a.at(1) == 3
    assert a.at(2) == 2

    with pytest.raises(ValueError):
        a(np.empty((2, 2)))
    with pytest.raises(ValueError):
        a(np.empty(2), 1)
    with pytest.raises(ValueError):
        a(np.empty(2), np.empty(3))
    with pytest.raises(ValueError):
        a("abc")

    with pytest.raises(ValueError):
        a.at(1, 2)

    a = histogram(integer_noflow(0, 2),
                  regular_noflow(2, 0, 2))
    a(ar(-1, 0, 1), ar(-1., 1., 0.1))
    assert a.at(0, 0) == 0
    assert a.at(0, 1) == 1
    assert a.at(1, 0) == 1
    assert a.at(1, 1) == 0
    # we don't support: assert a.at([1, 1]).value, 0

    with pytest.raises(ValueError):
        a(1)
    with pytest.raises(ValueError):
        a([1, 0], [1])
    with pytest.raises(ValueError):
        a.at(1)
    with pytest.raises(ValueError):
        a.at(1, 2, 3)

    a = histogram(integer_noflow(0, 3))
    a(ar(0, 0, 1, 2, 1, 0, 2, 2))
    assert a.at(0) == 3
    assert a.at(1) == 2
    assert a.at(2) == 3

@pytest.mark.skip(message="Weighting (pun) for weighted fills")
def test_fill_with_numpy_array_1():
    def ar(*args):
        return np.array(args, dtype=float)
    a = histogram(integer_uoflow(0, 3))
    v = ar(-1, 0, 1, 2, 3, 4)
    w = ar( 2, 3, 4, 5, 6, 7)  # noqa
    a(v, weight=w)
    a((0, 1), weight=(2, 3))
    assert a.at(-1) == 2
    assert a.at(0) == 5
    assert a.at(1) == 7
    assert a.at(2) == 5
    # assert a.at(-1).variance == 4
    # assert a.at(0).variance == 13
    # assert a.at(1).variance == 25
    # assert a.at(2).variance == 25

    a((1, 2), weight=1)
    a(0, weight=(1, 2))
    assert a.at(0) == 8
    assert a.at(1) == 8
    assert a.at(2) == 6

    with pytest.raises(ValueError):
        a((1, 2), foo=(1, 1))
    with pytest.raises(ValueError):
        a((1, 2), weight=(1,))
    with pytest.raises(ValueError):
        a((1, 2), weight="ab")
    with pytest.raises(ValueError):
        a((1, 2), weight=(1, 1), foo=1)
    with pytest.raises(ValueError):
        a((1, 2), weight=([1, 1], [2, 2]))

    a = histogram(integer_noflow(0, 2),
                  regular_noflow(2, 0, 2))
    a((-1, 0, 1), (-1, 1, 0.1))
    assert a.at(0, 0) == 0
    assert a.at(0, 1) == 1
    assert a.at(1, 0) == 1
    assert a.at(1, 1) == 0
    a = histogram(integer_noflow(0, 3))
    a((0, 0, 1, 2))
    a((1, 0, 2, 2))
    assert a.at(0) == 3
    assert a.at(1) == 2
    assert a.at(2) == 3

