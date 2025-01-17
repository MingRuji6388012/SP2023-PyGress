from __future__ import absolute_import, print_function, unicode_literals
from builtins import dict, str
import re
from indra.statements import *
from indra.assemblers.html.assembler import HtmlAssembler, template_path, \
                                            tag_text

def make_stmt():
    src = Agent('SRC', db_refs = {'HGNC': '11283'})
    ras = Agent('RAS', db_refs = {'FPLX': 'RAS'})
    ev = Evidence(text="We noticed that the Src kinase was able to "
                       "phosphorylate Ras proteins.",
                  source_api='test', pmid='1234567',
                  annotations={'agents': {'raw_text': ['Src kinase',
                                                       'Ras proteins']}})
    st = Phosphorylation(src, ras, 'tyrosine', '32', evidence=[ev])
    return st


def test_format_evidence_text():
    stmt = make_stmt()
    ev_list = HtmlAssembler.format_evidence_text(stmt)
    assert len(ev_list) == 1
    ev = ev_list[0]
    assert isinstance(ev, dict)
    assert set(ev.keys()) == set(['source_api', 'pmid', 'text'])
    assert ev['source_api'] == 'test'
    assert ev['pmid'] == '1234567'
    assert ev['text'] == ('We noticed that the '
                          '<span class="label label-subject">Src kinase</span> '
                          'was able to phosphorylate '
                          '<span class="label label-object">'
                          'Ras proteins</span>.')


def test_assembler():
    stmt = make_stmt()
    ha = HtmlAssembler([stmt])
    result = ha.make_model()
    assert isinstance(result, str)
    # Read from the template file and make sure the beginning and end of the
    # content matches
    with open(template_path, 'rt') as f:
        template = f.read().strip()
    assert result.startswith(template[0:100])
    assert result.strip().endswith(template[-10:])


def test_tag_text():
    """If there are overlapping or nested matches, show only one."""
    text = 'FooBarBaz binds Foo.'
    indices = []
    for span in ('FooBarBaz', 'Foo'):
        tag_start = "<%s>" % span
        tag_close = "<%s/>" % span
        indices += [(m.start(), m.start() + len(span), span,
                     tag_start, tag_close)
                     for m in re.finditer(re.escape(span), text)]
    tagged_text = tag_text(text, indices)
    print(tagged_text)
    assert tagged_text == '<FooBarBaz>FooBarBaz</FooBarBaz> binds ' \
                          '<Foo>Foo</Foo>.'

if __name__ == '__main__':
    test_tag_text()

