# -*- coding: utf-8 -*-
""" common MDF file format module """

import csv
import os
import sys
from collections import OrderedDict
from datetime import datetime
from warnings import warn
from functools import reduce
from struct import unpack

import numpy as np
from pandas import DataFrame

from .mdf_v2 import MDF2
from .mdf_v3 import MDF3
from .mdf_v4 import MDF4
from .signal import Signal
from .utils import (
    CHANNEL_COUNT,
    MERGE_LOW,
    MERGE_MINIMUM,
    MdfException,
    get_text_v3,
    get_text_v4,
    get_unique_name,
    matlab_compatible,
    validate_memory_argument,
    validate_version_argument,
    MDF2_VERSIONS,
    MDF3_VERSIONS,
    MDF4_VERSIONS,
    SUPPORTED_VERSIONS,
)
from .v2_v3_blocks import Channel as ChannelV3
from .v2_v3_blocks import HeaderBlock as HeaderV3
from .v4_blocks import Channel as ChannelV4
from .v4_blocks import HeaderBlock as HeaderV4
from .v4_blocks import ChannelArrayBlock, TextBlock, SourceInformation, FileIdentificationBlock
from . import v4_constants as v4c

PYVERSION = sys.version_info[0]


__all__ = ['MDF', 'SUPPORTED_VERSIONS']


