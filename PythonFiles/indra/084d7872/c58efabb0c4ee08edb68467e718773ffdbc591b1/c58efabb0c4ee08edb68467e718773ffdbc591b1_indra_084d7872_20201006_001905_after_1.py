"""This module implements a number of functions that can be used to
validate INDRA Statements."""
import re
from indra.databases.identifiers import identifiers_mappings, \
    non_grounding, non_registry, identifiers_registry


class UnknownNamespace(ValueError):
    pass


class InvalidIdentifier(ValueError):
    pass


def validate_ns(db_ns):
    """Return True if the given namespace is known.

    Parameters
    ----------
    db_ns : str
        The namespace.

    Returns
    -------
    bool
        True if the given namepsace is known, otherwise False.
    """
    identifiers_ns = identifiers_mappings.get(db_ns, db_ns.lower())
    if identifiers_ns in identifiers_registry or db_ns in non_registry \
            or db_ns in non_grounding:
        return True
    return False


def assert_valid_ns(db_ns):
    """Raise UnknownNamespace error if the given namespace is unknown.

    Parameters
    ----------
    db_ns : str
        The namespace.
    """
    if not validate_ns(db_ns):
        raise UnknownNamespace(db_ns)


def validate_id(db_ns, db_id):
    """Return True if the given ID is valid in the given namespace.

    Parameters
    ----------
    db_ns : str
        The namespace.
    db_id : str
        The ID.

    Returns
    -------
    bool
        True if the given ID is valid in the given namespace.
    """
    identifiers_ns = identifiers_mappings.get(db_ns, db_ns.lower())
    if identifiers_ns in identifiers_registry:
        if re.match(identifiers_registry[identifiers_ns]['pattern'], db_id):
            return True
        else:
            return False
    elif db_ns in non_registry or db_ns in non_grounding:
        return True
    else:
        return False


def assert_valid_id(db_ns, db_id):
    """Raise InvalidIdentifier error if the ID is invalid in the given
    namespace.

    Parameters
    ----------
    db_ns : str
        The namespace.
    db_id : str
        The ID.
    """
    if not validate_id(db_ns, db_id):
        raise InvalidIdentifier(f'{db_ns}:{db_id}')


def validate_db_refs(db_refs):
    """Return True if all the entries in the given db_refs are valid.

    Parameters
    ----------
    db_refs : dict
        A dict of database references, typically part of an INDRA Agent.

    Returns
    -------
    bool
        True if all the entries are valid, else False.
    """
    return all(validate_ns(db_ns) and validate_id(db_ns, db_id)
               for db_ns, db_id in db_refs.items())


def assert_valid_db_refs(db_refs):
    """Raise InvalidIdentifier error if any of the entries in the given
    db_refs are invalid.

    Parameters
    ----------
    db_refs : dict
        A dict of database references, typically part of an INDRA Agent.
    """
    for db_ns, db_id in db_refs.items():
        assert_valid_ns(db_ns)
        assert_valid_id(db_ns, db_id)


def validate_statement(stmt):
    """Return True if all the groundings in the given statement are valid.

    Parameters
    ----------
    stmt : indra.statements.Statement
        An INDRA Statement to validate.

    Returns
    -------
    bool
        True if all the db_refs entries of the Agents in the given
        Statement are valid, else False.
    """
    return all(validate_db_refs(agent.db_refs)
               for agent in stmt.real_agent_list())


def assert_valid_statement(stmt):
    """Raise InvalidIdentifier error if any of the groundings in the given
    statement are invalid.

    Parameters
    ----------
    stmt : indra.statements.Statement
        An INDRA Statement to validate.
    """
    for agent in stmt.real_agent_list():
        assert_valid_db_refs(agent.db_refs)