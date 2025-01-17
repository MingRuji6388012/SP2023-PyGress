from __future__ import absolute_import, print_function, unicode_literals
from builtins import dict, str
import re
import shutil
import gzip
from indra.literature import id_lookup, pubmed_client
from datetime import datetime
try:
    import lxml.etree.ElementTree as ET
except:
    import lxml.etree as ET
from os import path, walk, remove
from subprocess import call
from collections import namedtuple

from indra.db import insert_text_ref, insert_text_content, get_text_ref_by_id
from indra.util import zip_string

RE_PATT_TYPE = type(re.compile(''))
# TODO: finish this
SP_INFO = namedtuple('springer_info', ('File', 'date'))

# TODO: This might do better in util, or somewhere more gnereal ===============
def deep_find(top_dir, patt, since_date=None, verbose=False):
    '''Find files that match `patt` recursively down from `top_dir`
    
    Note: patt may be a regex string or a regex pattern object.
    '''
    if not isinstance(patt, RE_PATT_TYPE):
        patt = re.compile(patt)
    
    def is_after_time(time_stamp, path_str):
        mod_time = datetime.fromtimestamp(path.getmtime(path_str))
        if mod_time < time_stamp:
            return False
        return True
    
    def desired_files(fname):
        if since_date is not None:
            if not is_after_time(since_date, fname):
                return False
        return patt.match(path.basename(fname)) is not None
    
    def desired_dirs(dirpath):
        if since_date is not None:
            if not is_after_time(since_date, dirpath):
                return False
        return True
    
    def complete(root, leaves):
        return [path.join(root, leaf) for leaf in leaves]
    
    matches = []
    for root, dirnames, filenames in walk(top_dir):
        if verbose:
            print("Looking in %s." % root)
        # Check if the directory has been modified recently. Note that removing
        # a dirpath from dirnames will prevent walk from going into that dir.
        if since_date is not None:
            for dirpath in filter(desired_dirs, complete(root, dirnames)):
                dirnames.remove(dirpath)
        for filepath in filter(desired_files, complete(root, filenames)):
            matches.append(filepath)
    return matches


def pdftotext(pdf_file_path, txt_file_path = None):
    '''Wrapper around the command line function of the same name'''
    if txt_file_path is None:
        txt_file_path = pdf_file_path.replace('.pdf', '.txt')
    elif callable(txt_file_path):
        txt_file_path = txt_file_path(pdf_file_path)
    
    call(['pdftotext', pdf_file_path, txt_file_path])
    assert path.exists(txt_file_path),\
         "A txt file was not created or name is unknown!"
    
    return txt_file_path
#==============================================================================

def get_xml_data(pdf_path, entry_dict):
    'Get the data from the xml file if present'
    pdf_name = path.basename(pdf_path)
    art_dirname = path.abspath(pdf_path + '/'.join(4*['..']))
    xml_path_list = deep_find(art_dirname, pdf_name.replace('.pdf','\.xml.*?'))
    assert len(xml_path_list) > 0, "We have no metadata"
    if len(xml_path_list) == 1:
        xml = ET.parse(xml_path_list[0])
    elif len(xml_path_list) > 1:
        #TODO: we really should be more intelligent about this
        xml = ET.parse(xml_path_list[0])
    
    # Maybe include the journal subtitle too, in future.
    
    
    xml_data = {}
    for purpose_key, xml_label_dict in entry_dict.items():
        xml_data[purpose_key] = {}
        for table_key, xml_label in xml_label_dict.items():
            xml_data[purpose_key][table_key] = xml.find('.//' + xml_label)
            
    return xml_data

def find_other_ids(doi):
    '''Use the doi to try and find the pmid and/or pmcid.'''
    other_ids = dict(zip(['pmid', 'pmcid'], 2*[None]))
    id_dict = id_lookup(doi, 'doi')
    if id_dict['pmid'] is None:
        result_list = pubmed_client.get_ids(doi)
        for res in result_list:
            if 'PMC' in res:
                other_ids['pmcid'] = res
                # This is not very efficient...
                other_ids['pmid'] = id_lookup(res, 'pmcid')['pmid']
                break
        else:
            # This is based on a circumstantial assumption.
            # It will work for the test set, but may fail when
            # upon generalization.
            if len(result_list) == 1:
                other_ids['pmid'] = result_list[0]
            else:
                other_ids['pmid'] = None
    else:
        other_ids['pmid'] = id_dict['pmid']
        other_ids['pmcid'] = id_dict['pmcid']
        
    return other_ids

