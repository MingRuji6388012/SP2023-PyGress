import itertools
from indra.statements import *
from indra.preassembler.hierarchy_manager import activity_hierarchy as ah

class BaseAgentSet(object):
    """Container for a set of BaseAgents.
    Wraps a dict of BaseAgent instances.
    """
    def __init__(self):
        self.agents = {}

    def get_create_base_agent(self, agent):
        """Return agent with given name, creating it if needed."""
        try:
            base_agent = self.agents[agent.name]
        except KeyError:
            base_agent = BaseAgent(agent.name)
            self.agents[agent.name] = base_agent

        # Handle modification conditions
        for mc in agent.mods:
            base_agent.states.append(mc)

        return base_agent

    def keys(self):
        return self.agents.keys()

    def iteritems(self):
        return self.agents.iteritems()

    def __getitem__(self, name):
        return self.agents[name]

class BaseAgent(object):
    def __init__(self, name):
        self.name = name
        self.activities = []
        self.active_states = {}
        self.activity_graph = None
        self.states = []
        self.activity_reductions = None

    def get_activity_reduction(self, activity):
        self.make_activity_reductions()
        return self.activity_reductions.get(activity)

    def make_activity_reductions(self):
        self.make_activity_graph()
        self.activity_reductions = get_graph_reductions(self.activity_graph)

    def make_activity_graph(self):
        self.activity_graph  = []
        for a1, a2 in itertools.combinations(self.activities, 2):
            if ah.isa(a1, a2):
                self.activity_graph.append((a1, a2))
            if ah.isa(a2, a1):
                self.activity_graph.append((a2, a1))

    def add_activity(self, activity):
        if activity not in self.activities:
            self.activities.append(activity)

    def add_active_state(self, activity, mods):
        if not mods:
            return
        try:
            if not self.hasmod(self.active_states[activity], mods):
                self.active_states[activity].append(mods)
        except KeyError:
            self.active_states[activity] = [mods]

    @staticmethod
    def hasmod(mods_list, mods):
        for ml in mods_list:
            found_ix = []
            for m1 in ml:
                for ix, m2 in enumerate(mods):
                    if m1.equals(m2) and ix not in found_ix:
                        found_ix.append(ix)
                        break
            if len(found_ix) == len(mods):
                return True
        return False

    def __str__(self):
        s = '%s(' % self.name
        if self.activities:
            s += 'activities: %s, ' % self.activities
        for k, v in self.active_states.iteritems():
            s += '%s: %s' % (k, v)
        s += ')'
        return s

    def __repr__(self):
        return self.__str__()

