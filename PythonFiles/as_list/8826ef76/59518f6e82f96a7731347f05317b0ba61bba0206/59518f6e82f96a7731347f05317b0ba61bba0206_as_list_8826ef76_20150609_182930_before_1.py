# -*- coding: utf-8 -*-
"""as_list - returns list, tuple or list of single element"""

__version__ = '0.1'
__author__ = 'Victor Torres <vpaivatorres@gmail.com>'
__all__ = ["as_list"]


def as_list(input):
    if isinstance(input, (list, tuple)):
        return input

    return [input]