def process_one_pdf(pdf_path, txt_path):
    'Convert the pdf to txt and zip it'
    txt_path = pdftotext(pdf_path, txt_path)
    with open(txt_path, 'rb') as f_in:
        with gzip.open(txt_path + '.gz', 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    with open(txt_path, 'rb') as f:
        content = zip_string(f.read().decode('utf-8'))
    remove(txt_path) # Only a tmp file.
    return content

def zip_abstract(abst_el, ttl_el):
    'Get the abstract from the xml'
    abst_text = ET.tostring(
        abst_el, 
        encoding='utf8', 
        method='text'
        ).decode('utf8')
    return zip_string(abst_text + ttl_el.text)


def this_is_useful(ref_data):
    '''Determines if the data in the pdf is likely to be useful.
    
    Currently we are simply looking at the pmid and pmcid to see if either is
    present, however in future we should really implement a more meaningful
    method of determination.
    
    Returns: Bool
    '''
    return ref_data['pmid'] is None and ref_data['pmcid'] is None
    


def upload_springer(springer_dir, verbose = False, since_date=None):
    '''Convert the pdfs to text and upload data to AWS
    
    Note: Currently does nothing.
    '''
    txt_path = 'tmp.txt'
    uploaded = []
    if verbose:
        vprint = print
    else:
        vprint = lambda x: None
    vprint("Looking for PDF`s.")
    match_list = deep_find(
        springer_dir, 
        '.*?\.pdf', 
        verbose=verbose,
        since_date=since_date
        )
    # TODO: cache the result of the search
    vprint("Found PDF`s. Now entering loop.")
    for pdf_path in match_list:
        vprint("Examining %s" % pdf_path)
        xml_data = get_xml_data(
            pdf_path, 
            entry_dict = {
                'ref_data':{
                    'doi':'ArticleDOI',
                    'journal':'JournalTitle',
                    'pub_date':'Year',
                    'publisher':'PublisherName'
                    },
                'abst_data': {
                    'abstract':'Abstract',
                    'title':'ArticleTitle'
                    }
                }
            )
        ref_data = xml_data['ref_data']
        ref_data.update(find_other_ids(ref_data['doi'].text))
        
        if this_is_useful(ref_data):
            vprint("Skipping...")
            continue
        vprint("Processing...")
        
        # For now pmid's are the primary ID, so that should be the primary
        #text_ref_id = get_text_ref_by_id(ref_data['pmid'], 'pmid')
        #if text_ref_id is None:
            #text_ref_id = insert_text_ref(source = 'springer', **ref_data)
        content_type = None #TODO: define the content_type
        full_content = process_one_pdf(pdf_path, txt_path)
        #insert_text_content(text_ref_id, content_type, full_content)
        
        abst_data = xml_data['abst_data']
        if abst_data['abstract'] is not None:
            content_type  = None # Somthing abstract
            abst_content = zip_abstract(abst_data['abstract'], abst_data['title'])
            # TODO: Check if the abstract is already there.
            #insert_text_content(text_ref_id, content_type, abst_content)
        
        uploaded.append(pdf_path)
        vprint("Finished Processing...")
    return uploaded


if __name__ == "__main__":
    #TODO: we should probably support reading from a different
    # directory.
    record_file = 'last_update.txt'
    if path.exists(record_file):
        with open(record_file, 'r') as f:
            last_update = datetime.fromtimestamp(f.read())
    else:
        last_update = None
    
    default_dir = '/groups/lsp/darpa/springer/content/data'
    upload_springer(default_dir, verbose=True, since_date=last_update)
    
    with open(record_file, 'w') as f:
        f.write(datetime.now().timestamp())
    
    