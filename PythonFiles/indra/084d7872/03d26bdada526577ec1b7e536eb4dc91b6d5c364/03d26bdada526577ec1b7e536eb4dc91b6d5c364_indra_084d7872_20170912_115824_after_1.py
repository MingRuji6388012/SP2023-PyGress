from __future__ import absolute_import, print_function, unicode_literals
from builtins import dict, str
import numpy
from copy import copy
from indra.databases import ndex_client
from indra.databases import cbio_client
# Python 2
try:
    basestring
# Python 3
except:
    basestring = str

ndex_context = 'http://general.bigmech.ndexbio.org:8081/context/'

def get_protein_expression(gene_names, cell_types):
    """Return the protein expression levels of genes in cell types.

    Parameters
    ----------
    gene_names : list
        HGNC gene symbols for which expression levels are queried.
    cell_types : list
        List of cell type names in which expression levels are queried.
        The cell type names follow the CCLE database conventions.

        Example: LOXIMVI_SKIN, BT20_BREAST

    Returns
    -------
    res : str
        A json string containing the predicted protein expression levels of
        the given proteins in the given cell types as returned by the
        NDEx web service.
    """
    A = 0.2438361
    B = 3.0957627
    mrna_amounts = cbio_client.get_ccle_mrna(gene_names, cell_types)
    protein_amounts = copy(mrna_amounts)
    for cell_line, amounts in mrna_amounts.items():
        for gene_name, amount in amounts.items():
            protein_amount = 10**(A * amount + B)
            protein_amounts[cell_line][gene_name] = protein_amount
    return protein_amounts

def get_mutations(gene_names, cell_types):
    """Return the mutation status of genes in cell types.

    Parameters
    ----------
    gene_names : list
        HGNC gene symbols for which mutations are queried.
    cell_types : list
        List of cell type names in which mutations are queried.
        The cell type names follow the CCLE database conventions.

        Example: LOXIMVI_SKIN, BT20_BREAST

    Returns
    -------
    res : str
        A json string containing the mutation status of
        the given proteins in the given cell types as returned by the
        NDEx web service.
    """
    url = ndex_context + 'mutation/cell_line'
    if isinstance(gene_names, basestring):
        gene_names = [gene_names]
    if isinstance(cell_types, basestring):
        cell_types = [cell_types]
    params = {g: cell_types for g in gene_names}
    res = ndex_client.send_request(url, params, is_json=True)
    return res