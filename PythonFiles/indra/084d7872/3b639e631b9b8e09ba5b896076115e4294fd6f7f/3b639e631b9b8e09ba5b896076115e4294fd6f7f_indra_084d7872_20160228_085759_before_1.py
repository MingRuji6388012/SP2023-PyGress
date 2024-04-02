import re
import sys
import pickle
import warnings
import itertools
import collections

from indra.java_vm import autoclass, JavaException, cast

from indra.databases import hgnc_client
from indra.statements import *

warnings.simplefilter("always")


class BiopaxProcessor(object):
    def __init__(self, model):
        self.model = model
        self.statements = []
        self._hgnc_cache = self._load_hgnc_cache()

    def get_complexes(self, force_contains=None):
        for obj in self.model.getObjects().toArray():
            bpe = cast_biopax_element(obj)
            if not is_complex(bpe):
                continue
            citation = self._get_citation(bpe)
            source_id = bpe.getUri()
            members = self._get_complex_members(bpe)
            if members is not None:
                complexes = get_combinations(members)
                for c in complexes:
                    ev = Evidence(source_api='biopax',
                                  pmid=citation,
                                  source_id=source_id)
                    self.statements.append(Complex(c, ev))

    def get_phosphorylation(self, force_contains=None):
        stmts = self._get_generic_modification('phospho', 
                                               force_contains=force_contains)
        for s in stmts:
            self.statements.append(Phosphorylation(*s))

    def get_dephosphorylation(self, force_contains=None):
        stmts = self._get_generic_modification('phospho', mod_gain=False, 
                                               force_contains=force_contains)
        for s in stmts:
            self.statements.append(Dephosphorylation(*s))

    def get_acetylation(self, force_contains=None):
        stmts = self._get_generic_modification('acetyl', 
                                               force_contains=force_contains)
        for s in stmts:
            self.statements.append(Acetylation(*s))

    def get_glycosylation(self, force_contains=None):
        stmts = self._get_generic_modification('glycosyl', 
                                               force_contains=force_contains)
        for s in stmts:
            self.statements.append(Glycosylation(*s))

    def get_palmitoylation(self, force_contains=None):
        stmts = self._get_generic_modification('palmitoyl', 
                                               force_contains=force_contains)
        for s in stmts:
            self.statements.append(Palmitoylation(*s))

    def get_activity_modification(self, force_contains=None):
        mcc = bpp('constraint.ModificationChangeConstraint')
        mcct = bpp('constraint.ModificationChangeConstraint$Type')
        mod_filter = 'residue modification, active'
        for relationship in ['increases', 'decreases']:
            p = self._construct_modification_pattern()
            if relationship == 'increases':
                rel = mcct.GAIN
            else:
                rel = mcct.LOSS
            p.add(mcc(rel, mod_filter),
                  "input simple PE", "output simple PE")

            s = bpp('Searcher')
            res = s.searchPlain(self.model, p)
            res_array = [match_to_array(m) for m in res.toArray()]
        
            for r in res_array:
                monomer = self._get_agents_from_entity(
                    r[p.indexOf('changed generic ER')])
                if force_contains is not None:
                    if momomer not in force_contains:
                        continue
                citation = self._get_citation(r[p.indexOf('Conversion')])
                ev = Evidence(source_api='biopax', pmid=citation)
                out_pe = r[p.indexOf('output PE')]
                activity = 'Activity'
                mod, mod_pos = self._get_modification_site(out_pe)
                if mod:
                    stmt = ActivityModification(monomer, mod, mod_pos, 
                                            relationship, activity,
                                            evidence=ev)
                    self.statements.append(stmt)

    def _get_complex_members(self, cplx):
        # Get the members of a complex. This is returned as a list 
        # of lists since complexes can contain other complexes. The 
        # list of lists solution allows us to preserve this.
        member_pes = cplx.getComponent().toArray()
        # Some complexes do not have any members explicitly listed
        if len(member_pes) == 0:
            warnings.warn('Complex "%s" has no members.' % 
                cplx.getDisplayName())
            return None
        members = []
        for m in member_pes:
            if is_complex(m):
                ms = self._get_complex_members(m)
                if ms is None:
                    return None
                ms = [self._get_agents_from_entity(mm) for mm in ms]
                members.append(ms)
            else:
                ma = self._get_agents_from_entity(m)
                members.append(ma)
        return members
    
    @staticmethod
    def _get_modification_site(modPE):
        # Do we need to look at EntityFeatures?
        modMF = [mf for mf in modPE.getFeature().toArray()
                 if isinstance(mf, bpimpl('ModificationFeature'))]
        mod_pos = []
        mod = []

        for mf in modMF:
            mod1, mod_pos1 = BiopaxProcessor._extract_mod_from_feature(mf)
            mod.append(mod1)
            mod_pos.append(mod_pos1)
        return mod, mod_pos 

    def _get_generic_modification(self, mod_filter=None, mod_gain=True, 
                                  force_contains=None):
        mcc = bpp('constraint.ModificationChangeConstraint')
        mcct = bpp('constraint.ModificationChangeConstraint$Type')
        # Start with a generic modification pattern
        p = self._construct_modification_pattern()
        # The modification type should contain the filter string
        if mod_filter is not None:
            if mod_gain:
                mod_gain_const = mcct.GAIN
            else:
                mod_gain_const = mcct.LOSS
            p.add(mcc(mod_gain_const, mod_filter),
                      "input simple PE", "output simple PE")

        s = bpp('Searcher')
        res = s.searchPlain(self.model, p)
        res_array = [match_to_array(m) for m in res.toArray()]
        stmts = []
        for r in res_array:
            controller = r[p.indexOf('controller PE')]
            inputpe = r[p.indexOf('input PE')]
            conversion = r[p.indexOf('Conversion')]
            control = r[p.indexOf('Control')]
            if is_complex(controller):
                warnings.warn('Cannot handle complex enzymes.')
                continue
            if is_complex(inputpe):
                warnings.warn('Cannot handle complex substrates.')
                continue
            citation = self._get_citation(conversion)
            source_id = control.getUri()
            
            enzs = listify(self._get_agents_from_entity(controller))
            subs = listify(self._get_agents_from_entity(inputpe))
            for enz, sub in itertools.product(enzs, subs):
                # If neither the enzyme nor the substrate is contained then skip
                if force_contains is not None:
                    if (enz.name not in force_contains) and \
                        (sub.name not in force_contains):
                        continue
                ev = Evidence(source_api='biopax', pmid=citation,
                          source_id=source_id)

            # Get the modification (s)
            # Should this be simple PE?
            if mod_gain:
                modPE = r[p.indexOf('output simple PE')]
            else:
                modPE = r[p.indexOf('input simple PE')]

            # TODO: this should be based on the difference of input/output PE
            # and not simply the output PE.
            # TODO: the mod filter does not catch cases where modificantions
            # other than the specified one are also gained or lost.
            # We should introduce another filter here to not include those 
            # modifications.
            mod, mod_pos = self._get_modification_site(modPE)
            for m, mp in zip(mod, mod_pos):
                if m  == 'Active':
                    # Skip activity as a modification state
                    continue
                stmt = (enz, sub, m, mp, ev)
                stmts.append(stmt)
        return stmts

    @staticmethod
    def _get_citation(bpe):
        evidence = bpe.getEvidence().toArray()
        refs = []
        for e in evidence:
            pub = e.getXref().toArray()
            for p in pub:
                if p.getDb() is None:
                    refs.append(p.getUrl().toArray())
                else:
                    refs.append('%s:%s' % (p.getDb(), p.getId()))
        return refs

    @staticmethod
    def _construct_modification_pattern():
        pb = bpp('PatternBox')
        cb = bpp('constraint.ConBox')
        flop = bpp('constraint.Field$Operation')
        rt = bpp('util.RelType')
        tp = bpp('constraint.Type')
        cs = bpp('constraint.ConversionSide')
        cst = bpp('constraint.ConversionSide$Type')
        pt = bpp('constraint.Participant')

        # The following constraints were pieced together based on the
        # following two higher level constrains: pb.controlsStateChange(),
        # pb.controlsPhosphorylation(). The pattern cannot be started
        # from EntityReference because it cannot be instantiated.
        # Therefore starting with ProteinReference as controller ER
        p = bpp('Pattern')(bpimpl('ProteinReference')().getModelInterface(),
                           "controller ER")
        # Getting the generic controller EntityReference
        p.add(cb.linkedER(True), "controller ER", "generic controller ER")
        # Getting the controller PhysicalEntity
        p.add(cb.erToPE(), "generic controller ER", "controller simple PE")
        # Getting to the complex controller PhysicalEntity
        p.add(cb.linkToComplex(), "controller simple PE", "controller PE")
        # Getting the control itself
        p.add(cb.peToControl(), "controller PE", "Control")
        # Link the control to the conversion that it controls
        p.add(cb.controlToConv(), "Control", "Conversion")
        # The controller shouldn't be a participant of the conversion
        p.add(bpp('constraint.NOT')(cb.participantER()),
              "Conversion", "controller ER")
        # Get the input participant of the conversion
        p.add(pt(rt.INPUT, True), "Control", "Conversion", "input PE")
        # Make sure the participant is a protein
        p.add(tp(bpimpl('Protein')().getModelInterface()), "input PE")
        # Get the specific PhysicalEntity
        p.add(cb.linkToSpecific(), "input PE", "input simple PE")
        # Get the EntityReference for the converted entity
        p.add(cb.peToER(), "input simple PE", "changed generic ER")
        # Link to the other side of the conversion
        p.add(cs(cst.OTHER_SIDE), "input PE", "Conversion", "output PE")
        # Make sure the two sides are not the same
        p.add(bpp('constraint.Equality')(False), "input PE", "output PE")
        # Make sure the output is a Protein
        p.add(tp(bpimpl('Protein')().getModelInterface()), "output PE")
        # Get the specific PhysicalEntity
        p.add(cb.linkToSpecific(), "output PE", "output simple PE")
        # Link output to the converted EntityReference
        p.add(cb.peToER(), "output simple PE", "changed generic ER")
        # Get the specific converted EntityReference
        p.add(cb.linkedER(False), "changed generic ER", "changed ER")
        p.add(bpp('constraint.NOT')(cb.linkToSpecific()),
              "input PE", "output simple PE")
        p.add(bpp('constraint.NOT')(cb.linkToSpecific()),
              "output PE", "input simple PE")
        return p

    def _get_agents_from_entity(self, bpe):
        # If the entity has members (like a protein family),
        # we iterate over them
        members = bpe.getMemberPhysicalEntity().toArray()
        if members:
            agents = []
            for m in members:
                agents.append(self._get_agents_from_entity(m))
            return agents
        # If it is a single entity, we get its name and database
        # references
        name = self._get_entity_name(bpe)
        db_refs = self._get_db_refs(bpe)
        mods, mod_sites = self._get_entity_mods(bpe)
        agent = Agent(name, db_refs=db_refs, mods=mods, mod_sites=mod_sites)
        return agent

    def _get_entity_mods(self, bpe):
        """Get all the modifications of an entity in INDRA format"""
        feats = bpe.getFeature().toArray()
        mod_types = []
        mod_poss = []
        for f in feats:
            if is_modification(f):
                mod_type, mod_pos = self._extract_mod_from_feature(f)
                if mod_type is not None:
                    if mod_type == 'Active':
                        # Skip activity as a modification state for now
                        continue
                    mod_types.append(mod_type)
                    mod_poss.append(mod_pos)
        return mod_types, mod_poss
    
    @staticmethod
    def _extract_mod_from_feature(mf):
        """Extract the type of modification and the position from
        a ModificationFeature object in the INDRA format."""
        # ModificationFeature / SequenceModificationVocabulary
        mf_type = mf.getModificationType()
        if mf_type is None:
            warnings.warn('Modification type missing for  %s' % mf.getUri())
            return None, None
        if len(mf_type.getTerm().toArray()) != 1:
            warnings.warn('Other than one modification term')
        mf_type = mf_type.getTerm().toArray()[0]
        try:
            mod_type = BiopaxProcessor._mftype_dict[mf_type]
        except KeyError:
            warnings.warn('Unknown modification type %s' % mf_type)
            return None, None

        # getFeatureLocation returns SequenceLocation, which is the
        # generic parent class of SequenceSite and SequenceInterval.
        # Here we need to cast to SequenceSite in order to get to
        # the sequence position.
        mf_pos = mf.getFeatureLocation()
        if mf_pos is not None:
            mf_site = cast(bp('SequenceSite'), mf_pos)
            mf_pos_status = mf_site.getPositionStatus()
            if mf_pos_status is None:
                mod_pos = None
            elif mf_pos_status and mf_pos_status.toString() != 'EQUAL':
                warnings.warn('Modification site position is %s' %
                              mf_pos_status.toString())
            else:
                mod_pos = mf_site.getSequencePosition()
        else:
            mod_pos = None
        return mod_type, mod_pos

    def _get_db_refs(self, bpe):
        if is_protein(bpe):
            hgnc_id = self._get_hgnc_id(bpe)
            uniprot_id = self._get_uniprot_id(bpe)
            db_refs = {'HGNC': hgnc_id, 'UP': uniprot_id}
        elif is_small_molecule(bpe):
            # TODO: get ChEBI ID
            chebi_id = 999
            db_refs = {'CHEBI': chebi_id}
        else:
            warnings.warn('Unhandled entity type %s' %
                bpe.getModelInterface().getString())
            db_refs = {}
        return db_refs

    def _get_entity_name(self, bpe):
        if is_protein(bpe):
            hgnc_id = self._get_hgnc_id(bpe)
            if hgnc_id is not None:
                name = self._get_hgnc_name(hgnc_id)
            else:
                name = bpe.getDisplayName()
        elif is_small_molecule(bpe):
            name = bpe.getDisplayName()
        else:
            warnings.warn('Unhandled entity type %s' %
                bpe.getModelInterface().getString())
            name = bpe.getDisplayName()
        
        # Canonicalize name
        name = re.sub(r'[^\w]', '_', name)
        if re.match('[0-9]', name) is not None:
            name = 'p' + name
        return name
    
    @staticmethod
    def _get_uniprot_id(bpe):
        # There is sometimes more than one UniProt ID reported.
        # This usually corresponds to the primary accession ID and one or more
        # secondary accession IDs (these IDs are from deprecated entries that
        # have been merged into the primary.
        bp_entref = bpe.getEntityReference()
        xrefs = bp_entref.getXref().toArray()
        uniprot_refs = [x for x in xrefs if x.getDb() == 'UniProt Knowledgebase']
        uniprot_ids = [r.getId() for r in uniprot_refs]
        if not uniprot_ids:
            return None
        elif len(uniprot_ids) == 1:
            return uniprot_ids[0]
        else:
            return uniprot_ids

    @staticmethod
    def _get_hgnc_id(bpe):
        bp_entref = bpe.getEntityReference()
        xrefs = bp_entref.getXref().toArray()
        hgnc_refs = [x for x in xrefs if x.getDb() == 'HGNC']
        hgnc_id = None
        for r in hgnc_refs:
            try:
                hgnc_id = int(r.getId())
            except ValueError:
                continue
        return hgnc_id

    def _get_hgnc_name(self, hgnc_id):
        try:
            hgnc_name = self._hgnc_cache[hgnc_id]
        except KeyError:
            hgnc_name = hgnc_client.get_hgnc_name(hgnc_id)
            self._hgnc_cache[hgnc_id] = hgnc_name
        return hgnc_name

    def _load_hgnc_cache(self):
        try:
            fh = open('hgnc_cache.pkl', 'rb')
        except IOError:
            return {}
        return pickle.load(fh)

    def _dump_hgnc_cache(self):
        with open('hgnc_cache.pkl', 'wb') as fh:
            pickle.dump(self._hgnc_cache, fh)
    
    def print_statements(self):
        for i, stmt in enumerate(self.statements):
            print "%s: %s" % (i, stmt)

    _mftype_dict = {
        'phosphorylated residue': 'Phosphorylation',
        'O-phospho-L-serine': 'PhosphorylationSerine',
        'O-phospho-L-threonine': 'PhosphorylationThreonine',
        'O-phospho-L-tyrosine': 'PhosphorylationTyrosine',
        'O4\'-phospho-L-tyrosine': 'PhosphorylationTyrosine',
        'residue modification, active': 'Active'
        }

