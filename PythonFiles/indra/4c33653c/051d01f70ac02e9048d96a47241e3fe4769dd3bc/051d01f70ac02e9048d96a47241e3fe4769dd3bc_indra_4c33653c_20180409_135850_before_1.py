import logging
import xml.etree.ElementTree as ET
from collections import defaultdict, Counter
from indra.util import UnicodeXMLTreeBuilder as UTB
from indra.util import _require_python3
import codecs
import os

logger = logging.getLogger('medscan')

class MedscanRelation:
    def __init__(self, pmid, tagged_sentence):
        self.pmid = pmid
        self.tagged_sentence = tagged_sentence


def process_file(filename, num_documents=None):
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

    logger.info("Parsing %s to XML" % filename)
    pmid = None
    sec = None
    tagged_sent = None
    svo_list = []
    doc_counter = 0
    entities = {}
    match_text = None
    in_prop = False
    # TODO: Figure out what's going on with Unicode errors!
    with codecs.open(filename, 'r', encoding='latin_1') as f:
        for event, elem in ET.iterparse(f, events=('start', 'end')):
            # If opening up a new doc, set the PMID
            if event == 'start' and elem.tag == 'doc':
                pmid = elem.attrib.get('uri')
            # If getting a section, set the section type
            elif event == 'start' and elem.tag == 'sec':
                sec = elem.attrib.get('type')
            # Set the sentence context
            elif event == 'start' and elem.tag == 'sent':
                entities = {}
                tagged_sent = elem.attrib.get('msrc')
            elif event == 'start' and elem.tag == 'match':
                match_text = elem.attrib.get('chars')
            elif event == 'start' and elem.tag == 'entity' and not in_prop:
                ent_id = elem.attrib['msid']
                ent_urn = elem.attrib.get('urn')
                ent_type = elem.attrib['type']
                entities[ent_id] = (match_text, ent_urn, ent_type)
            elif event == 'start' and elem.tag == 'svo':
                svo = {'uri': pmid,
                       'sec': sec,
                       'text': tagged_sent,
                       'entities': entities}
                svo.update(elem.attrib)
                svo_list.append(svo)
            # TODO: Figure out if there's something better we can do with
            # properties
            elif event == 'start' and elem.tag == 'prop':
                in_prop = True
            elif event == 'end' and elem.tag == 'prop':
                in_prop = False
            elif event == 'end' and elem.tag == 'doc':
                doc_counter += 1
                # Give a status update
                if doc_counter % 100 == 0:
                    print("Processed %d documents" % doc_counter)
                if num_documents is not None and doc_counter >= num_documents:
                    break

    print("Done processing %d documents" % doc_counter)
    # Filter to CONTROL events
    ctrl = [s for s in svo_list if s['type'] == 'CONTROL']
    return ctrl

if __name__ == '__main__':
    #fname = '~/Downloads/medscan/test_file.csxml'
    fname = '~/Downloads/medscan/DARPAcorpus.csxml'
    fname = os.path.expanduser(fname)
    num_documents = None
    p = process_file(fname, num_documents)