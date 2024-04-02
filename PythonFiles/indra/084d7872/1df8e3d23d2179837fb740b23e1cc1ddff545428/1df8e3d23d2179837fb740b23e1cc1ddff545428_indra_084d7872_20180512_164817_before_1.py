import logging
import nltk
import os
import zlib
import codecs
from indra import get_config
import shutil
import subprocess
import tempfile
import re

logger = logging.getLogger('isi')

nxml2txt_path = get_config('NXML2TXT_PATH')
python2_path = get_config('PYTHON2_PATH')

class IsiPreprocessor(object):
    """Preprocesses a set of documents, one by one, and adds the preprocessed
    text to a temporary directory in a format suitable for the ISI reader.
    The ISI reader requires plain text with one sentence per line.

    Attributes
    ----------
    preprocessed_dir: str
        The directory holding the literature text preprocessed and sentence
        tokenized in a format suitable for the ISI reader
    next_file_id: int
        The next file with preprocessed text will be named next_file_id.txt
    pmids: dict
        A dictionary mapping file ids to the pmid of the text corresponding
        to that file, can be None if unknown
    extra_annotations: dict
        A dictionary mapping file ids to a (possibly empty) dictionary with
        additional annotations to include for statements extracted from this
        document
    """

    def __init__(self, preprocessed_dir):
        preprocessed_dir = os.path.abspath(preprocessed_dir)
        self.preprocessed_dir = preprocessed_dir
        self.next_file_id = 1
        self.pmids = {}
        self.extra_annotations = {}

        # This directory should be empty
        contents = os.listdir(preprocessed_dir)
        if len(contents) != 0:
            logger.warning('IsiPreprocessor should get an empty directory in' +
                           ' which to store preprocessed files.')

    def preprocess_plain_text_string(self, text, pmid, extra_annotations):
        """Preprocesses plain text by tokenizing into sentences and writing
        each sentence on its own line in a plain text file. All other
        preprocessing functions ultimately call this one.

        Parameters
        ----------
        text: str
            The plain text of the article of abstract
        pmid: str
            The pmid from which it comes, or None if not specified
        extra_annotations: dict
            Extra annotations to be added to each statement, possibly including
            metadata about the source (annotations with the key "interaction"
            will be overridden)
        """
        output_file = str(self.next_file_id) + '.txt'
        output_file = os.path.join(self.preprocessed_dir, output_file)

        # Tokenize sentence
        sentences = nltk.sent_tokenize(text)

        # Write sentences to text file
        first_sentence = True
        with codecs.open(output_file, 'w', encoding='utf-8') as f:
            for sentence in sentences:
                if not first_sentence:
                    f.write('\n')
                f.write(sentence.rstrip())
                first_sentence = False

        # Store annotations
        self.pmids[self.next_file_id] = pmid
        self.extra_annotations[self.next_file_id] = extra_annotations

        # Increment file id
        self.next_file_id += 1

    def preprocess_plain_text_file(self, filename, pmid, extra_annotations):
        """
        Preprocess a plain text file for use with ISI, by creating a new text
        file with one sentence per line.

        Parameters
        ----------
        text: str
            The plain text of the article of abstract
        pmid: str
            The pmid from which it comes, or None if not specified
        extra_annotations: dict
            Extra annotations to be added to each statement, possibly including
            metadata about the source (annotations with the key "interaction"
            will be overridden)
        """
        with codecs.open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            self.preprocess_plain_text_string(content, pmid,
                                              extra_annotations)


    def preprocess_nxml_file(self, filename, pmid, extra_annotations):
        """Preprocess an nxml file for use with ISI, by creating a plain
        text file with one sentence per line. Not yet implemented.

        Parameters
        ----------
        filename: str
            Filename of an nxml file to process
        pmid: str
            The pmid from which it comes, or None if not specified
        extra_annotations: dict
            Extra annotations to be added to each statement, possibly including
            metadata about the source (annotations with the key "interaction"
            will be overridden)
        """
        # Create a temporary directory
        tmp_dir = tempfile.mkdtemp('indra_isi_nxml2txt_output')

        # Run nxml2txt
        if nxml2txt_path is None:
            logger.error('NXML2TXT_PATH not specified in config file or ' + 
                         'environment variable')
            return
        if python2_path is None:
            logger.error('PYTHON2_PATH not specified in config file or ' + 
                         'environment variable')
        else:
            txt_out = os.path.join(tmp_dir, 'out.txt')
            so_out = os.path.join(tmp_dir, 'out.so')
            command = [python2_path,
                       os.path.join(nxml2txt_path, 'nxml2txt'),
                       filename,
                       txt_out,
                       so_out]
            ret = subprocess.call(command)
            if ret != 0:
                logger.warning('nxml2txt returned non-zero error code')

            with open(txt_out, 'r') as f:
                txt_content = f.read()

        # Remote temporary directory
        shutil.rmtree(tmp_dir)

        # We need to remove some common LaTEX commands from the converted text
        # or the reader will get confused
        cmd1 = '[^ \{\}]+\{[^\{\}]+\}\{[^\{\}]+\}'
        cmd2 = '[^ \{\}]+\{[^\{\}]+\}'
        txt_content = re.sub(cmd1, '', txt_content)
        txt_content = re.sub(cmd2, '', txt_content)

        with open('tmp.txt', 'w') as f:
            f.write(txt_content)

        # Prepocess text extracted from nxml
        self.preprocess_plain_text_string(txt_content, pmid, extra_annotations)


    def preprocess_abstract_list(self, abstract_list):
        """Preprocess a list of abstracts in database pickle dump format.
        For each abstract, creates a plain text file with one sentence per
        line, and stores metadata to be included with each statement from
        that abstract.

        Parameters
        ----------
        abstract_list: list[dict]
            Compressed abstracts with corresopnding metadata in INDRA database
            pickle dump format.
        """
        for abstract_struct in abstract_list:
            abs_format = abstract_struct['format']
            content_type = abstract_struct['text_type']
            content_zipped = abstract_struct['content']
            tcid = abstract_struct['tcid']
            trid = abstract_struct['trid']

            assert(abs_format == 'text')
            assert(content_type == 'abstract')

            pmid = None  # Don't worry about pmid for now
            extra_annotations = {'tcid': tcid, 'trid': trid}

            # Uncompress content
            content = zlib.decompress(content_zipped,
                                      zlib.MAX_WBITS+16).decode('utf-8')

            self.preprocess_plain_text_string(content, pmid, extra_annotations)