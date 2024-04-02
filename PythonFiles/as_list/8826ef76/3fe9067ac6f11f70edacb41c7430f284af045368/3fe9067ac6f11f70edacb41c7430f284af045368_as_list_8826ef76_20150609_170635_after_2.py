# -*- coding: utf-8 -*-
from as_list import as_list


def test_with_list():
    """Should return the same input list"""
    some_list = ["first", "second", "third"]
    same_list = as_list(some_list)
    assert some_list == same_list


def test_with_tuple():
    """Should return the same input tuple"""
    some_tuple = ("first", "second", "third")
    same_tuple = as_list(some_tuple)
    assert some_tuple == same_tuple


def test_with_element():
    """Should return list with input element"""
    some_element = "first"
    same_element_list = as_list(some_element)
    assert [some_element] == same_element_list
