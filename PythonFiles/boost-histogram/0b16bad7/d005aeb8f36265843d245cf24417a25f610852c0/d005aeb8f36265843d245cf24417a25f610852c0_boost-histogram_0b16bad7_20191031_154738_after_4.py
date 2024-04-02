from __future__ import absolute_import, division, print_function

del absolute_import, division, print_function

from ._core.algorithm import shrink_and_rebin, slice_and_rebin, rebin, shrink, slice


def sum(histogram, flow=False):
    """Sum a histogram, optionally with flow bins"""
    return histogram.sum(flow)


def reduce(histogram, *args):
    "Reduce a histogram with 1 or more reduce options"
    return histogram.reduce(*args)


def empty(histogram, flow=False):
    """Check to see if a histogram is empty, optionally with flow bins"""
    return histogram.empty(flow)