class MDF(object):
    """Unified access to MDF v3 and v4 files. Underlying _mdf's attributes and
    methods are linked to the `MDF` object via *setattr*. This is done to expose
    them to the user code and for performance considerations.

    Parameters
    ----------
    name : string
        mdf file name, if provided it must be a real file name
    memory : str
        memory option; default `full`:

        * if *full* the data group binary data block will be loaded in RAM
        * if *low* the channel data is read from disk on request, and the
          metadata is loaded into RAM
        * if *minimum* only minimal data is loaded into RAM


    version : string
        mdf file version from ('2.00', '2.10', '2.14', '3.00', '3.10', '3.20',
        '3.30', '4.00', '4.10', '4.11'); default '4.10'

    """

    def __init__(self, name=None, memory='full', version='4.10'):
        if name:
            if os.path.isfile(name):
                memory = validate_memory_argument(memory)
                with open(name, 'rb') as file_stream:
                    magic_header = file_stream.read(3)
                    if magic_header != b'MDF':
                        raise MdfException('"{}" is not a valid ASAM MDF file'.format(name))
                    file_stream.seek(8)
                    version = file_stream.read(4).decode('ascii').strip(' \0')
                    if not version:
                        file_stream.read(16)
                        version = unpack('<H', file_stream.read(2))[0]
                        version = str(version)
                        version = '{}.{}'.format(version[0], version[1:])
                if version in MDF3_VERSIONS:
                    self._mdf = MDF3(name, memory)
                elif version in MDF4_VERSIONS:
                    self._mdf = MDF4(name, memory)
                elif version in MDF2_VERSIONS:
                    self._mdf = MDF2(name, memory)
                else:
                    message = ('"{}" is not a supported MDF file; '
                               '"{}" file version was found')
                    raise MdfException(message.format(name, version))
            else:
                raise MdfException('File "{}" does not exist'.format(name))
        else:
            version = validate_version_argument(version)
            memory = validate_memory_argument(memory)
            if version in MDF2_VERSIONS:
                self._mdf = MDF3(
                    version=version,
                    memory=memory,
                )
            elif version in MDF3_VERSIONS:
                self._mdf = MDF3(
                    version=version,
                    memory=memory,
                )
            elif version in MDF4_VERSIONS:
                self._mdf = MDF4(
                    version=version,
                    memory=memory,
                )
            else:
                message = ('"{}" is not a supported MDF file version; '
                           'Supported versions are {}')
                raise MdfException(message.format(version, SUPPORTED_VERSIONS))

        # link underlying _mdf attributes and methods to the new MDF object
        for attr in set(dir(self._mdf)) - set(dir(self)):
            setattr(self, attr, getattr(self._mdf, attr))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def _excluded_channels(self, index):
        """ get the indexes list of channels that are excluded when processing
        teh channel group. The candiates for exlusion are the master channel
        (since it is retrieved as `Signal` timestamps), structure channel
        composition component channels (since they are retrieved as fields in
        the `Signal` samples recarray) and channel dependecies (mdf version 3) /
        channel array axes

        Parameters
        ----------
        index : int
            channel group index

        Returns
        -------
        excluded_channels : set
            set of excluded channels

        """

        group = self.groups[index]

        excluded_channels = set()
        master_index = self.masters_db.get(index, -1)
        excluded_channels.add(master_index)

        channels = group['channels']

        if self.version in MDF2_VERSIONS + MDF3_VERSIONS:
            for dep in group['channel_dependencies']:
                if dep is None:
                    continue
                for ch_nr, gp_nr in dep.referenced_channels:
                    if gp_nr == index:
                        excluded_channels.add(ch_nr)
        else:
            for dependencies in group['channel_dependencies']:
                if dependencies is None:
                    continue
                if all(not isinstance(dep, ChannelArrayBlock)
                       for dep in dependencies):
                    for channel in dependencies:
                        excluded_channels.add(channels.index(channel))
                else:
                    for dep in dependencies:
                        for ch_nr, gp_nr in dep.referenced_channels:
                            if gp_nr == index:
                                excluded_channels.add(ch_nr)

        return excluded_channels



    def __contains__(self, channel):
        """ if *'channel name'* in *'mdf file'* """
        return channel in self.channels_db

    def __iter__(self):
        """ terate over all the channels found in the file; master channels are
        skipped from iteration

        """

        for signal in self.iter_channels():
            yield signal

    def convert(self, to, memory='full'):
        """convert *MDF* to other version

        Parameters
        ----------
        to : str
            new mdf file version from ('2.00', '2.10', '2.14', '3.00', '3.10',
            '3.20', '3.30', '4.00', '4.10', '4.11'); default '4.10'
        memory : str
            memory option; default *full*

        Returns
        -------
        out : MDF
            new *MDF* object

        """
        version = validate_version_argument(to)
        memory = validate_memory_argument(memory)

        out = MDF(version=version, memory=memory)

        out.header.start_time = self.header.start_time

        # walk through all groups and get all channels
        for i, group in enumerate(self.groups):
            excluded_channels = self._excluded_channels(i)
            channels_nr = len(group['channels'])

            parents, dtypes = self._prepare_record(group)
            group['parents'], group['types'] = parents, dtypes

            data = self._load_group_data(group)
            for idx, fragment in enumerate(data):

                if dtypes.itemsize:
                    group['record'] = np.core.records.fromstring(
                        fragment[0],
                        dtype=dtypes,
                    )
                else:
                    group['record'] = None

                # the first fragment triggers and append that will add the
                # metadata for all channels
                if idx == 0:
                    sigs = []
                    for j in range(channels_nr):
                        if j in excluded_channels:
                            continue
                        else:
                            sig = self.get(
                                group=i,
                                index=j,
                                data=fragment,
                                raw=True,
                            )
                            if version < '4.00' and sig.samples.dtype.kind == 'S':
                                strsig = self.get(
                                    group=i,
                                    index=j,
                                    samples_only=True,
                                )
                                sig.samples = sig.samples.astype(strsig.dtype)
                                del strsig
                            if not sig.samples.flags.writeable:
                                sig.samples = sig.samples.copy()
                            sigs.append(sig)
                    source_info = 'Converted from {} to {}'

                    if sigs:
                        out.append(
                            sigs,
                            source_info.format(self.version, to),
                            common_timebase=True,
                        )
                        if self.version >= '4.00' and version >= '4.00' and (group['channel_group']['flags'] & v4c.FLAG_CG_BUS_EVENT):
                            original_texts = group['texts']['channel_group'][0]
                            cg_texts = {}
                            if memory == 'minimum':
                                stream = out._tempfile
                                tx_block = TextBlock(
                                    text=original_texts['acq_name_addr']['text'],
                                )
                                stream.seek(0, 2)
                                address = stream.tell()
                                stream.write(bytes(tx_block))
                                cg_texts['acq_name_addr'] = address

                                tx_block = TextBlock(
                                    text=original_texts['comment_addr']['text'],
                                    meta=True,
                                )
                                address = stream.tell()
                                stream.write(bytes(tx_block))
                                cg_texts['comment_addr'] = address
                            else:
                                cg_texts['acq_name_addr'] = TextBlock(
                                    text=original_texts['acq_name_addr']['text'],
                                )
                                cg_texts['comment_addr'] = TextBlock(
                                    text=original_texts['comment_addr']['text'],
                                    meta=True,
                                )

                            new_group = out.groups[-1]
                            new_group['texts']['channel_group'][0] = cg_texts

                            new_group['channel_group']['flags'] = group['channel_group']['flags']
                            new_group['channel_group']['path_separator'] = ord('.')

                            source = group['channel_group_source']
                            if source:
                                new_source = SourceInformation()
                                new_source.update(source)
                                new_source.name = source.name
                                new_source.path = source.path
                                new_source.comment = source.comment
                            else:
                                new_source = None

                            new_group['channel_group_source'] = new_source

                    else:
                        break

                # the other fragments will trigger onl the extension of
                # samples records to the data block
                else:
                    sigs = [self.get_master(i, data=fragment), ]

                    for j in range(channels_nr):
                        if j in excluded_channels:
                            continue
                        else:
                            sig = self.get(
                                group=i,
                                index=j,
                                data=fragment,
                                raw=True,
                                samples_only=True,
                            )
                            if not sig.flags.writeable:
                                sig = sig.copy()
                            sigs.append(sig)
                    out.extend(i, sigs)

                del group['record']

        return out

    def cut(self, start=None, stop=None, whence=0):
        """cut *MDF* file. *start* and *stop* limits are absolute values
        or values relative to the first timestamp depending on the *whence*
        argument.

        Parameters
        ----------
        start : float
            start time, default *None*. If *None* then the start of measurement
            is used
        stop : float
            stop time, default *None*. If *None* then the end of measurement is used
        whence : int
            how to search for the start and stop values

            * 0 : absolute
            * 1 : relative to first timestamp

        Returns
        -------
        out : MDF
            new MDF object

        """
        out = MDF(
            version=self.version,
            memory=self.memory,
        )

        out.header.start_time = self.header.start_time

        if whence == 1:
            timestamps = []
            for i, group in enumerate(self.groups):
                fragment = next(self._load_group_data(group))
                master = self.get_master(i, fragment)
                if master.size:
                    timestamps.append(master[0])
                del master

            if timestamps:
                first_timestamp = np.amin(timestamps)
            else:
                first_timestamp = 0
            if start is not None:
                start += first_timestamp
            if stop is not None:
                stop += first_timestamp

        out.header.start_time = self.header.start_time

        # walk through all groups and get all channels
        for i, group in enumerate(self.groups):
            sigs = []
            excluded_channels = self._excluded_channels(i)

            channels_nr = len(group['channels'])

            data = self._load_group_data(group)
            parents, dtypes = self._prepare_record(group)
            group['parents'], group['types'] = parents, dtypes

            idx = 0
            for fragment in data:
                if dtypes.itemsize:
                    group['record'] = np.core.records.fromstring(
                        fragment[0],
                        dtype=dtypes,
                    )
                else:
                    group['record'] = None
                master = self.get_master(i, fragment)
                if not len(master):
                    continue

                # check if this fragement is within the cut interval or
                # if the cut interval has ended
                if start is None and stop is None:
                    fragment_start = None
                    fragment_stop = None
                    start_index = 0
                    stop_index = len(master)
                else:
                    if start is None:
                        fragment_start = None
                        start_index = 0
                        if master[0] > stop:
                            break
                        else:
                            fragment_stop = min(stop, master[-1])
                            stop_index = np.searchsorted(master, fragment_stop, side='right')
                    elif stop is None:
                        fragment_stop = None
                        if master[-1] < start:
                            continue
                        else:
                            fragment_start = max(start, master[0])
                            start_index = np.searchsorted(master, fragment_start, side='left')
                            stop_index = len(master)
                    else:
                        if master[0] > stop:
                            break
                        elif master[-1] < start:
                            continue
                        else:
                            fragment_start = max(start, master[0])
                            start_index = np.searchsorted(master, fragment_start, side='left')
                            fragment_stop = min(stop, master[-1])
                            stop_index = np.searchsorted(master, fragment_stop, side='right')

                    # the first fragment triggers and append that will add the
                    # metadata for all channels
                    if idx == 0:
                        sigs = []
                        for j in range(channels_nr):
                            if j in excluded_channels:
                                continue
                            sig = self.get(
                                group=i,
                                index=j,
                                data=fragment,
                                raw=True,
                            ).cut(fragment_start, fragment_stop)
                            if not sig.samples.flags.writeable:
                                sig.samples = sig.samples.copy()
                            sigs.append(sig)

                        if sigs:
                            if start:
                                start_ = '{}s'.format(start)
                            else:
                                start_ = 'start of measurement'
                            if stop:
                                stop_ = '{}s'.format(stop)
                            else:
                                stop_ = 'end of measurement'
                            out.append(
                                sigs,
                                'Cut from {} to {}'.format(start_, stop_),
                                common_timebase=True,
                            )

                        idx += 1

                    # the other fragments will trigger onl the extension of
                    # samples records to the data block
                    else:
                        sigs = [master[start_index: stop_index].copy(), ]

                        for j in range(channels_nr):
                            if j in excluded_channels:
                                continue
                            sig = self.get(
                                group=i,
                                index=j,
                                data=fragment,
                                raw=True,
                                samples_only=True
                            )[start_index: stop_index]
                            if not sig.flags.writeable:
                                sig = sig.copy()
                            sigs.append(sig)

                        if sigs:
                            out.extend(i, sigs)

                        idx += 1

                del group['record']

            # if the cut interval is not found in the measurement
            # then append an empty data group
            if idx == 0:

                self.configure(read_fragment_size=1)
                sigs = []

                fragment = next(self._load_group_data(group))

                fragment = (fragment[0], -1)

                for j in range(channels_nr):
                    if j in excluded_channels:
                        continue
                    sig = self.get(
                        group=i,
                        index=j,
                        data=fragment,
                        raw=True,
                    )
                    sig.samples = sig.samples[:0]
                    sig.timestamps = sig.timestamps[:0]
                    sigs.append(sig)

                if start:
                    start_ = '{}s'.format(start)
                else:
                    start_ = 'start of measurement'
                if stop:
                    stop_ = '{}s'.format(stop)
                else:
                    stop_ = 'end of measurement'
                out.append(
                    sigs,
                    'Cut from {} to {}'.format(start_, stop_),
                    common_timebase=True,
                )

                self.configure(read_fragment_size=0)

        return out

    def export(self, fmt, filename=None, **kargs):
        """ export *MDF* to other formats. The *MDF* file name is used is
        available, else the *filename* aragument must be provided.

        Parameters
        ----------
        fmt : string
            can be one of the following:

            * `csv` : CSV export that uses the ";" delimiter. This option
              will generate a new csv file for each data group
              (<MDFNAME>_DataGroup_<cntr>.csv)

            * `hdf5` : HDF5 file output; each *MDF* data group is mapped to
              a *HDF5* group with the name 'DataGroup_<cntr>'
              (where <cntr> is the index)

            * `excel` : Excel file output (very slow). This option will
              generate a new excel file for each data group
              (<MDFNAME>_DataGroup_<cntr>.xlsx)

            * `mat` : Matlab .mat version 5 export, for Matlab >= 7.6. In
              the mat file the channels will be renamed to
              'DataGroup_<cntr>_<channel name>'. The channel group master
              will be renamed to 'DataGroup_<cntr>_<channel name>_master'
              ( *<cntr>* is the data group index starting from 0)
        filename : string
            export file name
        **kwargs

            * `single_time_base`: resample all channels to common time base, default *False*.
              Only valid for *mat* export.
            * `raster`: float time raster for resampling. Valid for *mat* export if *single_time_base* is *True*
              and for *pandas* export
            * `time_from_zero`: adjust time channel to start from 0. Valid for *mat* and *pandas* export.
            * `use_display_names`: use display name instead of standard channel name, if available.

        Returns
        -------
        dataframe : pandas.DataFrame
            only in case of *pandas* export

        """

        header_items = (
            'date',
            'time',
            'author',
            'organization',
            'project',
            'subject',
        )

        if filename is None and self.name is None:
            message = ('Must specify filename for export'
                       'if MDF was created without a file name')
            warn(message)
            return

        name = filename if filename else self.name
        if fmt == 'hdf5':
            try:
                from h5py import File as HDF5
            except ImportError:
                warn('h5py not found; export to HDF5 is unavailable')
                return
            else:
                if not name.endswith('.hdf'):
                    name = os.path.splitext(name)[0] + '.hdf'
                with HDF5(name, 'w') as hdf:
                    # header information
                    group = hdf.create_group(os.path.basename(name))

                    if self.version in MDF2_VERSIONS + MDF3_VERSIONS:
                        for item in header_items:
                            group.attrs[item] = self.header[item]

                    # save each data group in a HDF5 group called
                    # "DataGroup_<cntr>" with the index starting from 1
                    # each HDF5 group will have a string attribute "master"
                    # that will hold the name of the master channel
                    for i, grp in enumerate(self.groups):
                        group_name = r'/' + 'DataGroup_{}'.format(i + 1)
                        group = hdf.create_group(group_name)

                        master_index = self.masters_db.get(i, -1)

                        data = self._load_group_data(grp)

                        if PYVERSION == 2:
                            data = b''.join(str(d[0]) for d in data)
                        else:
                            data = b''.join(d[0] for d in data)
                        data = (data, 0)

                        for j, _ in enumerate(grp['channels']):
                            sig = self.get(group=i, index=j, data=data)
                            name = sig.name
                            if j == master_index:
                                group.attrs['master'] = name
                            dataset = group.create_dataset(name,
                                                           data=sig.samples)
                            if sig.unit:
                                dataset.attrs['unit'] = sig.unit
                            if sig.comment:
                                dataset.attrs['comment'] = sig.comment

        elif fmt == 'excel':
            try:
                import xlsxwriter
            except ImportError:
                warn('xlsxwriter not found; export to Excel unavailable')
                return
            else:
                excel_name = os.path.splitext(name)[0]
                count = len(self.groups)
                for i, grp in enumerate(self.groups):
                    print('Exporting group {} of {}'.format(i + 1, count))

                    data = self._load_group_data(grp)

                    if PYVERSION == 2:
                        data = b''.join(str(d[0]) for d in data)
                    else:
                        data = b''.join(d[0] for d in data)
                    data = (data, 0)

                    group_name = 'DataGroup_{}'.format(i + 1)
                    wb_name = '{}_{}.xlsx'.format(excel_name, group_name)
                    workbook = xlsxwriter.Workbook(wb_name)
                    bold = workbook.add_format({'bold': True})

                    sheet = workbook.add_worksheet(group_name)

                    # the sheet header has 3 rows
                    # the channel name and unit 'YY [xx]'
                    # the channel comment
                    # the flag for data grup master channel
                    sheet.write(0, 0, 'Channel', bold)
                    sheet.write(1, 0, 'comment', bold)
                    sheet.write(2, 0, 'is master', bold)

                    master_index = self.masters_db.get(i, -1)

                    for j in range(grp['channel_group']['cycles_nr']):
                        sheet.write(j + 3, 0, str(j))

                    for j, _ in enumerate(grp['channels']):
                        sig = self.get(group=i, index=j, data=data)

                        col = j + 1
                        sig_description = '{} [{}]'.format(
                            sig.name,
                            sig.unit,
                        )
                        comment = sig.comment if sig.comment else ''
                        sheet.write(0, col, sig_description)
                        sheet.write(1, col, comment)
                        if j == master_index:
                            sheet.write(2, col, 'x')
                        sheet.write_column(3, col, sig.samples.astype(str))

                    workbook.close()

        elif fmt == 'csv':
            csv_name = os.path.splitext(name)[0]
            count = len(self.groups)
            for i, grp in enumerate(self.groups):
                print('Exporting group {} of {}'.format(i + 1, count))
                data = self._load_group_data(grp)

                if PYVERSION == 2:
                    data = b''.join(str(d[0]) for d in data)
                else:
                    data = b''.join(d[0] for d in data)
                data = (data, 0)

                group_name = 'DataGroup_{}'.format(i + 1)
                group_csv_name = '{}_{}.csv'.format(csv_name, group_name)
                with open(group_csv_name, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)

                    ch_nr = len(grp['channels'])
                    channels = [
                        self.get(group=i, index=j, data=data)
                        for j in range(ch_nr)
                    ]

                    master_index = self.masters_db.get(i, -1)
                    cycles = grp['channel_group']['cycles_nr']

                    names_row = ['Channel', ]
                    names_row += [
                        '{} [{}]'.format(ch.name, ch.unit)
                        for ch in channels
                    ]
                    writer.writerow(names_row)

                    comment_row = ['comment', ]
                    comment_row += [ch.comment for ch in channels]
                    writer.writerow(comment_row)

                    master_row = ['Is master', ]
                    master_row += [
                        'x' if j == master_index else ''
                        for j in range(ch_nr)
                    ]
                    writer.writerow(master_row)

                    vals = [np.array(range(cycles), dtype=np.uint32), ]
                    vals += [ch.samples for ch in channels]

                    writer.writerows(zip(*vals))

        elif fmt == 'mat':
            try:
                from scipy.io import savemat
            except ImportError:
                warn('scipy not found; export to mat is unavailable')
                return

            if not name.endswith('.mat'):
                name = name + '.mat'

            mdict = {}

            single_time_base = kargs.get('single_time_base', False)
            raster = kargs.get('raster', 0)
            time_from_zero = kargs.get('time_from_zero', True)
            use_display_names = kargs.get('use_display_names', True)

            if single_time_base:
                masters = [
                    self.get_master(i)
                    for i in range(len(self.groups))
                ]
                master = reduce(np.union1d, masters)
                if raster:
                    master = np.arange(
                        master[0],
                        master[-1],
                        raster,
                        dtype=np.float64,
                    )
                if time_from_zero:
                    mdict['t'] = master - master[0]
                else:
                    mdict['t'] = master

                used_names = {'t'}

                for i, grp in enumerate(self.groups):
                    master_index = self.masters_db.get(i, -1)
                    data = self._load_group_data(grp)

                    if PYVERSION == 2:
                        data = b''.join(str(d[0]) for d in data)
                    else:
                        data = b''.join(d[0] for d in data)
                    data = (data, 0)

                    for j, _ in enumerate(grp['channels']):
                        if j == master_index:
                            continue
                        sig = self.get(
                            group=i,
                            index=j,
                            data=data,
                        ).interp(master)

                        if use_display_names:
                            channel_name = sig.display_name or sig.name
                        else:
                            channel_name = sig.name

                        channel_name = matlab_compatible(channel_name)

                        channel_name = get_unique_name(used_names, channel_name)
                        used_names.add(channel_name)

                        mdict[channel_name] = sig.samples

            else:
                master_name_template = 'DataGroup_{}_{}_master'
                channel_name_template = 'DataGroup_{}_{}'
                used_names = set()

                for i, grp in enumerate(self.groups):
                    master_index = self.masters_db.get(i, -1)
                    data = self._load_group_data(grp)

                    if PYVERSION == 2:
                        data = b''.join(str(d[0]) for d in data)
                    else:
                        data = b''.join(d[0] for d in data)
                    data = (data, 0)

                    for j, _ in enumerate(grp['channels']):
                        sig = self.get(
                            group=i,
                            index=j,
                            data=data,
                        )
                        if j == master_index:
                            channel_name = master_name_template.format(i, sig.name)
                        else:
                            if use_display_names:
                                channel_name = sig.display_name or sig.name
                            else:
                                channel_name = sig.name
                            channel_name = channel_name_template.format(i, channel_name)

                        channel_name = matlab_compatible(channel_name)
                        channel_name = get_unique_name(used_names, channel_name)
                        used_names.add(channel_name)

                        mdict[channel_name] = sig.samples

            savemat(
                name,
                mdict,
                long_field_names=True,
                do_compression=True,
            )

        elif fmt == 'pandas':

            if not name.endswith('.mat'):
                name = name + '.mat'

            mdict = {}

            raster = kargs.get('raster', 0)
            time_from_zero = kargs.get('time_from_zero', True)
            use_display_names = kargs.get('use_display_names', True)

            masters = [
                self.get_master(i)
                for i in range(len(self.groups))
            ]
            master = reduce(np.union1d, masters)
            if raster:
                master = np.arange(
                    master[0],
                    master[-1],
                    raster,
                    dtype=np.float64,
                )
            if time_from_zero:
                mdict['t'] = master - master[0]
            else:
                mdict['t'] = master

            used_names = {'t'}

            for i, grp in enumerate(self.groups):
                master_index = self.masters_db.get(i, -1)
                data = self._load_group_data(grp)

                if PYVERSION == 2:
                    data = b''.join(str(d[0]) for d in data)
                else:
                    data = b''.join(d[0] for d in data)
                data = (data, 0)

                for j, _ in enumerate(grp['channels']):
                    if j == master_index:
                        continue
                    sig = self.get(
                        group=i,
                        index=j,
                        data=data,
                    ).interp(master)

                    if use_display_names:
                        channel_name = sig.display_name or sig.name
                    else:
                        channel_name = sig.name

                    channel_name = matlab_compatible(channel_name)

                    channel_name = get_unique_name(used_names, channel_name)
                    used_names.add(channel_name)

                    mdict[channel_name] = sig.samples

            return DataFrame.from_dict(mdict)

        else:
            message = (
                'Unsopported export type "{}". '
                'Please select "csv", "excel", "hdf5" or "mat"'
            )
            warn(message.format(fmt))

    def filter(self, channels, memory='full'):
        """ return new *MDF* object that contains only the channels listed in
        *channels* argument

        Parameters
        ----------
        channels : list
            list of items to be filtered; each item can be :

                * a channel name string
                * (channel name, group index, channel index) list or tuple
                * (channel name, group index) list or tuple
                * (None, group index, channel index) lsit or tuple

        memory : str
            memory option for filtered *MDF*; default *full*

        Returns
        -------
        mdf : MDF
            new *MDF* file

        Examples
        --------
        >>> from asammdf import MDF, Signal
        >>> import numpy as np
        >>> t = np.arange(5)
        >>> s = np.ones(5)
        >>> mdf = MDF()
        >>> for i in range(4):
        ...     sigs = [Signal(s*(i*10+j), t, name='SIG') for j in range(1,4)]
        ...     mdf.append(sigs)
        ...
        >>> filtered = mdf.filter(['SIG', ('SIG', 3, 1), ['SIG', 2], (None, 1, 2)])
        >>> for gp_nr, ch_nr in filtered.channels_db['SIG']:
        ...     print(filtered.get(group=gp_nr, index=ch_nr))
        ...
        <Signal SIG:
                samples=[ 1.  1.  1.  1.  1.]
                timestamps=[0 1 2 3 4]
                unit=""
                info=None
                comment="">
        <Signal SIG:
                samples=[ 31.  31.  31.  31.  31.]
                timestamps=[0 1 2 3 4]
                unit=""
                info=None
                comment="">
        <Signal SIG:
                samples=[ 21.  21.  21.  21.  21.]
                timestamps=[0 1 2 3 4]
                unit=""
                info=None
                comment="">
        <Signal SIG:
                samples=[ 12.  12.  12.  12.  12.]
                timestamps=[0 1 2 3 4]
                unit=""
                info=None
                comment="">

        """

        memory = validate_memory_argument(memory)

        # group channels by group index
        gps = {}

        for item in channels:
            if isinstance(item, (list, tuple)):
                if len(item) not in (2, 3):
                    raise MdfException(
                        'The items used for filtering must be strings, '
                        'or they must match the first 3 argumens of the get '
                        'method'
                    )
                else:
                    group, index = self._validate_channel_selection(*item)
                    if group not in gps:
                        gps[group] = set()
                    gps[group].add(index)
            else:
                name = item
                group, index = self._validate_channel_selection(name)
                if group not in gps:
                    gps[group] = set()
                gps[group].add(index)

        # see if there are exluded channels in the filter list
        for group_index, indexes in gps.items():
            grp = self.groups[group_index]
            excluded_channels = set()
            for index in indexes:
                if self.version in MDF2_VERSIONS + MDF3_VERSIONS:
                    dep = grp['channel_dependencies'][index]
                    if dep:
                        for ch_nr, gp_nr in dep.referenced_channels:
                            if gp_nr == group:
                                excluded_channels.add(ch_nr)
                else:
                    dependencies = grp['channel_dependencies'][index]
                    if dependencies is None:
                        continue
                    if all(not isinstance(dep, ChannelArrayBlock)
                           for dep in dependencies):
                        channels = grp['channels']
                        for channel in dependencies:
                            excluded_channels.add(channels.index(channel))
                    else:
                        for dep in dependencies:
                            for ch_nr, gp_nr in dep.referenced_channels:
                                if gp_nr == group:
                                    excluded_channels.add(ch_nr)

            gps[group_index] = gps[group_index] - excluded_channels

        if memory not in ('full', 'low', 'minimum'):
            memory = self.memory

        mdf = MDF(
            version=self.version,
            memory=memory,
        )

        mdf.header.start_time = self.header.start_time

        if self.name:
            origin = os.path.basename(self.name)
        else:
            origin = 'New MDF'

        # append filtered channels to new MDF
        for new_index, (group_index, indexes) in enumerate(gps.items()):
            group = self.groups[group_index]

            data = self._load_group_data(group)
            parents, dtypes = self._prepare_record(group)
            group['parents'], group['types'] = parents, dtypes

            for idx, fragment in enumerate(data):

                if dtypes.itemsize:
                    group['record'] = np.core.records.fromstring(
                        fragment[0],
                        dtype=dtypes,
                    )
                else:
                    group['record'] = None

                # the first fragment triggers and append that will add the
                # metadata for all channels
                if idx == 0:
                    sigs = []
                    for j in indexes:
                        sig = self.get(
                            group=group_index,
                            index=j,
                            data=fragment,
                            raw=True,
                        )
                        if self.version < '4.00' and sig.samples.dtype.kind == 'S':
                            strsig = self.get(
                                group=group_index,
                                index=j,
                                samples_only=True,
                            )
                            sig.samples = sig.samples.astype(strsig.dtype)
                            del strsig
                        if not sig.samples.flags.writeable:
                            sig.samples = sig.samples.copy()
                        sigs.append(sig)

                    source_info = 'Signals filtered from <{}>'.format(origin)
                    mdf.append(
                        sigs,
                        source_info,
                        common_timebase=True,
                    )

                # the other fragments will trigger onl the extension of
                # samples records to the data block
                else:
                    sigs = [self.get_master(group_index, data=fragment), ]

                    for j in indexes:
                        sig = self.get(
                            group=group_index,
                            index=j,
                            data=fragment,
                            samples_only=True,
                            raw=True,
                        )
                        if not sig.flags.writeable:
                            sig = sig.copy()
                        sigs.append(sig)
                    mdf.extend(new_index, sigs)

                del group['record']

        return mdf

    @staticmethod
    def concatenate(files, outversion='4.10', memory='full'):
        """ concatenates several files. The files
        must have the same internal structure (same number of groups, and same
        channels in each group)

        Parameters
        ----------
        files : list | tuple
            list of *MDF* file names or *MDF* instances
        outversion : str
            merged file version
        memory : str
            memory option; default *full*

        Returns
        -------
        concatenate : MDF
            new *MDF* object with concatenated channels

        Raises
        ------
        MdfException : if there are inconsistencies between the files

        """
        if not files:
            raise MdfException('No files given for merge')

        files = [
            file if isinstance(file, MDF) else MDF(file, memory)
            for file in files
        ]

        timestamps = [
            file.header.start_time
            for file in files
        ]

        oldest = min(timestamps)
        offsets = [
            (timestamp - oldest).total_seconds()
            for timestamp in timestamps
        ]

        if not len(set(len(file.groups) for file in files)) == 1:
            message = (
                "Can't merge files: "
                "difference in number of data groups"
            )
            raise MdfException(message)

        version = validate_version_argument(outversion)
        memory = validate_memory_argument(memory)

        merged = MDF(
            version=version,
            memory=memory,
        )

        merged.header.start_time = files[0].header.start_time

        for i, groups in enumerate(zip(*(file.groups for file in files))):

            channels_nr = set(len(group['channels']) for group in groups)
            if not len(channels_nr) == 1:
                message = (
                    "Can't merge files: "
                    "different channel number for data groups {}"
                )
                raise MdfException(message.format(i))

            mdf = files[0]
            excluded_channels = mdf._excluded_channels(i)
            channels_nr = len(groups[0]['channels'])

            if memory == 'minimum':
                y_axis = MERGE_MINIMUM
            else:
                y_axis = MERGE_LOW

            read_size = np.interp(
                channels_nr,
                CHANNEL_COUNT,
                y_axis,
            )

            group_channels = [group['channels'] for group in groups]
            for j, channels in enumerate(zip(*group_channels)):
                if memory == 'minimum':
                    names = []
                    for file in files:
                        if file.version in MDF2_VERSIONS + MDF3_VERSIONS:
                            grp = file.groups[i]
                            if grp['data_location'] == 0:
                                stream = file._file
                            else:
                                stream = file._tempfile

                            channel = ChannelV3(
                                address=grp['channels'][j],
                                stream=stream,
                            )

                            if channel.get('long_name_addr', 0):
                                name = get_text_v3(
                                    channel['long_name_addr'],
                                    stream,
                                )
                            else:
                                name = (
                                    channel['short_name']
                                    .decode('latin-1')
                                    .strip(' \r\n\t\0')
                                    .split('\\')[0]
                                )
                        else:
                            grp = file.groups[i]
                            if grp['data_location'] == 0:
                                stream = file._file
                            else:
                                stream = file._tempfile

                            channel = ChannelV4(
                                address=grp['channels'][j],
                                stream=stream,
                            )
                            name = get_text_v4(
                                channel['name_addr'],
                                stream,
                            )
                        name = name.split('\\')[0]
                        names.append(name)
                    names = set(names)
                else:
                    names = set(ch.name for ch in channels)
                if not len(names) == 1:
                    message = (
                        "Can't merge files: "
                        "different channel names for data group {}"
                    )
                    raise MdfException(message.format(i))

            idx = 0
            last_timestamp = None
            for offset, group, mdf in zip(offsets, groups, files):
                if read_size:
                    mdf.configure(read_fragment_size=int(read_size))

                parents, dtypes = mdf._prepare_record(group)
                group['parents'], group['types'] = parents, dtypes

                data = mdf._load_group_data(group)

                for fragment in data:
                    if dtypes.itemsize:
                        group['record'] = np.core.records.fromstring(
                            fragment[0],
                            dtype=dtypes,
                        )
                    else:
                        group['record'] = None
                    if idx == 0:
                        signals = []
                        for j in range(channels_nr):
                            if j in excluded_channels:
                                continue
                            sig = mdf.get(
                                group=i,
                                index=j,
                                data=fragment,
                                raw=True,
                            )

                            if offset:
                                sig.timestamps = sig.timestamps + offset

                            if version < '4.00' and sig.samples.dtype.kind == 'S':
                                string_dtypes = [np.dtype('S'), ]
                                for tmp_mdf in files:
                                    strsig = tmp_mdf.get(
                                        group=i,
                                        index=j,
                                        samples_only=True,
                                    )
                                    string_dtypes.append(strsig.dtype)
                                    del strsig

                                sig.samples = sig.samples.astype(max(string_dtypes))

                                del string_dtypes

                            if not sig.samples.flags.writeable:
                                sig.samples = sig.samples.copy()
                            signals.append(sig)

                        if len(signals[0]):
                            last_timestamp = signals[0].timestamps[-1]
                            delta = last_timestamp / len(signals[0])

                        merged.append(signals, common_timebase=True)
                        idx += 1
                    else:
                        master = mdf.get_master(i, fragment)
                        if offset:
                            master = master + offset
                        if len(master):
                            if last_timestamp is None:
                                last_timestamp = master[-1]
                                delta = last_timestamp / len(master)
                            else:
                                if last_timestamp >= master[0]:
                                    master += last_timestamp + delta - master[0]
                                last_timestamp = master[-1]

                            signals = [master, ]

                            for j in range(channels_nr):
                                if j in excluded_channels:
                                    continue
                                signals.append(
                                    mdf.get(
                                        group=i,
                                        index=j,
                                        data=fragment,
                                        raw=True,
                                        samples_only=True,
                                    )
                                )

                            merged.extend(i, signals)
                        idx += 1

                    del group['record']

        return merged

    @staticmethod
    def merge(files, outversion='4.10', memory='full'):
        """ concatenates several files. The files
        must have the same internal structure (same number of groups, and same
        channels in each group)

        Parameters
        ----------
        files : list | tuple
            list of *MDF* file names or *MDF* instances
        outversion : str
            merged file version
        memory : str
            memory option; default *full*

        Returns
        -------
        concatenate : MDF
            new *MDF* object with concatenated channels

        Raises
        ------
        MdfException : if there are inconsistencies between the files

        """
        return MDF.concatenate(files, outversion, memory)

    @staticmethod
    def stack(files, outversion='4.10', memory='full', sync=True):
        """ merge several files and return the merged *MDF* object

        Parameters
        ----------
        files : list | tuple
            list of *MDF* file names or *MDF* instances
        outversion : str
            merged file version
        memory : str
            memory option; default *full*
        sync : bool
            sync the files based on the start of measurement, default *True*

        Returns
        -------
        merged : MDF
            new *MDF* object with merge channels

        """
        if not files:
            raise MdfException('No files given for merge')

        version = validate_version_argument(outversion)
        memory = validate_memory_argument(memory)

        merged = MDF(
            version=version,
            memory=memory,
        )

        if sync:
            timestamps = []
            for file in files:
                if isinstance(file, MDF):
                    timestamps.append(file.header.start_time)
                else:
                    with open(file, 'rb') as mdf:
                        mdf.seek(64)
                        blk_id = mdf.read(2)
                        if blk_id == b'HD':
                            header = HeaderV3
                        else:
                            blk_id += mdf.read(2)
                            if blk_id == b'##HD':
                                header = HeaderV4
                            else:
                                raise MdfException('"{}" is not a valid MDF file'.format(file))

                        header = header(
                            address=64,
                            stream=mdf,
                        )

                        timestamps.append(header.start_time)

            oldest = min(timestamps)
            offsets = [
                (timestamp - oldest).total_seconds()
                for timestamp in timestamps
            ]

            merged.header.start_time = oldest

        files = (
            file if isinstance(file, MDF) else MDF(file, memory)
            for file in files
        )

        for offset, mdf in zip(offsets, files):
            for i, group in enumerate(mdf.groups):
                idx = 0
                channels_nr = len(group['channels'])
                excluded_channels = mdf._excluded_channels(i)

                parents, dtypes = mdf._prepare_record(group)
                group['parents'], group['types'] = parents, dtypes

                data = mdf._load_group_data(group)

                for fragment in data:
                    if dtypes.itemsize:
                        group['record'] = np.core.records.fromstring(
                            fragment[0],
                            dtype=dtypes,
                        )
                    else:
                        group['record'] = None
                    if idx == 0:
                        signals = []
                        for j in range(channels_nr):
                            if j in excluded_channels:
                                continue
                            sig = mdf.get(
                                group=i,
                                index=j,
                                data=fragment,
                                raw=True,
                            )

                            if sync:
                                sig.timestamps = sig.timestamps + offset

                            if version < '4.00' and sig.samples.dtype.kind == 'S':
                                string_dtypes = [np.dtype('S'), ]
                                for tmp_mdf in files:
                                    strsig = tmp_mdf.get(
                                        group=i,
                                        index=j,
                                        samples_only=True,
                                    )
                                    string_dtypes.append(strsig.dtype)
                                    del strsig

                                sig.samples = sig.samples.astype(max(string_dtypes))

                                del string_dtypes

                            if not sig.samples.flags.writeable:
                                sig.samples = sig.samples.copy()
                            signals.append(sig)

                        merged.append(signals, common_timebase=True)
                        idx += 1
                    else:
                        master = mdf.get_master(i, fragment)
                        if sync:
                            master = master + offset
                        if len(master):

                            signals = [master, ]

                            for j in range(channels_nr):
                                if j in excluded_channels:
                                    continue
                                signals.append(
                                    mdf.get(
                                        group=i,
                                        index=j,
                                        data=fragment,
                                        raw=True,
                                        samples_only=True,
                                    )
                                )

                            merged.extend(i, signals)
                        idx += 1

                    del group['record']

        return merged

    def iter_channels(self, skip_master=True):
        """ generator that yields a *Signal* for each non-master channel

        Parameters
        ----------
        skip_master : bool
            do not yield master channels; default *True*

        """
        for i, group in enumerate(self.groups):
            try:
                master_index = self.masters_db[i]
            except KeyError:
                master_index = -1

            for j, _ in enumerate(group['channels']):
                if skip_master and j == master_index:
                    continue
                yield self.get(group=i, index=j)

    def iter_groups(self):
        """ generator that yields channel groups as pandas DataFrames"""

        for i, group in enumerate(self.groups):
            master_index = self.masters_db.get(i, -1)

            if master_index >= 0:
                master_name = self.get_channel_name(i, master_index)
            else:
                master_name = 'Idx'

            master = []

            names = [
                self.get_channel_name(i, j)
                for j, _ in enumerate(group['channels'])
                if j != master_index
            ]

            sigs = [
                []
                for j, _ in enumerate(group['channels'])
                if j != master_index
            ]

            data = self._load_group_data(group)
            for data_bytes in data:
                data_bytes = (data_bytes, )

                master.append(self.get_master(i, data=data_bytes))

                idx = 0
                for j, _ in enumerate(group['channels']):
                    if j == master_index:
                        continue
                    sigs[idx].append(
                        self.get(
                            group=i,
                            index=j,
                            data=data_bytes,
                            samples_only=True,
                        )
                    )
                    idx += 1

            pandas_dict = {}

            pandas_dict[master_name] = np.concatenate(master)

            for name, sig in zip(names, sigs):
                pandas_dict[name] = np.concatenate(sig)

                if master_index is not None:
                    master = self.get(
                        group=i,
                        index=master_index,
                        data=data_bytes,
                    )
                    pandas_dict = {master.name: master.samples}

            yield DataFrame.from_dict(pandas_dict)

    def resample(self, raster, memory='full'):
        """ resample all channels using the given raster

        Parameters
        ----------
        raster : float
            time raster is seconds
        memory : str
            memory option; default *None*

        Returns
        -------
        mdf : MDF
            new *MDF* with resampled channels

        """

        memory = validate_memory_argument(memory)

        mdf = MDF(
            version=self.version,
            memory=memory,
        )

        mdf.header.start_time = self.header.start_time

        # walk through all groups and get all channels
        for i, group in enumerate(self.groups):
            excluded_channels = self._excluded_channels(i)

            data = self._load_group_data(group)
            for idx, fragment in enumerate(data):
                if idx == 0:
                    sigs = []
                    for j, _ in enumerate(group['channels']):
                        if j in excluded_channels:
                            continue
                        sig = self.get(
                            group=i,
                            index=j,
                            data=fragment,
                            raw=True,
                            raster=raster,
                        )
                        if self.version < '4.00' and sig.samples.dtype.kind == 'S':
                            strsig = self.get(
                                group=i,
                                index=j,
                                samples_only=True,
                            )
                            sig.samples = sig.samples.astype(strsig.dtype)
                            del strsig
                        if not sig.samples.flags.writeable:
                            sig.samples = sig.samples.copy()
                        sigs.append(sig)

                    mdf.append(
                        sigs,
                        'Resampled to {}s'.format(raster),
                        common_timebase=True,
                    )

                else:
                    sigs = [self.get_master(i, data=fragment, raster=raster), ]

                    for j, _ in enumerate(group['channels']):
                        if j in excluded_channels:
                            continue
                        else:
                            sig = self.get(
                                group=i,
                                index=j,
                                data=fragment,
                                raw=True,
                                samples_only=True,
                                raster=raster,
                            )
                            if not sig.flags.writeable:
                                sig = sig.copy()
                            sigs.append(sig)
                    mdf.extend(i, sigs)
        return mdf

    def select(self, channels, dataframe=False):
        """ retreiv the channels listed in *channels* argument as *Signal*
        objects

        Parameters
        ----------
        channels : list
            list of items to be filtered; each item can be :

                * a channel name string
                * (channel name, group index, channel index) list or tuple
                * (channel name, group index) list or tuple
                * (None, group index, channel index) lsit or tuple

        dataframe: bool
            return a pandas DataFrame instead of a list of *Signals*; in this
            case the signals will be interpolated using the union of all
            timestamps

        Returns
        -------
        signals : list
            list of *Signal* objects based on the input channel list

        Examples
        --------
        >>> from asammdf import MDF, Signal
        >>> import numpy as np
        >>> t = np.arange(5)
        >>> s = np.ones(5)
        >>> mdf = MDF()
        >>> for i in range(4):
        ...     sigs = [Signal(s*(i*10+j), t, name='SIG') for j in range(1,4)]
        ...     mdf.append(sigs)
        ...
        >>> # select SIG group 0 default index 1 default, SIG group 3 index 1, SIG group 2 index 1 default and channel index 2 from group 1
        ...
        >>> mdf.select(['SIG', ('SIG', 3, 1), ['SIG', 2],  (None, 1, 2)])
        [<Signal SIG:
                samples=[ 1.  1.  1.  1.  1.]
                timestamps=[0 1 2 3 4]
                unit=""
                info=None
                comment="">
        , <Signal SIG:
                samples=[ 31.  31.  31.  31.  31.]
                timestamps=[0 1 2 3 4]
                unit=""
                info=None
                comment="">
        , <Signal SIG:
                samples=[ 21.  21.  21.  21.  21.]
                timestamps=[0 1 2 3 4]
                unit=""
                info=None
                comment="">
        , <Signal SIG:
                samples=[ 12.  12.  12.  12.  12.]
                timestamps=[0 1 2 3 4]
                unit=""
                info=None
                comment="">
        ]

        """

        # group channels by group index
        gps = {}

        indexes = []

        for item in channels:
            if isinstance(item, (list, tuple)):
                if len(item) not in (2, 3):
                    raise MdfException(
                        'The items used for filtering must be strings, '
                        'or they must match the first 3 argumens of the get '
                        'method'
                    )
                else:
                    group, index = self._validate_channel_selection(*item)
                    indexes.append((group, index))
                    if group not in gps:
                        gps[group] = set()
                    gps[group].add(index)
            else:
                name = item
                group, index = self._validate_channel_selection(name)
                indexes.append((group, index))
                if group not in gps:
                    gps[group] = set()
                gps[group].add(index)

        signal_parts = {}
        for group in gps:
            grp = self.groups[group]
            data = self._load_group_data(grp)
            parents, dtypes = self._prepare_record(grp)
            grp['parents'], grp['types'] = parents, dtypes

            for fragment in data:
                if dtypes.itemsize:
                    grp['record'] = np.core.records.fromstring(
                        fragment[0],
                        dtype=dtypes,
                    )
                else:
                    grp['record'] = None
                for index in gps[group]:
                    signal = self.get(group=group, index=index, data=fragment)
                    if (group, index) not in signal_parts:
                        signal_parts[(group, index)] = [signal, ]
                    else:
                        signal_parts[(group, index)].append(signal)
                del grp['record']

        signals = []
        for pair in indexes:
            parts = signal_parts[pair]
            signal = Signal(
                np.concatenate([part.samples for part in parts]),
                np.concatenate([part.timestamps for part in parts]),
                unit=parts[0].unit,
                name=parts[0].name,
                comment=parts[0].comment,
                raw=parts[0].raw,
                conversion=parts[0].conversion,
            )
            signals.append(signal)

        if dataframe:
            times = [s.timestamps for s in signals]
            t = reduce(np.union1d, times).flatten().astype(np.float64)
            signals = [s.interp(t) for s in signals]

            pandas_dict = {'t': t}
            for sig in signals:
                pandas_dict[sig.name] = sig.samples

            signals = DataFrame.from_dict(pandas_dict)

        return signals

    def whereis(self, channel):
        """ get ocurrences of channel name in the file

        Parameters
        ----------
        channel : str
            channel name string

        Returns
        -------
        ocurrences : tuple


        Examples
        --------
        >>> mdf = MDF(file_name)
        >>> mdf.whereis('VehicleSpeed') # "VehicleSpeed" exists in the file
        ((1, 2), (2, 4))
        >>> mdf.whereis('VehicleSPD') # "VehicleSPD" doesn't exist in the file
        ()

        """
        if channel in self:
            return tuple(self.channels_db[channel])
        else:
            return tuple()


if __name__ == '__main__':
    pass
