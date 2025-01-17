"""Objects for interacting with bulk nlp reading tools."""
from __future__ import absolute_import, print_function, unicode_literals
from builtins import dict, str

import sys
import shutil
import re
import tempfile
import glob
import json
import logging
import subprocess
import zlib
from os import path, mkdir, environ, listdir, remove
from io import BytesIO
from datetime import datetime
from multiprocessing import Pool
from platform import system

from indra import get_config
from indra.util import zip_string
from indra.sources import sparser, reach


logger = logging.getLogger('readers')

# Set a character limit for reach reading
CONTENT_CHARACTER_LIMIT = 5e5
CONTENT_MAX_SPACE_RATIO = 0.5


def _get_dir(*args):
    dirname = path.join(*args)
    if path.isabs(dirname):
        dirpath = dirname
    elif path.exists(dirname):
        dirpath = path.abspath(dirname)
    else:
        dirpath = path.join(path.dirname(path.abspath(__file__)), dirname)
    if not path.exists(dirpath):
        mkdir(dirpath)
    return dirpath


def _time_stamp():
    return datetime.now().strftime("%Y%m%d%H%M%S")


def _get_mem_total():
    if system() == 'Linux':
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
        tot_entry = [line for line in lines if line.startswith('MemTotal')][0]
        ret = int(tot_entry.split(':')[1].replace('kB', '').strip())/10**6
    else:
        ret = None
    return ret


class ReadingError(Exception):
    pass


class ReachError(ReadingError):
    pass


class SparserError(ReadingError):
    pass


class formats:
    JSON = 'json'
    TEXT = 'text'
    XML = 'xml'


class Content(object):
    """An object to regularize the content passed to the readers.

    To use this class, use one of the two constructor methods:
     - `from_file` : use content from a file on the filesystem.
     - `from_string` : Pass a string (or bytes) directly as content.

    This class also regularizes the handling of id's and formats, as well as
    allowing for decompression and decoding, in the manner standard in the INDRA
    project.
    """
    def __init__(self, id, format, compressed=False, encoded=False):
        self.file_exists = False
        self.compressed = compressed
        self.encoded = encoded
        self._id = id
        self._format = format
        self._text = None
        self._fname = None
        self._location = None
        self._raw_content = None
        return

    @classmethod
    def from_file(cls, file_path, compressed=False, encoded=False):
        """Create a content object from a file path."""
        file_id = '.'.join(path.basename(file_path).split('.')[:-1])
        file_format = file_path.split('.')[-1]
        content = cls(file_id, file_format, compressed, encoded)
        content.file_exists = True
        content._location = path.dirname(file_path)
        return content

    @classmethod
    def from_string(cls, id, format, raw_content, compressed=False,
                    encoded=False):
        """Create a Content object from string/bytes content."""
        content = cls(id, format, compressed, encoded)
        content._raw_content = raw_content
        return content

    def _load_raw_content(self):
        if self.file_exists and self._raw_content is None:
            with open(self.get_filepath(), 'r') as f:
                self._raw_content = f.read()
        return

    def change_id(self, new_id):
        """Change the id of this content."""
        self._load_raw_content()
        self._id = new_id
        self.get_filename(renew=True)
        self.get_filepath(renew=True)
        return

    def change_format(self, new_format):
        """Change the format label of this content.

        Note that this does NOT actually alter the format of the content, only
        the label.
        """
        self._load_raw_content()
        self._format = new_format
        self.get_filename(renew=True)
        self.get_filepath(renew=True)
        return

    def set_location(self, new_location):
        """Set/change the location of this content.

        Note that this does NOT change the actual location of the file. To do
        so, use the `copy_to` method.
        """
        self._load_raw_content()
        self._location = new_location
        self.get_filepath(renew=True)
        return

    def is_format(self, *formats):
        """Check the format of this content."""
        return any([self._format == fmt for fmt in formats])

    def get_id(self):
        return self._id

    def get_format(self):
        return self._format

    def get_text(self):
        """Get the loaded, decompressed, and decoded text of this content."""
        self._load_raw_content()
        if self._text is None:
            assert self._raw_content is not None
            ret_cont = self._raw_content
            if self.compressed:
                ret_cont = zlib.decompress(ret_cont, zlib.MAX_WBITS+16)
            if self.encoded:
                ret_cont = ret_cont.decode('utf-8')
            self._text = ret_cont
        assert self._text is not None
        return self._text

    def get_filename(self, renew=False):
        """Get the filename of this content.

        If the file name doesn't already exist, we created it as {id}.{format}.
        """
        if self._fname is None or renew:
            self._fname = '%s.%s' % (self._id, self._format)
        return self._fname

    def get_filepath(self, renew=False):
        """Get the file path, joining the name and location for this file.

        If no location is given, it is assumed to be "here", e.g. ".".
        """
        if self._location is None or renew:
            self._location = '.'
        return path.join(self._location, self.get_filename())

    def copy_to(self, location, fname=None):
        if fname is None:
            fname = self.get_filename()
        fpath = path.join(location, fname)
        if self.file_exists and not self._raw_content:
            shutil.copy(self.get_filepath(), fpath)
        else:
            with open(fpath, 'w') as f:
                f.write(self.get_text())
        self._fname = fname
        self._location = location
        self.file_exists = True
        return fpath


