from indra.databases import mesh_client


def test_mesh_id_lookup_from_web():
    mesh_id = 'D003094'
    mesh_name = mesh_client.get_mesh_name_from_web(mesh_id)
    assert mesh_name == 'Collagen'


def test_invalid_id():
    mesh_name = mesh_client.get_mesh_name_from_web('34jkgfh')
    assert mesh_name is None


def test_mesh_id_lookup_local():
    mesh_id = 'D005963'
    mesh_name = mesh_client.get_mesh_name(mesh_id, offline=True)
    assert mesh_name == 'Glucosylceramides'


def test_mesh_id_local_missing():
    mesh_id = 'D015242'
    mesh_name = mesh_client.get_mesh_name(mesh_id, offline=True)
    assert mesh_name is None


def test_mesh_id_fallback_to_rest():
    mesh_id = 'D015242'
    mesh_name = mesh_client.get_mesh_name(mesh_id, offline=False)
    assert mesh_name == 'Ofloxacin'


def test_mesh_term_lookup_local():
    mesh_term = 'Glucosylceramides'
    (mesh_id, mesh_name) = mesh_client.get_mesh_id_name(mesh_term, offline=True)
    assert mesh_id == 'D005963'
    assert mesh_name == mesh_term


def test_mesh_term_local_missing():
    mesh_term = 'Prostate Cancer'
    mesh_id, mesh_name = mesh_client.get_mesh_id_name(mesh_term, offline=True)
    assert mesh_id is None
    assert mesh_name is None


def test_mesh_term_name_norm():
    # For this one, the corresponding descriptor is D016922, which is in the
    # INDRA resource file; however, the descriptor name is "Cellular
    # Senescence".  This test verifies the expected behavior that in
    # offline-only mode, "Cellular Senescence" will return the correct
    # descriptor ID, but "Cell Aging" will not, unless using the REST service.
    query_name = 'Cellular Senescence'
    mesh_id, mesh_name = mesh_client.get_mesh_id_name(query_name, offline=True)
    assert mesh_id == 'D016922'
    assert mesh_name == query_name
    query_name = 'Cell Aging'
    mesh_id, mesh_name = mesh_client.get_mesh_id_name(query_name, offline=True)
    assert mesh_id is None
    assert mesh_name is None
    mesh_id, mesh_name = mesh_client.get_mesh_id_name(query_name, offline=False)
    assert mesh_id == 'D016922'
    assert mesh_name == 'Cellular Senescence'

