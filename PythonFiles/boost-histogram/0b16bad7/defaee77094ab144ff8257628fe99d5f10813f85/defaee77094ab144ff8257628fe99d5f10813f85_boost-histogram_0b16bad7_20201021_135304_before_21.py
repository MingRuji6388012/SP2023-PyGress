# -*- coding: utf-8 -*-
import pytest

import boost_histogram  # noqa: F401


@pytest.fixture(params=(False, True), ids=("no_growth", "growth"))
def growth(request):
    return request.param


@pytest.fixture(params=(False, True), ids=("no_overflow", "overflow"))
def overflow(request):
    return request.param


@pytest.fixture(params=(False, True), ids=("no_underflow", "underflow"))
def underflow(request):
    return request.param


@pytest.fixture(params=(False, True), ids=("no_flow", "flow"))
def flow(request):
    return request.param


@pytest.fixture(
    params=(None, "str", 1, {"a": 1}),
    ids=("no_metadata", "str_metadata", "int_metadata", "dict_metadata"),
)
def metadata(request):
    return request.param