class Reader(object):
    """This abstract object defines and some general methods for readers."""
    name = NotImplemented

    def __init__(self, base_dir=None, n_proc=1, check_content=True,
                 input_character_limit=CONTENT_CHARACTER_LIMIT,
                 max_space_ratio=CONTENT_MAX_SPACE_RATIO):
        if base_dir is None:
            base_dir = 'run_' + self.name.lower()
        self.n_proc = n_proc
        self.base_dir = _get_dir(base_dir)
        tmp_dir = tempfile.mkdtemp(
            prefix='%s_job_%s' % (self.name.lower(), _time_stamp()),
            dir=self.base_dir
            )
        self.tmp_dir = tmp_dir
        self.input_dir = _get_dir(tmp_dir, 'input')
        self.id_maps = {}
        self.do_content_check = check_content
        self.input_character_limit = input_character_limit
        self.max_space_ratio = max_space_ratio
        return

    def _check_content(self, content_str):
        """Check if the content is likely to be successfully read."""
        if self.do_content_check:
            space_ratio = float(content_str.count(' '))/len(content_str)
            if space_ratio > self.max_space_ratio:
                return "space-ratio: %f > %f" % (space_ratio,
                                                 self.max_space_ratio)
            if len(content_str) > self.input_character_limit:
                return "too long: %d > %d" % (len(content_str),
                                              self.input_character_limit)
        return None

    @classmethod
    def get_version(cls):
        raise NotImplementedError()

    def read(self, read_list, verbose=False, log=False):
        "Read a list of items and return a dict of output files."
        raise NotImplementedError()


