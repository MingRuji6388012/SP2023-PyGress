import pybel
from pybel.dsl import *
import pybel.constants as pc
from pybel.examples import egf_graph, sialic_acid_graph
from indra.statements import *
from indra.sources import pybel as pb
from indra.databases import hgnc_client
from nose.tools import raises

mek_hgnc_id = hgnc_client.get_hgnc_id('MAP2K1')
mek_up_id = hgnc_client.get_uniprot_id(mek_hgnc_id)


def test_process_pybel():
    pbp = pb.process_pybel_graph(egf_graph)
    assert pbp.statements


def test_increase_amount():
    mek = protein(name='MAP2K1', namespace='HGNC')
    erk = protein(name='MAPK1', namespace='HGNC')
    g = pybel.BELGraph()
    g.add_qualified_edge(mek, erk, relation=pc.INCREASES,
                         evidence="Some evidence.", citation='123456')
    pbp = pb.process_pybel_graph(g)
    assert pbp.statements
    assert len(pbp.statements) == 1
    assert isinstance(pbp.statements[0], IncreaseAmount)

def test_get_agent_hgnc():
    mek = protein(name='MAP2K1', namespace='HGNC')
    agent = pb._get_agent(mek)
    assert isinstance(agent, Agent)
    assert agent.name == 'MAP2K1'
    assert agent.db_refs.get('HGNC') == mek_hgnc_id
    assert agent.db_refs.get('UP') == mek_up_id

    # Now create an agent with an identifier
    mek = protein(name='Foo', namespace='HGNC', identifier='6840')
    agent = pb._get_agent(mek)
    assert isinstance(agent, Agent)
    assert agent.name == 'MAP2K1'
    assert agent.db_refs.get('HGNC') == mek_hgnc_id
    assert agent.db_refs.get('UP') == mek_up_id


def test_get_agent_up():
    mek = protein(namespace='UP', identifier='Q02750')
    agent = pb._get_agent(mek)
    assert isinstance(agent, Agent)
    assert agent.name == 'MAP2K1'
    assert agent.db_refs.get('HGNC') == mek_hgnc_id
    assert agent.db_refs.get('UP') == mek_up_id


@raises(ValueError)
def test_get_agent_up_no_id():
    mek = protein(name='MAP2K1', namespace='UP')
    agent = pb._get_agent(mek)


def test_get_agent_with_mods():
    mek = protein(name='MAP2K1', namespace='HGNC',
                  variants=[pmod('Ph')])
    agent = pb._get_agent(mek)
    assert isinstance(agent, Agent)
    assert len(agent.mods) == 1
    mod = agent.mods[0]
    assert mod.mod_type == 'phosphorylation'
    assert not mod.residue
    assert not mod.position

    mek = protein(name='MAP2K1', namespace='HGNC',
                  variants=[pmod('Ph', code='Ser')])
    agent = pb._get_agent(mek)
    assert isinstance(agent, Agent)
    assert len(agent.mods) == 1
    mod = agent.mods[0]
    assert mod.mod_type == 'phosphorylation'
    assert mod.residue == 'S'
    assert not mod.position

    mek = protein(name='MAP2K1', namespace='HGNC',
                  variants=[pmod('Ph', position=218)])
    agent = pb._get_agent(mek)
    assert isinstance(agent, Agent)
    assert len(agent.mods) == 1
    mod = agent.mods[0]
    assert mod.mod_type == 'phosphorylation'
    assert not mod.residue
    assert mod.position == '218'

    mek = protein(name='MAP2K1', namespace='HGNC',
                  variants=[pmod('Ph', position=218, code='Ser')])
    agent = pb._get_agent(mek)
    assert isinstance(agent, Agent)
    assert len(agent.mods) == 1
    mod = agent.mods[0]
    assert mod.mod_type == 'phosphorylation'
    assert mod.residue == 'S'
    assert mod.position == '218'


if __name__ == '__main__':
    test_get_agent_with_mods()

