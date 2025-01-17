from __future__ import absolute_import, print_function, unicode_literals
from builtins import dict, str
import logging
import rdflib
from indra.statements import Influence, Agent, Evidence

logger = logging.getLogger('cwms')

prefixes = """
PREFIX role: <http://www.cs.rochester.edu/research/trips/role#>
PREFIX lf: <http://www.cs.rochester.edu/research/trips/LF#>
"""

class CWMSProcessor(object):
    """This processor extracts INDRA statements from CWMS RDF output.

    Parameters
    ----------
    text: str
        The source sentence as text
    rdf_filename: str
        A string containing the RDF output returned by CWMS for that sentence

    Attributes
    ----------
    statements: list[indra.statements.Statement]
        A list of INDRA statements that were extracted by the processor.
    """
    def __init__(self, text, rdf_filename):
        self.text = text

        # Read in the RDF graph
        g = rdflib.Graph()
        with open(rdf_filename, 'rb') as f:
            logger.info('Started loading graph from %s' % rdf_filename)
            g.parse(f, format='application/rdf+xml') #, format='json-ld')
            logger.info('Finished loading graph')
        self.graph = g

        # Extract statements
        self.statements = []
        self.extract_statements()

    def extract_statement_from_query_result(self, res):
        agent_start, agent_end, affected_start, affected_end = res

        agent_start = int(agent_start)
        agent_end = int(agent_end)
        affected_start = int(affected_start)
        affected_end = int(affected_end)

        agent = self.text[agent_start:agent_end]
        affected = self.text[affected_start:affected_end]

        agent = agent.lstrip().rstrip()
        affected = affected.lstrip().rstrip()

        agent = Agent(agent, db_refs={'TEXT': agent})
        affected = Agent(affected, db_refs={'TEXT': affected})

        statement = Influence(subj=agent, obj=affected)
        self.statements.append(statement)

    def extract_statements(self):
        query = prefixes + """
        SELECT 
            ?agent_start
            ?agent_end
            ?affected_start
            ?affected_end
        WHERE {
            ?rel role:AGENT ?agent .
            ?rel role:AFFECTED ?affected .
            ?agent lf:start ?agent_start .
            ?agent lf:end ?agent_end .
            ?affected lf:start ?affected_start .
            ?affected lf:end ?affected_end .
        }
        """
        results = self.graph.query(query)
        for res in results:
            self.extract_statement_from_query_result(res)

        query = query.replace('role:AFFECTED', 'role:RESULT')
        results = self.graph.query(query)
        for res in results:
            self.extract_statement_from_query_result(res)