# Functions for accessing frequently used java classes with shortened path
def bp(path):
    prefix = 'org.biopax.paxtools.model.level3'
    classname = prefix + '.' + path
    return autoclass_robust(classname)


def bpp(path):
    prefix = 'org.biopax.paxtools.pattern'
    classname = prefix + '.' + path
    return autoclass_robust(classname)


def bpimpl(path):
    prefix = 'org.biopax.paxtools.impl.level3'
    postfix = 'Impl'
    classname = prefix + '.' + path + postfix
    return autoclass_robust(classname)


def autoclass_robust(path):
    try:
        cl = autoclass(path)
    except JavaException:
        print 'Could not instantiate ' + path
        return None
    return cl


def cast_biopax_element(bpe):
    """ Casts a generic BioPAXElement object into a specific type.
    This is useful when a search only returns generic elements. """
    return cast(bpe.getModelInterface().getName(), bpe)


def match_to_array(m):
    """ Returns an array consisting of the elements obtained from a pattern
    search cast into their appropriate classes. """
    return [cast_biopax_element(m.get(i)) for i in range(m.varSize())]

def is_complex(pe):
    """Return True if the physical entity is a complex"""
    val = isinstance(pe, bp('Complex')) or \
            isinstance(pe, bpimpl('Complex'))
    return val

def is_protein(pe):
    """Return True if the physical entity is a protein"""
    val = isinstance(pe, bp('Protein')) or \
            isinstance(pe, bpimpl('Protein'))
    return val

def is_small_molecule(pe):
    """Return True if the physical entity is a small molecule"""
    val = isinstance(pe, bp('SmallMolecule')) or \
            isinstance(pe, bpimpl('SmallMolecule'))
    return val

def is_modification(fe):
    """Return True if the feature is a modification"""
    val = isinstance(fe, bp('ModificationFeature')) or \
            isinstance(fe, bpimpl('ModificationFeature'))
    return val

def listify(lst):
    if not isinstance(lst, collections.Iterable):
        return [lst]
    else:
        return lst

def list_listify(lst):
    return [l if isinstance(l, collections.Iterable) else [l] for l in lst]

def get_combinations(lst):
    return itertools.product(*list_listify(lst))