from __future__ import absolute_import, print_function, unicode_literals
from builtins import dict, str
from indra.statements import *
from indra.assemblers import CAGAssembler

statements = [Influence(
    Agent('inorganic fertilizer'),
    Agent('farm sizes'),
    {'adjectives': 'serious', 'polarity': 1},
    {'adjectives': 'significant', 'polarity': 1},
)]


def test_assemble_influence():
    ca = CAGAssembler(statements)
    CAG = ca.make_model()
    assert(len(CAG.nodes()) == 2)
    assert(len(CAG.edges()) == 1)


def test_export_to_cyjs():
    ca = CAGAssembler(statements)
    ca.make_model()
    cyjs = ca.export_to_cytoscapejs()
    assert len(cyjs['nodes']) == 2
    assert len(cyjs['edges']) == 1
