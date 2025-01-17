# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from builtins import object, dict, str
import json
import jinja2
import logging
import networkx as nx
from functools import partial
from indra.statements import Influence

# Python 2
try:
    basestring
# Python 3
except:
    basestring = str

logger = logging.getLogger('cag_assembler')


class CAGAssembler(object):
    """Assembles a causal analysis graph from INDRA Statements.

    Parameters
    ----------
    stmts : Optional[list[indra.statement.Statements]]
        A list of INDRA Statements to be assembled. Currently supports
        Influence Statements.

    Attributes
    ----------
    statements : list[indra.statements.Statement]
        A list of INDRA Statements to be assembled.
    CAG : nx.MultiDiGraph
        A networkx MultiDiGraph object representing the causal analysis graph.
    """

    def __init__(self, stmts=None, grounding_threshold = None):
        if not stmts:
            self.statements = []
        else:
            self.statements = stmts
        self.grounding_threshold = grounding_threshold

    def add_statements(self, stmts):
        """Add a list of Statements to the assembler."""
        self.statements += stmts

    def make_model(self, grounding_threshold = None):
        """Return a networkx MultiDiGraph representing a causal analysis graph.

        Parameters
        ----------
        grounding_threshold: Optional[float]
            Minimum threshold score for Eidos grounding.

        Returns
        -------
        nx.MultiDiGraph
            The assembled CAG.
        """
        self.grounding_threshold = grounding_threshold

        # Filter to Influence Statements which are currently supported
        statements = [stmt for stmt in self.statements if
                      isinstance(stmt, Influence)]

        # Initialize graph
        self.CAG = nx.MultiDiGraph()

        # Add nodes and edges to the graph
        for s in statements:
            # Get standardized name of subject and object
            # subj, obj = (self._node_name(s.subj), self._node_name(s.obj))

            # See if both subject and object have polarities given
            has_both_polarity = (s.subj_delta['polarity'] is not None and
                                 s.obj_delta['polarity'] is not None)

            # Add the nodes to the graph
            for node, delta in zip((s.subj, s.obj),
                                   (s.subj_delta, s.obj_delta)):
                self.CAG.add_node(self._node_name(node),
                        simulable=has_both_polarity, mods=delta['adjectives'])

            # Edge is solid if both nodes have polarity given
            linestyle = 'solid' if has_both_polarity else 'dotted'
            if has_both_polarity:
                same_polarity = s.subj_delta['polarity'] == s.obj_delta['polarity']
                if same_polarity:
                    targetArrowShape, linecolor = ('circle', 'green')
                else:
                    targetArrowShape, linecolor = ('tee', 'maroon')
            else:
                targetArrowShape, linecolor = ('triangle', 'maroon')


            # Add edge to the graph with metadata from statement
            provenance = []
            if s.evidence:
                provenance = s.evidence[0].annotations.get('provenance', [])
                if provenance:
                    provenance[0]['text'] = s.evidence[0].text
            self.CAG.add_edge(
                    self._node_name(s.subj),
                    self._node_name(s.obj),
                    subj_polarity    = s.subj_delta['polarity'],
                    subj_adjectives  = s.subj_delta['adjectives'],
                    obj_polarity     = s.obj_delta['polarity'],
                    obj_adjectives   = s.obj_delta['adjectives'],
                    linestyle        = linestyle,
                    linecolor=linecolor,
                    targetArrowShape=targetArrowShape,
                    provenance=provenance,
                )

        return self.CAG

    def export_to_cytoscapejs(self):
        """Return CAG in format readable by CytoscapeJS.

        Return
        ------
        dict
            A JSON-like dict representing the graph for use with
            CytoscapeJS.
        """
        def _create_edge_data_dict(e):
            """Return a dict from a MultiDiGraph edge for CytoscapeJS export."""
            # A hack to get rid of the redundant 'Provenance' label.
            if e[3].get('provenance'):
                tooltip = e[3]['provenance'][0]
                if tooltip.get('@type'):
                    del tooltip['@type']
            else:
                tooltip = None
            edge_data_dict = {
                    'id'               : e[0]+'_'+e[1],
                    'source'           : e[0],
                    'target'           : e[1],
                    'linestyle'        : e[3]["linestyle"],
                    'linecolor'        : e[3]["linecolor"],
                    'targetArrowShape' : e[3]["targetArrowShape"],
                    'subj_adjectives'  : e[3]["subj_adjectives"],
                    'subj_polarity'    : e[3]["subj_polarity"],
                    'obj_adjectives'   : e[3]["obj_adjectives"],
                    'obj_polarity'     : e[3]["obj_polarity"],
                    'tooltip'          : tooltip,
                    'simulable'        : False if (
                        e[3]['obj_polarity'] is None or
                        e[3]['subj_polarity'] is None) else True,
                    }
            return edge_data_dict

        return {
                'nodes': [{'data': {
                    'id': n[0],
                    'simulable': n[1]['simulable'],
                    'tooltip': 'Modifiers: '+json.dumps(n[1]['mods'])}
                    } for n in self.CAG.nodes(data=True)],

                'edges': [{'data': _create_edge_data_dict(e)}
                           for e in self.CAG.edges(data=True, keys=True)]
                }

    def generate_jupyter_js(self, cyjs_style=cyjs_style,
                            cyjs_layout=cyjs_layout):
        """Generate Javascript from a template to run in Jupyter notebooks.

        Parameters
        ----------
        cyjs_style : dict
            A dict that sets CytoscapeJS style as specified in
            https://github.com/cytoscape/cytoscape.js/blob/master/documentation/md/style.md.

        cyjs_layout : dict
            A dict that sets CytoscapeJS
            `layout parameters <http://js.cytoscape.org/#core/layout>`_.

        Returns
        -------
        string
            A Javascript string to be rendered in a Jupyter notebook cell.
        """
        to_json = partial(json.dumps, indent=2)
        return jupyter_cyjs_template.render(
            cyjs_elements=to_json(self.export_to_cytoscapejs()),
            cyjs_style=to_json(cyjs_style),
            cyjs_layout=to_json(cyjs_layout))


    def _node_name(self, concept):
        """Return a standardized name for a node given a Concept."""
        if (# grounding threshold is specified
            self.grounding_threshold is not None
            # Eidos groundings are present
            and concept.db_refs['EIDOS']
            # The grounding score is above the grounding threshold
            and concept.db_refs['EIDOS'][0][1] > self.grounding_threshold):
                entry = concept.db_refs['EIDOS'][0][0]
                return entry.split('/')[-1].replace('_', ' ').capitalize()
        else:
            return concept.name.capitalize()


