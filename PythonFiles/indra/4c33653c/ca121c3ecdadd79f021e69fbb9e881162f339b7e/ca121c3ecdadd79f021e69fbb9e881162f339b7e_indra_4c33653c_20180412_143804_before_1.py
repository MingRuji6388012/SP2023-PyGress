import logging
import xml.etree.ElementTree as ET
import lxml
import lxml.etree
from collections import defaultdict, Counter
from indra.util import UnicodeXMLTreeBuilder as UTB
from indra.util import _require_python3
import codecs
import os
import numpy as np
import pickle
from indra.sources.medscan.processor import *
from collections import namedtuple
import os

logger = logging.getLogger('medscan')
MedscanEntity = namedtuple('MedscanEntity', ['name', 'urn', 'type',
                           'properties'])
MedscanProperty = namedtuple('MedscanProperty', ['type', 'name', 'urn'])

class MedscanRelation(object):
    """A structure representing the information contained in a Medscan
    SVO xml element as well as associated entities and properties.

    Attribues
    ----------
    uri: str
        The URI of the current document (such as a PMID)
    sec: str
        The section of the document the relation occurs in
    entities: dict
        A dictionary mapping entity IDs from the same sentence to MedscanEntity
        objects.
    tagged_sentence: str
        The sentence from which the relation was extracted, with some tagged
        phrases and annotations.
    subj: str
        The entity ID of the subject
    verb: str
        The verb in the relationship between the subject and the object
    obj: str
        The entity ID of the object
    svo_type: str
        The type of SVO relationship (for example, CONTROL indicates
        that the verb is normalized)
    """
    def __init__(self, uri, sec, entities, tagged_sentence, subj, verb, obj,
                 svo_type):
        self.uri = uri
        self.sec = sec
        self.entities = entities
        self.tagged_sentence = tagged_sentence

        self.subj = subj
        self.verb = verb
        self.obj = obj

        self.svo_type = svo_type


def process_file(filename, medscan_resource_dir, num_documents=None):
    """Process a CSXML file for its relevant information.

    The CSXML format consists of a top-level `<batch>` root element containing
    a series of `<doc>` (document) elements, in turn containing `<sec>`
    (section) elements, and in turn containing `<sent>` (sentence) elements.

    Within the `<sent>` element, a series of additional elements appear
    in the following order:
    * `<toks>`, which contains a tokenized form of the sentence in its
      text attribute
    * `<textmods>`, which describes any preprocessing/normalization done to
      the underlying text
    * `<match>` elements, each of which contains one of more `<entity>`
      elements, describing entities in the text with their identifiers.
      The local IDs of each entities are given in the `msid` attribute of
      this element; these IDs are then referenced in any subsequent SVO
      elements.
    * `<svo>` elements, representing subject-verb-object triples. SVO elements
      with a `type` attribute of `CONTROL` represent normalized regulation
      relationships; they often represent the normalized extraction of the
      immediately preceding (but unnormalized SVO element). However, in some
      cases there can be a "CONTROL" SVO element without its parent immediately
      preceding it.
    """
    mp = MedscanProcessor(medscan_resource_dir)

    logger.info("Parsing %s to XML" % filename)
    pmid = None
    sec = None
    tagged_sent = None
    svo_list = []
    doc_counter = 0
    entities = {}
    match_text = None
    in_prop = False
    last_relation = None
    property_entities = []
    property_name = None

    # Got through the document again and extract statements
    with codecs.open(filename, 'rb') as f:
        for event, elem in lxml.etree.iterparse(f, events=('start', 'end'),
                                                encoding='utf-8',
                                                recover=True):
            # If opening up a new doc, set the PMID
            if event == 'start' and elem.tag == 'doc':
                pmid = elem.attrib.get('uri')
            # If getting a section, set the section type
            elif event == 'start' and elem.tag == 'sec':
                sec = elem.attrib.get('type')
            # Set the sentence context
            elif event == 'start' and elem.tag == 'sent':
                tagged_sent = elem.attrib.get('msrc')
                last_relation = None  # Only interested within sentences
                entities = {}
            elif event == 'start' and elem.tag == 'match':
                match_text = elem.attrib.get('chars')
            elif event == 'start' and elem.tag == 'entity':
                if not in_prop:
                    ent_id = elem.attrib['msid']
                    ent_urn = elem.attrib.get('urn')
                    ent_type = elem.attrib['type']
                    entities[ent_id] = MedscanEntity(match_text, ent_urn,
                                                     ent_type, {})
                else:
                    ent_type = elem.attrib['type']
                    ent_urn = elem.attrib['urn']
                    ent_name = elem.attrib['name']
                    property_entities.append(MedscanEntity(ent_name, ent_urn,
                                                          ent_type, None))
            elif event == 'start' and elem.tag == 'svo':
                subj = elem.attrib.get('subj')
                verb = elem.attrib.get('verb')
                obj = elem.attrib.get('obj')
                svo_type = elem.attrib.get('type')
                svo = {'uri': pmid,
                       'sec': sec,
                       'text': tagged_sent,
                       'entities': entities}
                svo.update(elem.attrib)

                relation = MedscanRelation(
                                       uri=pmid,
                                       sec=sec,
                                       tagged_sentence=tagged_sent,
                                       entities=entities,
                                       subj=subj,
                                       verb=verb,
                                       obj=obj,
                                       svo_type=svo_type,
                                      )
                if svo_type == 'CONTROL':
                    mp.process_relation(relation, last_relation)
                else:
                    # Sometimes a CONTROL SVO can be after an unnormalized SVO
                    # that is a more specific but less uniform version of the
                    # same extracted statement.
                    last_relation = relation
            elif event == 'start' and elem.tag == 'prop':
                in_prop = True
                property_name = elem.attrib.get('name')
                property_entities = []
            elif event == 'end' and elem.tag == 'prop':
                in_prop = False
                entities[ent_id].properties[property_name] = property_entities
            elif event == 'end' and elem.tag == 'doc':
                doc_counter += 1
                # Give a status update
                if doc_counter % 100 == 0:
                    print("Processed %d documents"
                          % doc_counter)
                if num_documents is not None and doc_counter >= num_documents:
                    break

    print("Done processing %d documents" % doc_counter)
    return mp