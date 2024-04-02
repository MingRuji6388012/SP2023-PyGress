"""A client for OWL-sourced identifier mappings."""

import json
import pickle
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Optional, TYPE_CHECKING, Union

from tqdm import tqdm

from indra.databases.obo_client import OntologyClient, RESOURCES, prune_empty_entries

if TYPE_CHECKING:
    import pronto


class OwlClient(OntologyClient):
    """A base client for data that's been grabbed via OWL."""

    @staticmethod
    def entry_from_term(term: 'pronto.Term') -> Mapping[str, Any]:
        """Create a data dictionary from a Pronto term."""
        rels_dict = defaultdict(list)
        xrefs = []
        for xref in term.xrefs:
            try:
                xref_db, xref_id = xref.id.split(':')
            except ValueError:
                continue
            else:
                xrefs.append(dict(namespace=xref_db, id=xref_id))
        for child in term.subclasses(distance=1, with_self=False):
            rels_dict['is_a'].append(child.id)

        namespace, identifier = term.id.split(':')

        return {
            'namespace': namespace,
            'id': identifier,
            'name': term.name,
            'synonyms': [
                s.description
                for s in term.synonyms
            ],
            'xrefs': xrefs,
            'alt_ids': sorted(term.alternate_ids),
            'relations': dict(rels_dict),
        }

    @classmethod
    def entries_from_ontology(
        cls,
        prefix: str,
        ontology: 'pronto.Ontology',
        *,
        skip_obsolete: bool = True,
    ):
        """"""
        rv = []
        for term in tqdm(ontology.terms(), desc=f'[{prefix}]'):
            if term.obsolete and skip_obsolete:
                continue
            if not term.id.startswith(prefix):
                continue
            rv.append(cls.entry_from_term(term))
        return rv

    @classmethod
    def update_resource(
        cls,
        prefix: str,
        ontology: 'pronto.Ontology',
        directory: Union[str, Path],
        skip_obsolete: bool = True,
    ):
        entries = cls.entries_from_ontology(prefix=prefix, ontology=ontology, skip_obsolete=skip_obsolete)
        entries = prune_empty_entries(
            entries,
            {'synonyms', 'xrefs', 'alt_ids', 'relations'},
        )
        entries = sorted(entries, key=lambda x: int(x['id']))

        resource_path = cls._make_resource_path(directory=directory, prefix=prefix.lower())
        with open(resource_path, 'w') as file:
            json.dump(entries, file, indent=1, sort_keys=True)

    @classmethod
    def update_from_obo_library(
        cls,
        prefix: str,
        extension: str = 'owl',
        directory: Optional[str] = None,
        **kwargs,
    ):
        if directory is None:
            directory = RESOURCES
        directory = Path(directory).resolve()
        cache_path = directory.joinpath(f'{prefix.lower()}.{extension}.pkl')
        if cache_path.is_file():
            with cache_path.open('rb') as file:
                ontology = pickle.load(file)
        else:
            try:
                import pronto
            except ImportError:
                raise ImportError(
                    'To use the INDRA OWL Client, you must first'
                    'install Pronto with `pip install pronto`.'
                )
            ontology = pronto.Ontology.from_obo_library(f'{prefix}.{extension}')
            with cache_path.open('wb') as file:
                pickle.dump(ontology, file, protocol=pickle.HIGHEST_PROTOCOL)

        cls.update_resource(prefix=prefix, ontology=ontology, directory=directory, **kwargs)

    @classmethod
    def update_from_file(
        cls,
        prefix: str,
        file,
        directory: Optional[str] = None,
        **kwargs,
    ):
        try:
            import pronto
        except ImportError:
            raise ImportError(
                'To use the INDRA OWL Client, you must first'
                'install Pronto with `pip install pronto`.'
            )
        ontology = pronto.Ontology(file)
        cls.update_resource(prefix=prefix, ontology=ontology, directory=directory, **kwargs)


if __name__ == '__main__':
    OwlClient.update_from_obo_library('IDO')