jupyter_cyjs_template = jinja2.Template("""
require.config({
  paths: {
    cytoscape: 'https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.2.8/cytoscape',
  }
})

require(['cytoscape'], function(cytoscape){
  $("#cyDiv").remove();
  element.append("<div id='cyDiv'></div>");
  $("#cyDiv").height("300px");

    var cy = cytoscape({
      container : document.getElementById('cyDiv'),
      elements  : {{ cyjs_elements | safe }},
      style     : {{ cyjs_style    | safe }},
      layout    : {{ cyjs_layout   | safe }},
      maxZoom   : 10,
      minZoom   : 0.1,
    });
});
""")


cyjs_style = [ {
        'selector'             : 'node',
        'style'                : {
            "label"            : "data(id)",
            "background-color" : "white",
            "border-color"     : "maroon",
            "border-width"     : "1px",
            "font-family"      : "Arno Pro, Arial",
            "text-halign"      : "center",
            "text-valign"      : "center",
            "padding"          : 10,
            "width"            : "function( node ){ return 2*node.degree(); }",
            "height"           : "function( node ){ return 2*node.degree(); }",
            "shape"            : "ellipse",
            "text-max-width"   : 80,
            "text-wrap"        : True,
        }
    }, {
        'selector'               : 'edge',
        'style'                  : {
            "curve-style"        : "bezier",
            "line-color"         : "data(linecolor)",
            "target-arrow-shape" : "data(targetArrowShape)",
            "target-arrow-color" : "data(linecolor)",
            "line-style"         : "data(linestyle)",
            "width"              : "1",
    }
}]

cyjs_layout = {'name': 'cose',
               'nodeDimensionsIncludeLabels': True,
               'componentSpacing': 1,
               'nodeOverlap': 1000,
               'nodeRepulsion': 500}