class MechLinker(object):
    def __init__(self, stmts=None):
        if stmts is not None:
            self.statements = stmts
        else:
            self.statements = []
        self.base_agents = BaseAgentSet()

    def add_statements(self, stmts):
        self.statements.extend(stmts)

    def get_activities(self):
        for stmt in self.statements:
            if isinstance(stmt, Phosphorylation) or\
                isinstance(stmt, Transphosphorylation) or\
                isinstance(stmt, Autophosphorylation):
                if stmt.enz is not None:
                    enz_base = self.get_base(stmt.enz)
                    enz_base.add_activity('kinase')
                    enz_base.add_active_state('kinase', stmt.enz.mods)
            elif isinstance(stmt, Dephosphorylation):
                if stmt.enz is not None:
                    enz_base = self.get_base(stmt.enz)
                    enz_base.add_activity('phosphatase')
                    enz_base.add_active_state('phosphatase', stmt.enz.mods)
            elif isinstance(stmt, Modification):
                if stmt.enz is not None:
                    enz_base = self.get_base(stmt.enz)
                    enz_base.add_activity('catalytic')
                    enz_base.add_active_state('catalytic', stmt.enz.mods)
            elif isinstance(stmt, SelfModification):
                if stmt.enz is not None:
                    enz_base = self.get_base(stmt.enz)
                    enz_base.add_activity('catalytic')
                    enz_base.add_active_state('catalytic', stmt.enz.mods)
            elif isinstance(stmt, RasGef):
                if stmt.gef is not None:
                    gef_base = self.get_base(stmt.gef)
                    gef_base.add_activity('rasgef')
                    gef_base.add_active_state('rasgef', stmt.gef.mods)
            elif isinstance(stmt, RasGap):
                if stmt.gap is not None:
                    gap_base = self.get_base(stmt.gap)
                    gap_base.add_activity('rasgap')
                    gap_base.add_active_state('rasgap', stmt.gap.mods)
            elif isinstance(stmt, ActivityActivity):
                if stmt.subj is not None:
                    subj_base =\
                        self.get_base(stmt.subj)
                    subj_base.add_activity(stmt.subj_activity)
                    subj_base.add_active_state(stmt.subj_activity,
                                               stmt.subj.mods)
                if stmt.obj is not None:
                    obj_base =\
                        self.get_base(stmt.obj)
                    obj_base.add_activity(stmt.obj_activity)
                    obj_base.add_active_state(stmt.obj_activity,
                                              stmt.obj.mods)
            elif isinstance(stmt, ActiveForm):
                agent_base = self.get_base(stmt.agent)
                agent_base.add_activity(stmt.activity)
                agent_base.add_active_state(stmt.activity, stmt.agent.mods)

    def get_base(self, agent):
        base_agent = self.base_agents.get_create_base_agent(agent)
        return base_agent

    def reduce_activities(self):
        for stmt in self.statements:
            if isinstance(stmt, RasGef):
                if stmt.gef is not None:
                    gef_base = self.get_base(stmt.gef)
                    act_red = \
                        gef_base.get_activity_reduction(stmt.gef_activity)
                    if act_red is not None:
                        stmt.gef_activity = act_red
            elif isinstance(stmt, RasGap):
                if stmt.gap is not None:
                    gap_base = self.get_base(stmt.gap)
                    act_red = \
                        gap_base.get_activity_reduction(stmt.gap_activity)
                    if act_red is not None:
                        stmt.gap_activity = act_red
            elif isinstance(stmt, ActivityActivity):
                if stmt.subj is not None:
                    subj_base =\
                        self.get_base(stmt.subj)
                    act_red = \
                        subj_base.get_activity_reduction(stmt.subj_activity)
                    if act_red is not None:
                        stmt.subj_activity = act_red
                if stmt.obj is not None:
                    obj_base =\
                        self.get_base(stmt.obj)
                    act_red = \
                        obj_base.get_activity_reduction(stmt.obj_activity)
                    if act_red is not None:
                        stmt.obj_activity = act_red
            elif isinstance(stmt, ActiveForm):
                agent_base = self.get_base(stmt.agent)
                act_red = \
                    agent_base.get_activity_reduction(stmt.activity)
                if act_red is not None:
                    stmt.activity = act_red

    def replace_activations(self):
        for act_stmt in get_statement_type(self.statements, ActivityActivity):
            if act_stmt.subj_activity == 'kinase':
                matching = []
                for phos_stmt in get_statement_type(self.statements,
                                                    Phosphorylation):
                    if phos_stmt.enz is not None:
                        if phos_stmt.enz.matches(act_stmt.subj) and \
                            phos_stmt.sub.matches(act_stmt.obj):
                            matching.append(phos_stmt)
                if not matching:
                    continue
                mods = [ModCondition('phosphorylation',
                                     m.residue, m.position)
                       for m in matching]
                if act_stmt.relationship == 'increases':
                    is_active = True
                else:
                    is_active = False
                st = ActiveForm(Agent(act_stmt.obj.name, mods=mods),
                                act_stmt.obj_activity, is_active)
                print st
            if act_stmt.subj_activity == 'phosphatase':
                matching = []
                for phos_stmt in get_statement_type(self.statements,
                                                    Dephosphorylation):
                    if phos_stmt.enz is not None:
                        if phos_stmt.enz.matches(act_stmt.subj) and \
                            phos_stmt.sub.matches(act_stmt.obj):
                            matching.append(phos_stmt)
                if not matching:
                    continue
                mods = [ModCondition('phosphorylation',
                                     m.residue, m.position, False)
                       for m in matching]
                if act_stmt.relationship == 'increases':
                    is_active = True
                else:
                    is_active = False
                st = ActiveForm(Agent(act_stmt.obj.name, mods=mods),
                                act_stmt.obj_activity, is_active)
                print st

def get_statement_type(stmts, stmt_type):
    return [st for st in stmts if isinstance(st, stmt_type)]

def get_graph_reductions(edges):
    reductions = {}
    nodes = set()
    for s, t in edges:
        nodes.add(s)
        nodes.add(t)
    reverse_edges = {n:[] for n in nodes}
    for s, t in edges:
        reverse_edges[t].append(s)
    for n in nodes:
        next_nodes = reverse_edges[n]
        reduced_to = None
        while len(next_nodes) == 1:
            reduced_to = next_nodes[0]
            next_nodes = reverse_edges[next_nodes[0]]
        if reduced_to is not None:
            reductions[n] = reduced_to
    return reductions

if __name__ == '__main__':
    import pickle
    a = pickle.load(open('models/rasmachine/rem/model.pkl'))
    stmts = [v for k,v in a.iteritems() for v in v]
    ml = MechLinker(stmts)
    print len(ml.statements)
    ml.get_activities()
    ml.reduce_activities()
    ml.replace_activations()
