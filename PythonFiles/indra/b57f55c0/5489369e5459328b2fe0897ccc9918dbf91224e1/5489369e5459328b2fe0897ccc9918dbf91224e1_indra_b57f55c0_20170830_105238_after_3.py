import zlib
import logging
from io import BytesIO
import xml.etree.ElementTree as ET
from indra.db import get_aws_db
from indra.literature import pubmed_client
from indra.util import zip_string, unzip_string, UnicodeXMLTreeBuilder as UTB
from indra.db.update_content import _get_ftp_connection, ftp_blocksize
import functools
import multiprocessing as mp

db = get_aws_db()

logger = logging.getLogger('update_medline')

def get_deleted_pmids():
    ftp = _get_ftp_connection('/pubmed')
    file_gz = BytesIO()
    ftp.retrbinary('RETR deleted.pmids.gz', callback=lambda b: file_gz.write(b),
                   blocksize=ftp_blocksize)
    pmid_list = [line.strip()
                 for line in unzip_string(file_gz.getvalue()).split('\n')]
    ftp.close()
    return pmid_list

def _upload_xml_file(xml_file, deleted_pmids=None):
    ftp = _get_ftp_connection('/pubmed/baseline')
    #for ix, xml_file in enumerate(xml_files):
    # Download the Gzipped content into a BytesIO
    gzf_bytes = BytesIO()
    #print("Downloading %s (%d of %d)" % (xml_file, ix+1, len(xml_files)))
    print("Downloading %s" % (xml_file))
    ftp.retrbinary('RETR %s' % xml_file,
                            callback=lambda b: gzf_bytes.write(b),
                            blocksize=ftp_blocksize)
    # Unzip the BytesIO into uncompressed bytes
    print("Unzipping")
    xml_bytes = zlib.decompress(gzf_bytes.getvalue(), 16+zlib.MAX_WBITS)
    # Convert the bytes into an XML ElementTree
    print("Parsing XML metadata")
    tree = ET.XML(xml_bytes, parser=UTB())
    # Get the article metadata from the tree
    article_info = pubmed_client.get_metadata_from_xml_tree(
                    tree, get_abstracts=True, prepend_title=False)
    print("%d PMIDs in XML dataset" % len(article_info))
    # Convert the article_info into a list of tuples for insertion into
    # the text_ref table
    text_ref_records = []
    text_content_info = {}
    valid_pmids = set(article_info.keys()).difference(set(deleted_pmids))
    print("%d valid PMIDs" % len(valid_pmids))
    existing_pmids = set(db.get_all_pmids())
    print("%d existing PMIDs in text_refs" % len(existing_pmids))
    pmids_to_add = valid_pmids.difference(existing_pmids)
    print("%d PMIDs to add to text_refs" % len(pmids_to_add))
    for pmid in pmids_to_add:
        pmid_data = article_info[pmid]
        rec = (pmid, pmid_data.get('pmcid'), pmid_data.get('doi'),
               pmid_data.get('pii'))
        text_ref_records.append(tuple([None if not r else r.encode('utf8')
                                      for r in rec]))
        abstract = pmid_data.get('abstract')
        # Make sure it's not an empty or whitespace-only string
        if abstract and abstract.strip():
            abstract_gz = zip_string(abstract)
            text_content_info[pmid] = \
                            (b'pubmed', b'text', b'abstract', abstract_gz)
    # Copy the text ref information over
    db.copy('text_ref', text_ref_records, ('pmid', 'pmcid', 'doi', 'pii'))

    # Build a dict mapping PMIDs to text_ref IDs
    pmid_list = list(text_content_info.keys())
    tref_list = db.select('text_ref', db.TextRef.pmid==pmid_list)
    pmid_tr_dict = {pmid:trid for (pmid, trid) in 
                    db.get_values(tref_list, ['pmid', 'id'])}

    # Add the text_ref IDs to the content to be inserted
    text_content_records = []
    for pmid, tc_data in text_content_info.items():
        tr_id = pmid_tr_dict[pmid]
        text_content_records.append((tr_id,) + tc_data)
    # Copy into database
    db.copy(
        'text_content', 
        text_content_records,
        cols=('text_ref_id', 'source', 'format', 'text_type', 'content')
        )
    ftp.close()
    return True

def download_baseline():
    # Get the list of deleted PMIDs
    deleted_pmids = get_deleted_pmids()
    # Get the list of .xml.tar.gz files
    ftp = _get_ftp_connection('/pubmed/baseline')
    xml_files = [f[0] for f in ftp.mlsd() if f[0].endswith('.xml.gz')]
    ftp.close()
    pool = mp.Pool(4)
    functools.partial(_upload_xml_file, deleted_pmids=deleted_pmids)
    pool.map(_upload_xml_file, xml_files)



def update_text_refs():
    pass

if __name__ == '__main__':
    #db.drop_tables()
    #db.create_tables()
    download_baseline()
    """
    with open('medline17n0001.xml', 'rb') as f:
        content_bytes = f.read()
    tree = ET.XML(content_bytes, parser=UTB())
    article_info = pubmed_client.get_metadata_from_xml_tree(
                            tree, get_abstracts=True, prepend_title=False)
    """

    # High-level content update procedure
    # 1. Download MEDLINE baseline, will contain all PMIDs, abstracts,
    #    other info
    # 2. Download PMC, update text refs with PMCIDs where possible, with
    #    update commands.
    # 3. Add PMC-OA content.
    # 4. Add PMC-author manuscript information, updating files with manuscript
    #    IDs and content.
    # 5. (Optional): Run script to check for/obtain DOIs for those that are
    #    missing
    # 6. Obtain Elsevier XML for Elsevier articles
    # 7. Obtain Springer content for Springer articles
    # 8. Obtain scraped PDF content for other articles available via OA-DOI.
