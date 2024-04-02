from indra.preassembler.sitemapper import default_mapper as sm, MappedStatement
from indra.statements import *

def test_check_agent_mod():
    mapk1_valid = Agent('MAPK1',
                         mods=['PhosphorylationThreonine',
                                'PhosphorylationTyrosine'],
                          mod_sites=['185', '187'], db_refs={'UP': 'P28482'})
    res_valid = sm.check_agent_mod(mapk1_valid)
    assert len(res_valid) == 2
    assert res_valid[0] == {}
    assert isinstance(res_valid[1], Agent)
    assert res_valid[1].matches(mapk1_valid)

    mapk1_invalid = Agent('MAPK1',
                          mods=['PhosphorylationThreonine',
                                'PhosphorylationTyrosine'],
                          mod_sites=['183', '185'], db_refs={'UP': 'P28482'})
    res_invalid = sm.check_agent_mod(mapk1_invalid)
    assert len(res_invalid) == 2
    assert isinstance(res_invalid[0], dict)
    assert isinstance(res_invalid[1], Agent)
    invalid_sites = res_invalid[0]
    assert len(invalid_sites.keys()) == 2
    map183 = invalid_sites[('MAPK1', 'T', '183')]
    assert len(map183) == 3
    assert map183[0] == 'T'
    assert map183[1] == '185'
    map185 = invalid_sites[('MAPK1', 'Y', '185')]
    assert len(map185) == 3
    assert map185[0] == 'Y'
    assert map185[1] == '187'
    new_agent = res_invalid[1]
    assert new_agent.mods == ['PhosphorylationThreonine',
                             'PhosphorylationTyrosine']
    assert new_agent.mod_sites == ['185', '187']

    # Test a site that is invalid but not found in the site map

def test_site_map_complex():
    mapk1_invalid = Agent('MAPK1',
                          mods=['PhosphorylationThreonine',
                                'PhosphorylationTyrosine'],
                          mod_sites=['183', '185'], db_refs={'UP': 'P28482'})
    mapk3_invalid = Agent('MAPK3',
                            mods=['PhosphorylationThreonine',
                                  'PhosphorylationTyrosine'],
                            mod_sites=['201', '203'], db_refs={'UP': 'P27361'})

    st1 = Complex([mapk1_invalid, mapk3_invalid])
    res = sm.map_sites([st1])
    assert len(res) == 2
    valid_stmts = res[0]
    mapped_stmts = res[1]
    assert isinstance(valid_stmts, list)
    assert isinstance(mapped_stmts, list)
    assert len(valid_stmts) == 0
    assert len(mapped_stmts) == 1
    mapped_stmt = mapped_stmts[0]
    assert isinstance(mapped_stmt, MappedStatement)
    assert mapped_stmt.original_stmt == st1
    assert isinstance(mapped_stmt.mapped_mods, dict)
    assert len(mapped_stmt.mapped_mods.keys()) == 4
    ms = mapped_stmt.mapped_stmt
    assert isinstance(ms, Statement)
    members = ms.members
    assert len(members) == 2
    agent1 = members[0]
    agent2 = members[1]
    assert agent1.name == 'MAPK1'
    assert len(agent1.mods) == 2
    assert len(agent1.mod_sites) == 2
    assert agent1.mods[0] == 'PhosphorylationThreonine'
    assert agent1.mods[1] == 'PhosphorylationTyrosine'
    assert agent1.mod_sites[0] == '185'
    assert agent1.mod_sites[1] == '187'
    assert agent2.mods[0] == 'PhosphorylationThreonine'
    assert agent2.mods[1] == 'PhosphorylationTyrosine'
    assert agent2.mod_sites[0] == '202'
    assert agent2.mod_sites[1] == '204'