class ReachReader(Reader):
    """This object encodes an interface to the reach reading script."""
    REACH_MEM = 5  # GB
    MEM_BUFFER = 2  # GB
    name = 'REACH'

    def __init__(self, *args, **kwargs):
        self.exec_path, self.version = self._check_reach_env()
        super(ReachReader, self).__init__(*args, **kwargs)
        conf_fmt_fname = path.join(path.dirname(__file__),
                                   'util/reach_conf_fmt.txt')
        self.conf_file_path = path.join(self.tmp_dir, 'indra.conf')
        with open(conf_fmt_fname, 'r') as fmt_file:
            fmt = fmt_file.read()
            log_level = 'INFO'
            # log_level = 'DEBUG' if logger.level == logging.DEBUG else 'INFO'
            with open(self.conf_file_path, 'w') as f:
                f.write(
                    fmt.format(tmp_dir=self.tmp_dir, num_cores=self.n_proc,
                               loglevel=log_level)
                    )
        self.output_dir = _get_dir(self.tmp_dir, 'output')
        return

    @classmethod
    def _join_json_files(cls, prefix, clear=False):
        """Join different REACH output JSON files into a single JSON object.

        The output of REACH is broken into three files that need to be joined
        before processing. Specifically, there will be three files of the form:
        `<prefix>.uaz.<subcategory>.json`.

        Parameters
        ----------
        prefix : str
            The absolute path up to the extensions that reach will add.
        clear : bool
            Default False - if True, delete the files as soon as they are
            loaded.

        Returns
        -------
        json_obj : dict
            The result of joining the files, keyed by the three subcategories.
        """
        filetype_list = ['entities', 'events', 'sentences']
        json_dict = {}
        try:
            for filetype in filetype_list:
                fname = prefix + '.uaz.' + filetype + '.json'
                with open(fname, 'rt') as f:
                    json_dict[filetype] = json.load(f)
                if clear:
                    remove(fname)
                    logger.debug("Removed %s." % fname)
        except IOError as e:
            logger.error(
                'Failed to open JSON files for %s; REACH error?' % prefix
                )
            logger.exception(e)
            return None
        return json_dict

    @staticmethod
    def _check_reach_env():
        """Check that the environment supports runnig reach."""
        # Get the path to the REACH JAR
        path_to_reach = get_config('REACHPATH')
        if path_to_reach is None:
            path_to_reach = environ.get('REACHPATH', None)
        if path_to_reach is None or not path.exists(path_to_reach):
            raise ReachError(
                'Reach path unset or invalid. Check REACHPATH environment var '
                'and/or config file.'
                )

        logger.debug('Using REACH jar at: %s' % path_to_reach)

        # Get the reach version.
        reach_version = get_config('REACH_VERSION')
        if reach_version is None:
            reach_version = environ.get('REACH_VERSION', None)
        if reach_version is None:
            logger.debug('REACH version not set in REACH_VERSION')
            m = re.match('reach-(.*?)\.jar', path.basename(path_to_reach))
            reach_version = re.sub('-SNAP.*?$', '', m.groups()[0])

        logger.debug('Using REACH version: %s' % reach_version)
        return path_to_reach, reach_version

    @classmethod
    def get_version(cls):
        _, version = cls._check_reach_env()
        return version

    def prep_input(self, read_list):
        """Apply the readers to the content."""
        logger.info("Prepping input.")
        i = 0
        for content in read_list:
            # Check the quality of the text, and skip if there are any issues.
            quality_issue = self._check_content(content.get_text())
            if quality_issue is not None:
                logger.warning("Skipping %d due to: %s"
                               % (content.get_id(), quality_issue))
                continue

            # Look for things that are more like file names, rather than ids.
            cid = content.get_id()
            if isinstance(cid, str) and re.match('^\w*?\d+$', cid) is None:
                new_id = 'FILE%06d' % i
                i += 1
                self.id_maps[new_id] = cid
                content.change_id(new_id)
                new_fpath = content.copy_to(self.input_dir)
            else:
                # Put the content in the appropriate directory.
                new_fpath = content.copy_to(self.input_dir)
            logger.debug('%s saved for reading by reach.'
                         % new_fpath)
        return

    def get_output(self):
        """Get the output of a reading job as a list of filenames."""
        logger.info("Getting outputs.")
        # Get the set of prefixes (each will correspond to three json files.)
        json_files = glob.glob(path.join(self.output_dir, '*.json'))
        json_prefixes = set()
        for json_file in json_files:
            # Remove .uaz.<subfile type>.json
            prefix = '.'.join(path.basename(json_file).split('.')[:-3])
            json_prefixes.add(path.join(self.output_dir, prefix))

        # Join each set of json files and store the json dict.
        reading_data_list = []
        for prefix in json_prefixes:
            base_prefix = path.basename(prefix)
            if base_prefix.isdecimal():
                base_prefix = int(base_prefix)
            elif base_prefix in self.id_maps.keys():
                base_prefix = self.id_maps[base_prefix]
            try:
                content = self._join_json_files(prefix, clear=True)
            except Exception as e:
                logger.exception(e)
                logger.error("Could not load result for prefix %s." % prefix)
                continue
            reading_data_list.append(ReadingData(
                base_prefix,
                self.name,
                self.version,
                formats.JSON,
                content
                ))
            logger.debug('Joined files for prefix %s.' % base_prefix)
        return reading_data_list

    def clear_input(self):
        """Remove all the input files (at the end of a reading)."""
        for item in listdir(self.input_dir):
            item_path = path.join(self.input_dir, item)
            if path.isfile(item_path):
                remove(item_path)
                logger.debug('Removed input %s.' % item_path)
        return

    def read(self, read_list, verbose=False, log=False):
        """Read the content, returning a list of ReadingData objects."""
        ret = []
        mem_tot = _get_mem_total()
        if mem_tot is not None and mem_tot <= self.REACH_MEM + self.MEM_BUFFER:
            logger.error(
                "Too little memory to run reach. At least %s required." %
                (self.REACH_MEM + self.MEM_BUFFER)
                )
            logger.info("REACH not run.")
        elif len(read_list) > 0:
            # Prep the content
            self.prep_input(read_list)
            # Run REACH!
            logger.info("Beginning reach.")
            args = [
                'java',
                '-Dconfig.file=%s' % self.conf_file_path,
                '-jar', self.exec_path
                ]
            p = subprocess.Popen(args, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            log_file_str = ''
            for line in iter(p.stdout.readline, b''):
                log_line = 'REACH: ' + line.strip().decode('utf8')
                if verbose:
                    logger.info(log_line)
                if log:
                    log_file_str += log_line + '\n'
            if log:
                with open('reach_run.log', 'ab') as f:
                    f.write(log_file_str.encode('utf8'))
            p_out, p_err = p.communicate()
            if p.returncode:
                logger.error('Problem running REACH:')
                logger.error('Stdout: %s' % p_out.decode('utf-8'))
                logger.error('Stderr: %s' % p_err.decode('utf-8'))
                raise ReachError("Problem running REACH")
            logger.info("Reach finished.")
            ret = self.get_output()
            self.clear_input()
        return ret


class SparserReader(Reader):
    """This object provides methods to interface with the commandline tool."""

    name = 'SPARSER'

    def __init__(self, *args, **kwargs):
        self.version = self.get_version()
        super(SparserReader, self).__init__(*args, **kwargs)
        self.file_list = None
        return

    @classmethod
    def get_version(cls):
        return sparser.get_version()

    def prep_input(self, read_list):
        "Prepare the list of files or text content objects to be read."
        logger.info('Prepping input for sparser.')

        self.file_list = []

        for content in read_list:
            quality_issue = self._check_content(content.get_text())
            if quality_issue is not None:
                logger.warning("Skipping %d due to: %s"
                               % (content.get_id(), quality_issue))
                continue

            if content.is_format('nxml'):
                # If it is already an nxml, we just need to adjust the
                # name a bit, if anything.
                if not content.get_filename().startswith('PMC'):
                    content.change_id('PMC' + str(content.get_id()))
                fpath = content.copy_to(self.tmp_dir)
                self.file_list.append(fpath)
            elif content.is_format('txt', 'text'):
                # Otherwise we need to frame the content in xml and put it
                # in a new file with the appropriate name.
                nxml_str = sparser.make_nxml_from_text(content.get_text())
                new_content = Content.from_string('PMC' + str(content.get_id()),
                                                  'nxml', nxml_str)
                fpath = new_content.copy_to(self.tmp_dir)
                self.file_list.append(fpath)
            else:
                raise SparserError("Unrecognized format %s."
                                   % content.format)
        return

    def get_output(self, output_files, clear=True):
        "Get the output files as an id indexed dict."
        reading_data_list = []
        patt = re.compile(r'(.*?)-semantics.*?')
        for outpath in output_files:
            if outpath is None:
                logger.warning("Found outpath with value None. Skipping.")
                continue

            re_out = patt.match(path.basename(outpath))
            if re_out is None:
                raise SparserError("Could not get prefix from output path %s."
                                   % outpath)
            prefix = re_out.groups()[0]
            if prefix.startswith('PMC'):
                prefix = prefix[3:]
            if prefix.isdecimal():
                # In this case we assume the prefix is a tcid.
                prefix = int(prefix)

            try:
                with open(outpath, 'rt') as f:
                    content = json.load(f)
            except Exception as e:
                logger.exception(e)
                logger.error("Could not load reading content from %s."
                             % outpath)
                continue

            reading_data_list.append(ReadingData(
                prefix,
                self.name,
                self.version,
                formats.JSON,
                content
                ))
            if clear:
                input_path = outpath.replace('-semantics.json', '.nxml')
                try:
                    remove(outpath)
                    remove(input_path)
                except Exception as e:
                    logger.exception(e)
                    logger.error("Could not remove sparser files %s and %s."
                                 % (outpath, input_path))
        return reading_data_list

    def read_one(self, fpath, outbuf=None, verbose=False):
        fpath = path.abspath(fpath)
        if outbuf is None:
            outbuf = BytesIO()
        outbuf.write(b'\nReading %s.\n' % fpath.encode('utf8'))
        outbuf.flush()
        if verbose:
            logger.info('Reading %s.' % fpath)
        outpath = None
        try:
            outpath = sparser.run_sparser(fpath, 'json', outbuf, timeout=60)
        except Exception as e:
            if verbose:
                logger.error('Failed to run sparser on %s.' %
                             fpath)
                logger.exception(e)
            outbuf.write(b'Reading failed.----------\n')
            outbuf.write(str(e).encode('utf-8') + b'\n')
            outbuf.write(b'-------------------------\n')
        return outpath, outbuf

    def read_some(self, fpath_list, outbuf=None, verbose=False):
        "Perform a few readings."
        outpath_list = []
        for fpath in fpath_list:
            output, outbuf = self.read_one(fpath, outbuf, verbose)
            if output is not None:
                outpath_list.append(output)
        return outpath_list, outbuf

    def read(self, read_list, verbose=False, log=False, n_per_proc=None):
        "Perform the actual reading."
        ret = []
        self.prep_input(read_list)
        L = len(self.file_list)
        if L > 0:
            logger.info("Beginning to run sparser.")
            output_file_list = []
            if log:
                log_name = 'sparser_run_%s.log' % _time_stamp()
                outbuf = open(log_name, 'wb')
            else:
                outbuf = None
            try:
                if self.n_proc == 1:
                    for fpath in self.file_list:
                        outpath, _ = self.read_one(fpath, outbuf, verbose)
                        if outpath is not None:
                            output_file_list.append(outpath)
                else:
                    if n_per_proc is None:
                        n_per_proc = max(1, min(1000, L//self.n_proc//2))
                    pool = None
                    try:
                        pool = Pool(self.n_proc)
                        if n_per_proc is not 1:
                            batches = [self.file_list[n*n_per_proc:(n+1)*n_per_proc]
                                       for n in range(L//n_per_proc + 1)]
                            out_lists_and_buffs = pool.map(self.read_some,
                                                           batches)
                        else:
                            out_files_and_buffs = pool.map(self.read_one,
                                                           self.file_list)
                            out_lists_and_buffs = [([out_files], buffs)
                                                   for out_files, buffs
                                                   in out_files_and_buffs]
                    finally:
                        if pool is not None:
                            pool.close()
                            pool.join()
                    for i, (out_list, buff) in enumerate(out_lists_and_buffs):
                        if out_list is not None:
                            output_file_list += out_list
                        if log:
                            outbuf.write(b'Log for producing output %d/%d.\n'
                                         % (i, len(out_lists_and_buffs)))
                            if buff is not None:
                                buff.seek(0)
                                outbuf.write(buff.read() + b'\n')
                            else:
                                outbuf.write(b'ERROR: no buffer was None. '
                                             b'No logs available.\n')
                            outbuf.flush()
            finally:
                if log:
                    outbuf.close()
                    if verbose:
                        logger.info("Sparser logs may be found at %s." %
                                    log_name)
            ret = self.get_output(output_file_list)
        return ret


def get_readers():
    """Get all children of the Reader objcet."""
    try:
        children = Reader.__subclasses__()
    except AttributeError:
        module = sys.modules[__name__]
        children = [cls for cls_name, cls in module.__dict__.items()
                    if isinstance(cls, type) and issubclass(cls, Reader)
                    and cls_name != 'Reader']
    return children


def get_reader_class(reader_name):
    """Get a particular reader class by name."""
    for reader_class in get_readers():
        if reader_class.name.lower() == reader_name.lower():
            return reader_class
    else:
        logger.error("No such reader: %s" % reader_name)
        return None


def get_reader(reader_name, *args, **kwargs):
    """Get an instantiated reader by name."""
    return get_reader_class(reader_name)(*args, **kwargs)


class ReadingData(object):
    """Object to contain the data produced by a reading.

    This is primarily designed for use with the database.

    Init Parameters
    ---------------
    tcid : int or str
        An identifier of the text content that produced the reading. Must
        be an int for use with the database.
    reader : str
        The name of the reader, consistent with it's `name` attribute, for
        example: 'REACH'
    reader_version : str
        A string identifying the version of the underlying nlp reader.
    content_format : str
        The format of the content. Options are in indra.db.formats.
    content : str
        The content of the reading result. A string in the format given by
        `content_format`.
    reading_id : int or None
        Optional. The id corresponding to the Readings entry in the db.
    """

    def __init__(self, tcid, reader, reader_version, content_format, content,
                 reading_id=None):
        self.reading_id = reading_id
        self.tcid = tcid
        self.reader = reader
        self.reader_version = reader_version
        self.format = content_format
        self.content = content
        self._statements = None
        return

    @classmethod
    def from_db_reading(cls, db_reading):
        return cls(db_reading.text_content_id, db_reading.reader,
                   db_reading.reader_version, db_reading.format,
                   json.loads(zlib.decompress(db_reading.bytes,
                                              16+zlib.MAX_WBITS)
                              .decode('utf8')),
                   db_reading.id)

    @staticmethod
    def get_cols():
        """Get the columns for the tuple returned by `make_tuple`."""
        return ('text_content_id', 'reader', 'reader_version', 'format',
                'bytes')

    def get_statements(self, reprocess=False):
        """General method to create statements."""
        if self._statements is None or reprocess:
            logger.debug("Making statements from %s." % self.reading_id)
            if self.reader == ReachReader.name:
                if self.format == formats.JSON:
                    # Process the reach json into statements.
                    json_str = json.dumps(self.content)
                    processor = reach.process_json_str(json_str)
                else:
                    raise ReadingError("Incorrect format for Reach output: %s."
                                       % self.format)
            elif self.reader == SparserReader.name:
                if self.format == formats.JSON:
                    # Process the sparser content into statements
                    processor = sparser.process_json_dict(self.content)
                    if processor is not None:
                        processor.set_statements_pmid(None)
                else:
                    raise ReadingError("Sparser should only ever be JSON, not "
                                       "%s." % self.format)
            else:
                raise ReadingError("Unknown reader: %s." % self.reader)
            if processor is None:
                logger.error("Production of statements from %s failed for %s."
                             % (self.reader, self.tcid))
                stmts = []
            else:
                stmts = processor.statements
            self._statements = stmts
        else:
            logger.debug("Returning %d statements that were already produced "
                         "from %s." % (len(self._statements), self.reading_id))
            stmts = self._statements
        return stmts

    def zip_content(self):
        """Compress the content, returning bytes."""
        if self.format == formats.JSON:
            ret = zip_string(json.dumps(self.content))
        elif self.format == formats.TEXT:
            ret = zip_string(self.content)
        else:
            raise Exception('Do not know how to zip format %s.' % self.format)
        return ret

    def make_tuple(self):
        """Make the tuple expected by the database."""
        return (self.tcid, self.reader, self.reader_version, self.format,
                self.zip_content())

    def matches(self, r_entry):
        """Determine if reading data matches the a reading entry from the db.

        Returns True if tcid, reader, reader_version match the corresponding
        elements of a db.Reading instance, else False.
        """
        # Note the temporary fix in clipping the reader version length. This is
        # because the version is for some reason clipped in the database.
        return (r_entry.text_content_id == self.tcid
                and r_entry.reader == self.reader
                and r_entry.reader_version == self.reader_version[:20])
