# -*- coding: utf-8 -*-
"""
ASAM MDF version 3 file format module

"""
from __future__ import print_function, division
import sys


import os
import time
import warnings

from collections import defaultdict
from functools import reduce, partial
from tempfile import TemporaryFile
from itertools import product

from numpy import (interp, linspace, dtype, array_equal, column_stack,
                   array, searchsorted, log, exp, clip, union1d, float64,
                   flip, unpackbits, packbits, roll, zeros, uint8,
                   issubdtype, unsignedinteger, arange)
from numpy.core.records import fromstring, fromarrays
from numpy.core.defchararray import encode
from numexpr import evaluate

from .utils import MdfException, get_fmt, pair, fmt_to_datatype, get_unique_name, get_min_max, fix_dtype_fields
from .signal import Signal
from . import v3constants as v3c
from .v3blocks import (Channel, ChannelConversion, ChannelDependency,
                       ChannelExtension, ChannelGroup, DataBlock, DataGroup,
                       FileIdentificationBlock, HeaderBlock, TextBlock, TriggerBlock)


get_fmt = partial(get_fmt, version=3)
fmt_to_datatype = partial(fmt_to_datatype, version=3)

PYVERSION = sys.version_info[0]
if PYVERSION == 2:
    from .utils import bytes


__all__ = ['MDF3', ]


class MDF3(object):
    """If the *name* exist it will be loaded otherwise an empty file will be created that can be later saved to disk

    Parameters
    ----------
    name : string
        mdf file name
    load_measured_data : bool
        load data option; default *True*

        * if *True* the data group binary data block will be loaded in RAM
        * if *False* the channel data is read from disk on request

    version : string
        mdf file version ('3.00', '3.10', '3.20' or '3.30'); default '3.30'

    Attributes
    ----------
    name : string
        mdf file name
    groups : list
        list of data groups
    header : OrderedDict
        mdf file header
    file_history : TextBlock
        file history text block; can be None
    load_measured_data : bool
        load measured data option
    version : str
        mdf version
    channels_db : dict
        used for fast channel access by name; for each name key the value is a list of (group index, channel index) tuples
    masters_db : dict
        used for fast master channel access; for each group index key the value is the master channel index

    """

    def __init__(self, name=None, load_measured_data=True, version='3.30'):
        self.groups = []
        self.header = None
        self.identification = None
        self.file_history = None
        self.name = name
        self.load_measured_data = load_measured_data
        self.channels_db = {}
        self.masters_db = {}

        self._master_channel_cache = {}

        # used when appending to MDF object created with load_measured_data=False
        self._tempfile = None

        if name:
            self._read()
        else:
            self.identification = FileIdentificationBlock(version=version)
            self.version = version
            self.header = HeaderBlock(version=self.version)

    def _load_group_data(self, group):
        """ get group's data block bytes"""
        if self.load_measured_data == False:
            # could be an appended group
            # for now appended groups keep the measured data in the memory.
            # the plan is to use a temp file for appended groups, to keep the
            # memory usage low.
            if group['data_location'] == v3c.LOCATION_ORIGINAL_FILE:
                # this is a group from the source file
                # so fetch the measured data from it
                with open(self.name, 'rb') as file_stream:
                    # go to the first data block of the current data group
                    dat_addr = group['data_group']['data_block_addr']

                    if group['sorted']:
                        read_size = group['size']
                        data = DataBlock(file_stream=file_stream, address=dat_addr, size=read_size)['data']

                    else:
                        read_size = group['size']
                        record_id = group['channel_group']['record_id']
                        cg_size = group['record_size']
                        record_id_nr = group['data_group']['record_id_nr'] if group['data_group']['record_id_nr'] <= 2 else 0
                        cg_data = []

                        data = DataBlock(file_stream=file_stream, address=dat_addr, size=read_size)['data']

                        i = 0
                        size = len(data)
                        while i < size:
                            rec_id = data[i]
                            # skip redord id
                            i += 1
                            rec_size = cg_size[rec_id]
                            if rec_id == record_id:
                                rec_data = data[i: i+rec_size]
                                cg_data.append(rec_data)
                            # if 2 record id's are sued skip also the second one
                            if record_id_nr == 2:
                                i += 1
                            # go to next record
                            i += rec_size
                        data = b''.join(cg_data)
            elif group['data_location'] == v3c.LOCATION_TEMPORARY_FILE:
                read_size = group['size']
                dat_addr = group['data_group']['data_block_addr']
                self._tempfile.seek(dat_addr, v3c.SEEK_START)
                data = self._tempfile.read(read_size)
        else:
            data = group['data_block']['data']
        return data

    def _prepare_record(self, group):
        """ compute record dtype and parents dict for this group

        Parameters
        ----------
        group : dict
            MDF group dict

        Returns
        -------
        parents, dtypes : dict, numpy.dtype
            mapping of channels to records fields, records fiels dtype

        """

        grp = group
        record_size = grp['channel_group']['samples_byte_nr'] << 3
        next_byte_aligned_position = 0
        types = []
        current_parent = ""
        parent_start_offset = 0
        parents = {}
        group_channels = set()

        # the channels are first sorted ascending (see __lt__ method of Channel class):
        # a channel with lower start offset is smaller, when two channels have
        # the same start offset the one with higer bit size is considered smaller.
        # The reason is that when the numpy record is built and there are overlapping
        # channels, the parent fields should be bigger (bit size) than the embedded
        # channels. For each channel the parent dict will have a (parent name, bit offset) pair:
        # the channel value is computed using the values from the parent field,
        # and the bit offset, which is the channel's bit offset within the parent bytes.
        # This means all parents will have themselves as parent, and bit offset of 0.
        # Gaps in the records are also considered. Non standard integers size is
        # adjusted to the first higher standard integer size (eq. uint of 28bits will
        # be adjusted to 32bits)

        for original_index, new_ch in sorted(enumerate(grp['channels']), key=lambda i: i[1]):
            # channels with channel dependencies are skipped from the numpy record
            if new_ch['ch_depend_addr']:
                continue

            start_offset = new_ch['start_offset']
            bit_offset = start_offset % 8
            data_type = new_ch['data_type']
            bit_count = new_ch['bit_count']
            name = new_ch.name

            # handle multiple occurance of same channel name
            name = get_unique_name(group_channels, name)
            group_channels.add(name)

            if start_offset >= next_byte_aligned_position:
                parent_start_offset = (start_offset >> 3 ) << 3


                # check if there are byte gaps in the record
                gap = (parent_start_offset - next_byte_aligned_position) >> 3
                if gap:
                    types.append( ('', 'a{}'.format(gap)) )

                # adjust size to 1, 2, 4 or 8 bytes for nonstandard integers
                size = bit_offset + bit_count
                if data_type == v3c.DATA_TYPE_STRING:
                    next_byte_aligned_position = parent_start_offset + size
                    size = size >> 3
                    if next_byte_aligned_position <= record_size:
                        types.append( (name, get_fmt(data_type, size)) )
                        parents[original_index] = name, bit_offset

                elif data_type == v3c.DATA_TYPE_BYTEARRAY:
                    size = size >> 3
                    if next_byte_aligned_position <= record_size:
                        types.append( (name, 'u1', (size, 1)) )
                        parents[original_index] = name, bit_offset

                else:
                    if size > 32:
                        next_byte_aligned_position = parent_start_offset + 64
                        size = 8
                    elif size > 16:
                        next_byte_aligned_position = parent_start_offset + 32
                        size = 4
                    elif size > 8:
                        next_byte_aligned_position = parent_start_offset + 16
                        size = 2
                    else:
                        next_byte_aligned_position = parent_start_offset + 8
                        size = 1

                    if next_byte_aligned_position <= record_size:
                        types.append( (name, get_fmt(data_type, size)) )
                        parents[original_index] = name, bit_offset

                current_parent = name
            else:
                max_overlapping_size = next_byte_aligned_position - start_offset
                if max_overlapping_size >= bit_count:
                    parents[original_index] = current_parent, start_offset - parent_start_offset
            if next_byte_aligned_position > record_size:
                break

        gap = (record_size - next_byte_aligned_position) >> 3
        if gap:
            types.append( ('', 'a{}'.format(gap)) )

        if PYVERSION == 2:
            types = fix_dtype_fields(types)

        return parents, dtype(types)

    def _get_not_byte_aligned_data(self, data, group, ch_nr):

        big_endian_types = (v3c.DATA_TYPE_UNSIGNED_MOTOROLA,
                            v3c.DATA_TYPE_FLOAT_MOTOROLA,
                            v3c.DATA_TYPE_DOUBLE_MOTOROLA,
                            v3c.DATA_TYPE_SIGNED_MOTOROLA)

        record_size = group['channel_group']['samples_byte_nr']

        channel = group['channels'][ch_nr]

        bit_offset = channel['start_offset'] % 8
        byte_offset = channel['start_offset'] // 8
        bit_count = channel['bit_count']

        byte_count = bit_offset + bit_count
        if byte_count % 8:
            byte_count = (byte_count >> 3) + 1
        else:
            byte_count >>= 3

        types = [('', 'a{}'.format(byte_offset)),
                 ('vals', '({},)u1'.format(byte_count)),
                 ('', 'a{}'.format(record_size - byte_count - byte_offset))]

        vals = fromstring(data, dtype=dtype(types))

        vals = vals['vals']

        if channel['data_type'] not in big_endian_types:
            vals = flip(vals, 1)

        vals = unpackbits(vals)
        vals = roll(vals, bit_offset)
        vals = vals.reshape((len(vals) // 8, 8))
        vals = packbits(vals)
        vals = vals.reshape((len(vals) // byte_count, byte_count))

        if bit_count < 64:
            mask = 2 ** bit_count - 1
            masks = []
            while mask:
                masks.append(mask & 0xFF)
                mask >>= 8
            for i in range(byte_count - len(masks)):
                masks.append(0)

            masks = masks[::-1]
            for i, mask in enumerate(masks):
                vals[:, i] &= mask

        if channel['data_type'] not in big_endian_types:
            vals = flip(vals, 1)

        if bit_count <= 8:
            size = 1
        elif bit_count <= 16:
            size = 2
        elif bit_count <= 32:
            size = 4
        elif bit_count <= 64:
            size = 8

        if size > byte_count:
            extra_bytes = size - byte_count
            extra = zeros((len(vals), extra_bytes), dtype=uint8)

            types = [('vals', vals.dtype, vals.shape[1:]),
                      ('', extra.dtype, extra.shape[1:])]
            vals = fromarrays([vals, extra], dtype=dtype(types))
        vals = vals.tostring()

        fmt = get_fmt(channel['data_type'], size)
        if size <= byte_count:
            types = [('vals', fmt),
                     ('', 'a{}'.format(byte_count - size))]
        else:
            types = [('vals', fmt),]

        vals = fromstring(vals, dtype=dtype(types))

        return vals['vals']

    def _read(self):
        with open(self.name, 'rb') as file_stream:

            # performance optimization
            read = file_stream.read
            seek = file_stream.seek

            dg_cntr = 0
            seek(0, v3c.SEEK_START)

            self.identification = FileIdentificationBlock(file_stream=file_stream)
            self.header = HeaderBlock(file_stream=file_stream)

            self.version = self.identification['version_str'].decode('latin-1').strip(' \n\t\x00')

            self.file_history = TextBlock(address=self.header['comment_addr'], file_stream=file_stream)

            # this will hold mapping from channel address to Channel object
            # needed for linking dependecy blocks to refernced channels after the file is loaded
            ch_map = {}

            # go to first date group
            dg_addr = self.header['first_dg_addr']
            # read each data group sequentially
            while dg_addr:
                gp = DataGroup(address=dg_addr, file_stream=file_stream)
                cg_nr = gp['cg_nr']
                cg_addr = gp['first_cg_addr']
                data_addr = gp['data_block_addr']

                # read trigger information if available
                trigger_addr = gp['trigger_addr']
                if trigger_addr:
                    trigger = TriggerBlock(address=trigger_addr, file_stream=file_stream)
                    if trigger['text_addr']:
                        trigger_text = TextBlock(address=trigger['text_addr'], file_stream=file_stream)
                    else:
                        trigger_text = None
                else:
                    trigger = None
                    trigger_text = None

                new_groups = []
                for i in range(cg_nr):

                    new_groups.append({})
                    grp = new_groups[-1]
                    grp['channels'] = []
                    grp['channel_conversions'] = []
                    grp['channel_extensions'] = []
                    grp['data_block'] = None
                    grp['texts'] = {'channels': [], 'conversion_tab': [], 'channel_group': []}
                    grp['trigger'] = [trigger, trigger_text]
                    grp['channel_dependencies'] = []

                    kargs = {'first_cg_addr': cg_addr,
                             'data_block_addr': data_addr}
                    if self.version in ('3.20', '3.30'):
                        kargs['block_len'] = v3c.DG32_BLOCK_SIZE
                    else:
                        kargs['block_len'] = v3c.DG31_BLOCK_SIZE

                    grp['data_group'] = DataGroup(**kargs)

                    # read each channel group sequentially
                    grp['channel_group'] = ChannelGroup(address=cg_addr, file_stream=file_stream)

                    # read acquisition name and comment for current channel group
                    grp['texts']['channel_group'].append({})

                    address = grp['channel_group']['comment_addr']
                    if address:
                        grp['texts']['channel_group'][-1]['comment_addr'] = TextBlock(address=address, file_stream=file_stream)

                    # go to first channel of the current channel group
                    ch_addr = grp['channel_group']['first_ch_addr']
                    ch_cntr = 0
                    grp_chs = grp['channels']
                    grp_conv = grp['channel_conversions']
                    grp_ch_texts = grp['texts']['channels']

                    while ch_addr:
                        # read channel block and create channel object
                        new_ch = Channel(address=ch_addr, file_stream=file_stream)

                        # check if it has channel dependencies
                        if new_ch['ch_depend_addr']:
                            grp['channel_dependencies'].append(ChannelDependency(address=new_ch['ch_depend_addr'], file_stream=file_stream))
                        else:
                            grp['channel_dependencies'].append(None)

                        # update channel map
                        ch_map[ch_addr] = (ch_cntr, dg_cntr)

                        # read conversion block and create channel conversion object
                        address = new_ch['conversion_addr']
                        if address:
                            new_conv = ChannelConversion(address=address, file_stream=file_stream)
                            grp_conv.append(new_conv)
                        else:
                            new_conv = None
                            grp_conv.append(None)

                        vtab_texts = {}
                        if new_conv and new_conv['conversion_type'] == v3c.CONVERSION_TYPE_VTABR:
                            for idx in range(new_conv['ref_param_nr']):
                                address = new_conv['text_{}'.format(idx)]
                                if address:
                                    vtab_texts['text_{}'.format(idx)] = TextBlock(address=address, file_stream=file_stream)
                        grp['texts']['conversion_tab'].append(vtab_texts)

                        if self.load_measured_data:
                            # read source block and create source infromation object
                            address = new_ch['source_depend_addr']
                            if address:
                                grp['channel_extensions'].append(ChannelExtension(address=address, file_stream=file_stream))
                            else:
                                grp['channel_extensions'].append(None)
                        else:
                            grp['channel_extensions'].append(None)

                        # read text fields for channel
                        ch_texts = {}
                        for key in ('long_name_addr', 'comment_addr', 'display_name_addr'):
                            address = new_ch[key]
                            if address:
                                ch_texts[key] = TextBlock(address=address, file_stream=file_stream)
                        grp_ch_texts.append(ch_texts)

                        # update channel object name and block_size attributes
                        if new_ch['long_name_addr']:
                            new_ch.name = ch_texts['long_name_addr']['text'].decode('latin-1').strip(' \n\t\x00')
                        else:
                            new_ch.name = new_ch['short_name'].decode('latin-1').strip(' \n\t\x00')

                        if new_ch.name in self.channels_db:
                            self.channels_db[new_ch.name].append((dg_cntr, ch_cntr))
                        else:
                            self.channels_db[new_ch.name] = []
                            self.channels_db[new_ch.name].append((dg_cntr, ch_cntr))

                        if new_ch['channel_type'] == v3c.CHANNEL_TYPE_MASTER:
                            self.masters_db[dg_cntr] = ch_cntr
                        # go to next channel of the current channel group
                        ch_addr = new_ch['next_ch_addr']
                        ch_cntr += 1
                        grp_chs.append(new_ch)

                    cg_addr = grp['channel_group']['next_cg_addr']
                    dg_cntr += 1

                # store channel groups record sizes dict and data block size in each
                # new group data belong to the initial unsorted group, and add
                # the key 'sorted' with the value False to use a flag;
                # this is used later if load_measured_data=False

                if cg_nr > 1:
                    # this is an unsorted file since there are multiple channel groups
                    # within a data group
                    cg_size = {}
                    size = 0
                    record_id_nr = gp['record_id_nr'] if gp['record_id_nr'] <= 2 else 0
                    for grp in new_groups:
                        size += (grp['channel_group']['samples_byte_nr'] + record_id_nr) * grp['channel_group']['cycles_nr']
                        cg_size[grp['channel_group']['record_id']] = grp['channel_group']['samples_byte_nr']

                    for grp in new_groups:
                        grp['sorted'] = False
                        grp['record_size'] = cg_size
                        grp['size'] = size
                else:
                    record_id_nr = gp['record_id_nr'] if gp['record_id_nr'] <= 2 else 0
                    grp['size'] = size = (grp['channel_group']['samples_byte_nr'] + record_id_nr) * grp['channel_group']['cycles_nr']
                    grp['sorted'] = True

                if self.load_measured_data:
                    # read data block of the current data group
                    dat_addr = gp['data_block_addr']
                    if dat_addr:
                        seek(dat_addr, v3c.SEEK_START)
                        data = read(size)
                    else:
                        data = b''
                    if cg_nr == 1:
                        grp = new_groups[0]
                        grp['data_location'] = v3c.LOCATION_MEMORY
                        kargs = {'data': data}
                        grp['data_block'] = DataBlock(**kargs)

                    else:
                        # agregate data for each record ID in the cg_data dict
                        cg_data = defaultdict(list)
                        i = 0
                        size = len(data)
                        while i < size:
                            rec_id = data[i]
                            # skip redord id
                            i += 1
                            rec_size = cg_size[rec_id]
                            rec_data = data[i: i+rec_size]
                            cg_data[rec_id].append(rec_data)
                            # if 2 record id's are sued skip also the second one
                            if record_id_nr == 2:
                                i += 1
                            # go to next record
                            i += rec_size
                        for grp in new_groups:
                            grp['data_location'] = v3c.LOCATION_MEMORY
                            kargs = {}
                            kargs['data'] = b''.join(cg_data[grp['channel_group']['record_id']])
                            grp['channel_group']['record_id'] = 1
                            grp['data_block'] = DataBlock(**kargs)
                else:
                    for grp in new_groups:
                        grp['data_location'] = v3c.LOCATION_ORIGINAL_FILE

                self.groups.extend(new_groups)

                # go to next data group
                dg_addr = gp['next_dg_addr']

            # once the file has been loaded update the channel depency refenreces
            for grp in self.groups:
                for dependency_block in grp['channel_dependencies']:
                    if dependency_block:
                        for i in range(dependency_block['sd_nr']):
                            ref_channel_addr = dependency_block['ch_{}'.format(i)]
                            dependency_block.referenced_channels.append(ch_map[ref_channel_addr])

    def add_trigger(self, group, time, pre_time=0, post_time=0, comment=''):
        """ add trigger to data group

        Parameters
        ----------
        group : int
            group index
        time : float
            trigger time
        pre_time : float
            trigger pre time; default 0
        post_time : float
            trigger post time; default 0
        comment : str
            trigger comment

        """
        gp = self.groups[group]
        trigger, trigger_text = gp['trigger']
        if trigger:
            nr = trigger['trigger_event_nr']
            trigger['trigger_event_nr'] += 1
            trigger['block_len'] += 24
            trigger['trigger_{}_time'.format(nr)] = time
            trigger['trigger_{}_pretime'.format(nr)] = pre_time
            trigger['trigger_{}_posttime'.format(nr)] = post_time
            if trigger_text is None and comment:
                trigger_text = TextBlock(text=comment)
                gp['trigger'][1] = trigger_text
        else:
            trigger = TriggerBlock(trigger_event_nr=1,
                                   trigger_0_time=time,
                                   trigger_0_pretime=pre_time,
                                   trigger_0_posttime=post_time)
            if comment:
                trigger_text = TextBlock(text=comment)
            else:
                trigger_text = None

            gp['trigger'] = [trigger, trigger_text]

    def append(self, signals, acquisition_info='Python', common_timebase=False, compact=True):
        """
        Appends a new data group.

        For channel depencies type Signals, the *samples* attribute must be a numpy.recarray

        Parameters
        ----------
        signals : list
            list on *Signal* objects
        acquisition_info : str
            acquisition information; default 'Python'
        common_timebase : bool
            flag to hint that the signals have the same timebase
        compact : bool
            compact unsigned signals if possible; this can decrease the file
            size but increases the execution time


        Examples
        --------
        >>> # case 1 conversion type None
        >>> s1 = np.array([1, 2, 3, 4, 5])
        >>> s2 = np.array([-1, -2, -3, -4, -5])
        >>> s3 = np.array([0.1, 0.04, 0.09, 0.16, 0.25])
        >>> t = np.array([0.001, 0.002, 0.003, 0.004, 0.005])
        >>> names = ['Positive', 'Negative', 'Float']
        >>> units = ['+', '-', '.f']
        >>> info = {}
        >>> s1 = Signal(samples=s1, timstamps=t, unit='+', name='Positive')
        >>> s2 = Signal(samples=s2, timstamps=t, unit='-', name='Negative')
        >>> s3 = Signal(samples=s3, timstamps=t, unit='flts', name='Floats')
        >>> mdf = MDF3('new.mdf')
        >>> mdf.append([s1, s2, s3], 'created by asammdf v1.1.0')
        >>> # case 2: VTAB conversions from channels inside another file
        >>> mdf1 = MDF3('in.mdf')
        >>> ch1 = mdf1.get("Channel1_VTAB")
        >>> ch2 = mdf1.get("Channel2_VTABR")
        >>> sigs = [ch1, ch2]
        >>> mdf2 = MDF3('out.mdf')
        >>> mdf2.append(sigs, 'created by asammdf v1.1.0')

        """
        if not signals:
            raise MdfException('"append" requires a non-empty list of Signal objects')

        # check if the signals have a common timebase
        # if not interpolate the signals using the union of all timbases
        t_ = signals[0].timestamps
        if not common_timebase:
            for s in signals[1:]:
                if not array_equal(s.timestamps, t_):
                    different = True
                    break
            else:
                different = False

            if different:
                times = [s.timestamps for s in signals]
                t = reduce(union1d, times).flatten().astype(float64)
                signals = [s.interp(t) for s in signals]
                times = None
            else:
                t = t_
        else:
            t = t_

        # split regular from composed signals. Composed signals have recarray samples
        # or multimendional ndarray.
        # The regular signals will be first added to the group.
        # The composed signals will be saved along side the fields, which will
        # be saved as new signals.
        simple_signals = [sig for sig in signals
                          if len(sig.samples.shape) <= 1
                          and sig.samples.dtype.names is None]
        composed_signals = [sig for sig in signals
                            if len(sig.samples.shape) > 1
                            or sig.samples.dtype.names]

        # mdf version 4 structure channels and CANopen types will be saved to new channel groups
        new_groups_signals = [sig for sig in composed_signals
                              if sig.samples.dtype.names
                              and sig.samples.dtype.names[0] != sig.name]
        composed_signals = [sig for sig in composed_signals
                            if not sig.samples.dtype.names
                            or sig.samples.dtype.names[0] == sig.name]

        if simple_signals or composed_signals:
            dg_cntr = len(self.groups)

            gp = {}
            gp['channels'] = gp_channels = []
            gp['channel_conversions'] = gp_conv = []
            gp['channel_extensions'] = gp_source = []
            gp['channel_dependencies'] = gp_dep = []
            gp['texts'] = gp_texts = {'channels': [],
                                      'conversion_tab': [],
                                      'channel_group': []}
            self.groups.append(gp)

            cycles_nr = len(t)
            fields = []
            types = []
            parents = {}
            ch_cntr = 0
            offset = 0
            field_names = set()

            # setup all blocks related to the time master channel

            # time channel texts
            for _, item in gp_texts.items():
                item.append({})

            gp_texts['channel_group'][-1]['comment_addr'] = TextBlock(text=acquisition_info)

            #conversion for time channel
            kargs = {'conversion_type': v3c.CONVERSION_TYPE_NONE,
                     'unit': 's'.encode('latin-1'),
                     'min_phy_value': t[0] if cycles_nr else 0,
                     'max_phy_value': t[-1] if cycles_nr else 0}
            gp_conv.append(ChannelConversion(**kargs))

            #source for time
            kargs = {'module_nr': 0,
                     'module_address': 0,
                     'type': v3c.SOURCE_ECU,
                     'description': 'Channel inserted by Python Script'.encode('latin-1')}
            gp_source.append(ChannelExtension(**kargs))

            #time channel
            t_type, t_size = fmt_to_datatype(t.dtype)
            kargs = {'short_name': 't'.encode('latin-1'),
                     'channel_type': v3c.CHANNEL_TYPE_MASTER,
                     'data_type': t_type,
                     'start_offset': 0,
                     'min_raw_value' : t[0] if cycles_nr else 0,
                     'max_raw_value' : t[-1] if cycles_nr else 0,
                     'bit_count': t_size}
            channel = Channel(**kargs)
            channel.name = name = 't'
            gp_channels.append(channel)

            if not name in self.channels_db:
                self.channels_db[name] = []
            self.channels_db[name].append((dg_cntr, ch_cntr))
            self.masters_db[dg_cntr] = 0
            # data group record parents
            parents[ch_cntr] = name, 0

            # time channel doesn't have channel dependencies
            gp_dep.append(None)

            fields.append(t)
            types.append( (name, t.dtype))
            field_names.add(name)

            offset += t_size
            ch_cntr += 1

            if compact:
                compacted_signals = [{'signal': sig} for sig in simple_signals if issubdtype(sig.samples.dtype, unsignedinteger)]

                max_itemsize = 1
                dtype_ = dtype(uint8)

                for signal in compacted_signals:
                    itemsize = signal['signal'].samples.dtype.itemsize

                    signal['min'], signal['max'] = get_min_max(signal['signal'].samples)
                    minimum_bitlength = (itemsize // 2) * 8 + 1
                    bit_length = int(signal['max']).bit_length()

                    signal['bit_count'] = max(minimum_bitlength, bit_length)

                    if itemsize > max_itemsize:
                        dtype_ = signal['signal'].samples.dtype
                        max_itemsize = itemsize

                compacted_signals.sort(key=lambda x: x['bit_count'])
                simple_signals = [sig for sig in simple_signals if not issubdtype(sig.samples.dtype, unsignedinteger)]
                dtype_size = dtype_.itemsize * 8

            else:
                compacted_signals = []

            # first try to compact unsigned integers
            while compacted_signals:
                # channels texts

                cluster = []

                tail = compacted_signals.pop()
                size = tail['bit_count']
                cluster.append(tail)

                while size < dtype_size and compacted_signals:
                    head = compacted_signals[0]
                    head_size = head['bit_count']
                    if head_size + size > dtype_size:
                        break
                    else:
                        cluster.append(compacted_signals.pop(0))
                        size += head_size

                bit_offset = 0
                field_name = get_unique_name(field_names, 'COMPACT')
                types.append( (field_name, dtype_) )
                field_names.add(field_name)

                values = zeros(cycles_nr, dtype=dtype_)

                for signal_d in cluster:

                    signal = signal_d['signal']
                    bit_count = signal_d['bit_count']
                    min_val = signal_d['min']
                    max_val = signal_d['max']

                    name = signal.name
                    for _, item in gp['texts'].items():
                        item.append({})
                    if len(name) >= 32:
                        gp_texts['channels'][-1]['long_name_addr'] = TextBlock(text=name)

                    info = signal.info
                    if info and 'raw' in info:
                        kargs = {}
                        kargs['conversion_type'] = v3c.CONVERSION_TYPE_VTAB
                        raw = info['raw']
                        phys = info['phys']
                        for i, (r_, p_) in enumerate(zip(raw, phys)):
                            kargs['text_{}'.format(i)] = p_[:31] + b'\x00'
                            kargs['param_val_{}'.format(i)] = r_
                        kargs['ref_param_nr'] = len(raw)
                        kargs['unit'] = signal.unit.encode('latin-1')
                    elif info and 'lower' in info:
                        kargs = {}
                        kargs['conversion_type'] = v3c.CONVERSION_TYPE_VTABR
                        lower = info['lower']
                        upper = info['upper']
                        texts = info['phys']
                        kargs['unit'] = signal.unit.encode('latin-1')
                        kargs['ref_param_nr'] = len(upper)

                        for i, (u_, l_, t_) in enumerate(zip(upper, lower, texts)):
                            kargs['lower_{}'.format(i)] = l_
                            kargs['upper_{}'.format(i)] = u_
                            kargs['text_{}'.format(i)] = 0
                            gp_texts['conversion_tab'][-1]['text_{}'.format(i)] = TextBlock(text=t_)

                    else:
                        kargs = {'conversion_type': v3c.CONVERSION_TYPE_NONE,
                                 'unit': signal.unit.encode('latin-1'),
                                 'min_phy_value': min_val if min_val <= max_val else 0,
                                 'max_phy_value': max_val if min_val <= max_val else 0}
                    gp_conv.append(ChannelConversion(**kargs))

                    # source for channel
                    kargs = {'module_nr': 0,
                             'module_address': 0,
                             'type': v3c.SOURCE_ECU,
                             'description': b'Channel inserted by Python Script'}
                    gp_source.append(ChannelExtension(**kargs))

                    # compute additional byte offset for large records size
                    current_offset = offset + bit_offset
                    if current_offset > v3c.MAX_UINT16:
                        additional_byte_offset = (current_offset - v3c.MAX_UINT16 ) >> 3
                        start_bit_offset = current_offset - additional_byte_offset << 3
                    else:
                        start_bit_offset = current_offset
                        additional_byte_offset = 0

                    kargs = {'short_name': (name[:31] + '\x00').encode('latin-1') if len(name) >= 32 else name.encode('latin-1'),
                             'channel_type': v3c.CHANNEL_TYPE_VALUE,
                             'data_type': v3c.DATA_TYPE_UNSIGNED_INTEL,
                             'min_raw_value': min_val if min_val <= max_val else 0,
                             'max_raw_value': max_val if min_val <= max_val else 0,
                             'start_offset': start_bit_offset,
                             'bit_count': bit_count,
                             'aditional_byte_offset' : additional_byte_offset}
                    comment = signal.comment
                    if comment:
                        if len(comment) >= 128:
                            comment = (comment[:127] + '\x00').encode('latin-1')
                        else:
                            comment = comment.encode('latin-1')
                        kargs['description'] = comment

                    channel = Channel(**kargs)
                    channel.name = name
                    gp_channels.append(channel)

                    if name not in self.channels_db:
                        self.channels_db[name] = []
                    self.channels_db[name].append((dg_cntr, ch_cntr))

                    # update the parents as well
                    parents[ch_cntr] = field_name, bit_offset

                    # simple channels don't have channel dependencies
                    gp_dep.append(None)

                    values += signal.samples.astype(dtype_) << bit_offset
                    bit_offset += bit_count

                    ch_cntr += 1

                    # simple channels don't have channel dependencies
                    gp_dep.append(None)

                offset += dtype_.itemsize * 8
                fields.append(values)

            # first add the signals in the simple signal list
            for signal in simple_signals:
                # channels texts
                name = signal.name
                for _, item in gp['texts'].items():
                    item.append({})
                if len(name) >= 32:
                    gp_texts['channels'][-1]['long_name_addr'] = TextBlock(text=name)

                # conversions for channel
                min_val, max_val = get_min_max(signal.samples)

                info = signal.info
                if info and 'raw' in info:
                    kargs = {}
                    kargs['conversion_type'] = v3c.CONVERSION_TYPE_VTAB
                    raw = info['raw']
                    phys = info['phys']
                    for i, (r_, p_) in enumerate(zip(raw, phys)):
                        kargs['text_{}'.format(i)] = p_[:31] + b'\x00'
                        kargs['param_val_{}'.format(i)] = r_
                    kargs['ref_param_nr'] = len(raw)
                    kargs['unit'] = signal.unit.encode('latin-1')
                elif info and 'lower' in info:
                    kargs = {}
                    kargs['conversion_type'] = v3c.CONVERSION_TYPE_VTABR
                    lower = info['lower']
                    upper = info['upper']
                    texts = info['phys']
                    kargs['unit'] = signal.unit.encode('latin-1')
                    kargs['ref_param_nr'] = len(upper)

                    for i, (u_, l_, t_) in enumerate(zip(upper, lower, texts)):
                        kargs['lower_{}'.format(i)] = l_
                        kargs['upper_{}'.format(i)] = u_
                        kargs['text_{}'.format(i)] = 0
                        gp_texts['conversion_tab'][-1]['text_{}'.format(i)] = TextBlock(text=t_)

                else:
                    kargs = {'conversion_type': v3c.CONVERSION_TYPE_NONE,
                             'unit': signal.unit.encode('latin-1'),
                             'min_phy_value': min_val if min_val <= max_val else 0,
                             'max_phy_value': max_val if min_val <= max_val else 0}
                gp_conv.append(ChannelConversion(**kargs))

                # source for channel
                kargs = {'module_nr': 0,
                         'module_address': 0,
                         'type': v3c.SOURCE_ECU,
                         'description': b'Channel inserted by Python Script'}
                gp_source.append(ChannelExtension(**kargs))

                # compute additional byte offset for large records size
                if offset > v3c.MAX_UINT16:
                    additional_byte_offset = (offset - v3c.MAX_UINT16 ) >> 3
                    start_bit_offset = offset - additional_byte_offset << 3
                else:
                    start_bit_offset = offset
                    additional_byte_offset = 0
                s_type, s_size = fmt_to_datatype(signal.samples.dtype)
                kargs = {'short_name': (name[:31] + '\x00').encode('latin-1') if len(name) >= 32 else name.encode('latin-1'),
                         'channel_type': v3c.CHANNEL_TYPE_VALUE,
                         'data_type': s_type,
                         'min_raw_value': min_val if min_val <= max_val else 0,
                         'max_raw_value': max_val if min_val <= max_val else 0,
                         'start_offset': start_bit_offset,
                         'bit_count': s_size,
                         'aditional_byte_offset' : additional_byte_offset}
                comment = signal.comment
                if comment:
                    if len(comment) >= 128:
                        comment = (comment[:127] + '\x00').encode('latin-1')
                    else:
                        comment = comment.encode('latin-1')
                    kargs['description'] = comment

                channel = Channel(**kargs)
                channel.name = name
                gp_channels.append(channel)
                offset += s_size

                if not name in self.channels_db:
                    self.channels_db[name] = []
                self.channels_db[name].append((dg_cntr, ch_cntr))

                # update the parents as well
                field_name = get_unique_name(field_names, name)
                parents[ch_cntr] = field_name, 0

                fields.append(signal.samples)
                types.append( (field_name, signal.samples.dtype) )
                field_names.add(field_name)

                ch_cntr += 1

                # simple channels don't have channel dependencies
                gp_dep.append(None)

            # second, add the composed signals
            for signal in composed_signals:
                names = signal.samples.dtype.names
                name = signal.name

                component_names = []
                component_samples = []
                if names:
                    samples = signal.samples[names[0]]
                else:
                    samples = signal.samples

                shape = samples.shape[1:]
                dims = [list(range(size)) for size in shape]

                for indexes in product(*dims):
                    subarray = samples
                    for idx in indexes:
                        subarray = subarray[:, idx]
                    component_samples.append(subarray)
                    component_names.append('{}{}'.format(name, ''.join('[{}]'.format(idx) for idx in indexes)))

                # add channel dependency block for composed parent channel
                sd_nr = len(component_samples)
                kargs = {'sd_nr': sd_nr}
                for i, dim in enumerate(shape[::-1]):
                    kargs['dim_{}'.format(i)] = dim
                parent_dep = ChannelDependency(**kargs)
                gp_dep.append(parent_dep)

                if names:
                    component_samples.extend([signal.samples[name_] for name_ in names[1:]])
                    component_names.extend(names[1:])

                # add composed parent signal texts
                for _, item in gp['texts'].items():
                    item.append({})
                if len(name) >= 32:
                    gp_texts['channels'][-1]['long_name_addr'] = TextBlock(text=name)

                # composed parent has no conversion
                gp_conv.append(None)

                # add parent and components sources
                kargs = {'module_nr': 0,
                         'module_address': 0,
                         'type': v3c.SOURCE_ECU,
                         'description': b'Channel inserted by Python Script'}
                gp_source.append(ChannelExtension(**kargs))

                min_val, max_val = get_min_max(samples)

                s_type, s_size = fmt_to_datatype(samples.dtype)
                # compute additional byte offset for large records size
                if offset > v3c.MAX_UINT16:
                    additional_byte_offset = (offset - v3c.MAX_UINT16 ) >> 3
                    start_bit_offset = offset - additional_byte_offset << 3
                else:
                    start_bit_offset = offset
                    additional_byte_offset = 0
                kargs = {'short_name': (name[:31] + '\x00').encode('latin-1') if len(name) >= 32 else name.encode('latin-1'),
                         'channel_type': v3c.CHANNEL_TYPE_VALUE,
                         'data_type': s_type,
                         'min_raw_value': min_val if min_val <= max_val else 0,
                         'max_raw_value': max_val if min_val <= max_val else 0,
                         'start_offset': start_bit_offset,
                         'bit_count': s_size,
                         'aditional_byte_offset' : additional_byte_offset}
                comment = signal.comment
                if comment:
                    if len(comment) >= 128:
                        comment = (comment[:127] + '\x00').encode('latin-1')
                    else:
                        comment = comment.encode('latin-1')
                    kargs['description'] = comment

                channel = Channel(**kargs)
                channel.name = name
                gp_channels.append(channel)

                if not name in self.channels_db:
                    self.channels_db[name] = []
                self.channels_db[name].append((dg_cntr, ch_cntr))

                ch_cntr += 1

                for i, (name, samples) in enumerate(zip(component_names, component_samples)):
                    for _, item in gp['texts'].items():
                        item.append({})
                    if len(name) >= 32:
                        gp_texts['channels'][-1]['long_name_addr'] = TextBlock(text=name)

                    min_val, max_val = get_min_max(samples)
                    s_type, s_size = fmt_to_datatype(samples.dtype)
                    shape = samples.shape[1:]

                    kargs = {'module_nr': 0,
                             'module_address': 0,
                             'type': v3c.SOURCE_ECU,
                             'description': b'Channel inserted by Python Script'}
                    gp_source.append(ChannelExtension(**kargs))

                    gp_conv.append(None)

                    # compute additional byte offset for large records size
                    if offset > v3c.MAX_UINT16:
                        additional_byte_offset = (offset - v3c.MAX_UINT16 ) >> 3
                        start_bit_offset = offset - additional_byte_offset << 3
                    else:
                        start_bit_offset = offset
                        additional_byte_offset = 0

                    kargs = {'short_name': (name[:31] + '\x00').encode('latin-1') if len(name) >= 32 else name.encode('latin-1'),
                             'channel_type': v3c.CHANNEL_TYPE_VALUE,
                             'data_type': s_type,
                             'min_raw_value': min_val if min_val <= max_val else 0,
                             'max_raw_value': max_val if min_val <= max_val else 0,
                             'start_offset': start_bit_offset,
                             'bit_count': s_size,
                             'aditional_byte_offset' : additional_byte_offset}

                    channel = Channel(**kargs)
                    channel.name = name
                    gp_channels.append(channel)
                    size = s_size
                    for dim in shape:
                        size *= dim
                    offset += size

                    if not name in self.channels_db:
                        self.channels_db[name] = []
                    self.channels_db[name].append((dg_cntr, ch_cntr))

                    # update the parents as well
                    field_name = get_unique_name(field_names, name)
                    parents[ch_cntr] = field_name, 0

                    fields.append(samples)
                    types.append( (field_name, samples.dtype, shape) )
                    field_names.add(field_name)

                    gp_dep.append(None)

                    if i < sd_nr:
                        parent_dep.referenced_channels.append((ch_cntr, dg_cntr))
                    else:
                        channel['description'] = '{} - axis {}'.format(signal.name, name).encode('latin-1')

                    ch_cntr += 1

            #channel group
            kargs = {'cycles_nr': cycles_nr,
                     'samples_byte_nr': offset >> 3}
            gp['channel_group'] = ChannelGroup(**kargs)
            gp['channel_group']['ch_nr'] = ch_cntr
            gp['size'] = cycles_nr * (offset >> 3)

            #data group
            kargs = {'block_len': v3c.DG32_BLOCK_SIZE if self.version in ('3.20', '3.30') else v3c.DG31_BLOCK_SIZE}
            gp['data_group'] = DataGroup(**kargs)

            #data block
            if PYVERSION == 2:
                types = fix_dtype_fields(types)
            types = dtype(types)

            gp['types'] = types
            gp['parents'] = parents
            gp['sorted'] = True

            samples = fromarrays(fields, dtype=types)
            block = samples.tostring()

            if self.load_measured_data:
                gp['data_location'] = v3c.LOCATION_MEMORY
                kargs = {'data': block}
                gp['data_block'] = DataBlock(**kargs)
            else:
                gp['data_location'] = v3c.LOCATION_TEMPORARY_FILE
                if self._tempfile is None:
                    self._tempfile = TemporaryFile()
                self._tempfile.seek(0, v3c.SEEK_END)
                data_address = self._tempfile.tell()
                gp['data_group']['data_block_addr'] = data_address
                self._tempfile.write(block)

            # data group trigger
            gp['trigger'] = [None, None]

        for signal in new_groups_signals:
            dg_cntr = len(self.groups)
            gp = {}
            gp['channels'] = gp_channels = []
            gp['channel_conversions'] = gp_conv = []
            gp['channel_extensions'] = gp_source = []
            gp['channel_dependencies'] = gp_dep = []
            gp['texts'] = gp_texts = {'channels': [],
                                      'conversion_tab': [],
                                      'channel_group': []}
            self.groups.append(gp)

            cycles_nr = len(t)
            fields = []
            types = []
            parents = {}
            ch_cntr = 0
            offset = 0
            field_names = set()

            # setup all blocks related to the time master channel

            # time channel texts
            for _, item in gp_texts.items():
                item.append({})

            gp_texts['channel_group'][-1]['comment_addr'] = TextBlock(text=acquisition_info)

            #conversion for time channel
            kargs = {'conversion_type': v3c.CONVERSION_TYPE_NONE,
                     'unit': 's'.encode('latin-1'),
                     'min_phy_value': t[0] if cycles_nr else 0,
                     'max_phy_value': t[-1] if cycles_nr else 0}
            gp_conv.append(ChannelConversion(**kargs))

            #source for time
            kargs = {'module_nr': 0,
                     'module_address': 0,
                     'type': v3c.SOURCE_ECU,
                     'description': 'Channel inserted by Python Script'.encode('latin-1')}
            gp_source.append(ChannelExtension(**kargs))

            #time channel
            t_type, t_size = fmt_to_datatype(t.dtype)
            kargs = {'short_name': 't'.encode('latin-1'),
                     'channel_type': v3c.CHANNEL_TYPE_MASTER,
                     'data_type': t_type,
                     'start_offset': 0,
                     'min_raw_value' : t[0] if cycles_nr else 0,
                     'max_raw_value' : t[-1] if cycles_nr else 0,
                     'bit_count': t_size}
            channel = Channel(**kargs)
            channel.name = name = 't'
            gp_channels.append(channel)

            if not name in self.channels_db:
                self.channels_db[name] = []
            self.channels_db[name].append((dg_cntr, ch_cntr))
            self.masters_db[dg_cntr] = 0
            # data group record parents
            parents[ch_cntr] = name, 0

            # time channel doesn't have channel dependencies
            gp_dep.append(None)

            fields.append(t)
            types.append( (name, t.dtype))
            field_names.add(name)

            offset += t_size
            ch_cntr += 1

            names = signal.samples.dtype.names
            if names == ('ms', 'days'):
                gp_texts['channel_group'][-1]['comment_addr'] = TextBlock(text='From mdf version 4 CANopen Time channel')
            elif names == ('ms', 'min', 'hour', 'day', 'month', 'year', 'summer_time', 'day_of_week'):
                gp_texts['channel_group'][-1]['comment_addr'] = TextBlock(text='From mdf version 4 CANopen Date channel')
            else:
                gp_texts['channel_group'][-1]['comment_addr'] = TextBlock(text='From mdf version 4 structure channel composition')

            for name in names:

                samples = signal.samples[name]

                # channels texts
                for _, item in gp['texts'].items():
                    item.append({})
                if len(name) >= 32:
                    gp_texts['channels'][-1]['long_name_addr'] = TextBlock(text=name)

                # conversions for channel
                min_val, max_val = get_min_max(signal.samples)

                kargs = {'conversion_type': v3c.CONVERSION_TYPE_NONE,
                         'unit': signal.unit.encode('latin-1'),
                         'min_phy_value': min_val if min_val <= max_val else 0,
                         'max_phy_value': max_val if min_val <= max_val else 0}
                gp_conv.append(ChannelConversion(**kargs))

                # source for channel
                kargs = {'module_nr': 0,
                         'module_address': 0,
                         'type': v3c.SOURCE_ECU,
                         'description': b'Channel inserted by Python Script'}
                gp_source.append(ChannelExtension(**kargs))

                # compute additional byte offset for large records size
                if offset > v3c.MAX_UINT16:
                    additional_byte_offset = (offset - v3c.MAX_UINT16 ) >> 3
                    start_bit_offset = offset - additional_byte_offset << 3
                else:
                    start_bit_offset = offset
                    additional_byte_offset = 0
                s_type, s_size = fmt_to_datatype(samples.dtype)
                kargs = {'short_name': (name[:31] + '\x00').encode('latin-1') if len(name) >= 32 else name.encode('latin-1'),
                         'channel_type': v3c.CHANNEL_TYPE_VALUE,
                         'data_type': s_type,
                         'min_raw_value': min_val if min_val <= max_val else 0,
                         'max_raw_value': max_val if min_val <= max_val else 0,
                         'start_offset': start_bit_offset,
                         'bit_count': s_size,
                         'aditional_byte_offset' : additional_byte_offset}

                channel = Channel(**kargs)
                channel.name = name
                gp_channels.append(channel)
                offset += s_size

                if not name in self.channels_db:
                    self.channels_db[name] = []
                self.channels_db[name].append((dg_cntr, ch_cntr))

                # update the parents as well
                field_name = get_unique_name(field_names, name)
                parents[ch_cntr] = field_name, 0

                fields.append(samples)
                types.append( (field_name, samples.dtype) )
                field_names.add(field_name)

                ch_cntr += 1

                # simple channels don't have channel dependencies
                gp_dep.append(None)

            # channel group
            kargs = {'cycles_nr': cycles_nr,
                     'samples_byte_nr': offset >> 3}
            gp['channel_group'] = ChannelGroup(**kargs)
            gp['channel_group']['ch_nr'] = ch_cntr
            gp['size'] = cycles_nr * (offset >> 3)

            #data group
            kargs = {'block_len': v3c.DG32_BLOCK_SIZE if self.version in ('3.20', '3.30') else v3c.DG31_BLOCK_SIZE}
            gp['data_group'] = DataGroup(**kargs)

            #data block
            if PYVERSION == 2:
                types = fix_dtype_fields(types)
            types = dtype(types)

            gp['types'] = types
            gp['parents'] = parents
            gp['sorted'] = True

            samples = fromarrays(fields, dtype=types)
            block = samples.tostring()

            if self.load_measured_data:
                gp['data_location'] = v3c.LOCATION_MEMORY
                kargs = {'data': block}
                gp['data_block'] = DataBlock(**kargs)
            else:
                gp['data_location'] = v3c.LOCATION_TEMPORARY_FILE
                if self._tempfile is None:
                    self._tempfile = TemporaryFile()
                self._tempfile.seek(0, v3c.SEEK_END)
                data_address = self._tempfile.tell()
                gp['data_group']['data_block_addr'] = data_address
                self._tempfile.write(block)

            # data group trigger
            gp['trigger'] = [None, None]

    def close(self):
        """ if the MDF was created with load_measured_data=False and new channels
        have been appended, then this must be called just before the object is not
        used anymore to clean-up the temporary file"""
        if self.load_measured_data == False and self._tempfile is not None:
            self._tempfile.close()

    def get(self, name=None, group=None, index=None, raster=None, samples_only=False):
        """Gets channel samples.
        Channel can be specified in two ways:

        * using the first positional argument *name*

            * if there are multiple occurances for this channel then the *group* and *index* arguments can be used to select a specific group.
            * if there are multiple occurances for this channel and either the *group* or *index* arguments is None then a warning is issued

        * using the group number (keyword argument *group*) and the channel number (keyword argument *index*). Use *info* method for group and channel numbers


        If the *raster* keyword argument is not *None* the output is interpolated accordingly

        Parameters
        ----------
        name : string
            name of channel
        group : int
            0-based group index
        index : int
            0-based channel index
        raster : float
            time raster in seconds
        samples_only : bool
            if *True* return only the channel samples as numpy array; if *False* return a *Signal* object

        Returns
        -------
        res : (numpy.array | Signal)
            returns *Signal* if *samples_only*=*False* (default option), otherwise returns numpy.array.
            The *Signal* samples are:

                * numpy recarray for channels that have CDBLOCK or BYTEARRAY type channels
                * numpy array for all the rest

        Raises
        ------
        MdfError :

        * if the channel name is not found
        * if the group index is out of range
        * if the channel index is out of range

        """
        if name is None:
            if group is None or index is None:
                raise MdfException('Invalid arguments for "get" method: must give "name" or, "group" and "index"')
            else:
                gp_nr, ch_nr = group, index
                if gp_nr > len(self.groups) - 1:
                    raise MdfException('Group index out of range')
                if index > len(self.groups[gp_nr]['channels']) - 1:
                    raise MdfException('Channel index out of range')
        else:
            if not name in self.channels_db:
                raise MdfException('Channel "{}" not found'.format(name))
            else:
                if group is None or index is None:
                    gp_nr, ch_nr = self.channels_db[name][0]
                    if len(self.channels_db[name]) > 1:
                        warnings.warn('Multiple occurances for channel "{}". Using first occurance from data group {}. Provide both "group" and "index" arguments to select another data group'.format(name, gp_nr))
                else:
                    for gp_nr, ch_nr in self.channels_db[name]:
                        if (gp_nr, ch_nr) == (group, index):
                            break
                    else:
                        gp_nr, ch_nr = self.channels_db[name][0]
                        warnings.warn('You have selected group "{}" for channel "{}", but this channel was not found in this group. Using first occurance of "{}" from group "{}"'.format(group, name, name, gp_nr))


        grp = self.groups[gp_nr]
        channel = grp['channels'][ch_nr]
        conversion = grp['channel_conversions'][ch_nr]
        dependency_block = grp['channel_dependencies'][ch_nr]
        cycles_nr = grp['channel_group']['cycles_nr']

        # get data group record
        data = self._load_group_data(grp)

        info = None

        # check if this is a channel array
        if dependency_block:
            if dependency_block['dependency_type'] == v3c.DEPENDENCY_TYPE_VECTOR:
                shape = [dependency_block['sd_nr'], ]
            elif dependency_block['dependency_type'] >= v3c.DEPENDENCY_TYPE_NDIM:
                shape = []
                i = 0
                while True:
                    try:
                        dim = dependency_block['dim_{}'.format(i)]
                        shape.append(dim)
                        i += 1
                    except KeyError:
                        break
                shape = shape[::-1]

            record_shape = tuple(shape)

            arrays = [self.get(group=dg_nr, index=ch_nr, samples_only=True) for ch_nr, dg_nr in dependency_block.referenced_channels]
            if cycles_nr:
                shape.insert(0, cycles_nr)

            vals = column_stack(arrays).flatten().reshape(tuple(shape))

            arrays = [vals, ]
            types = [ (channel.name, vals.dtype, record_shape), ]

            if PYVERSION == 2:
                types = fix_dtype_fields(types)

            types = dtype(types)
            vals = fromarrays(arrays, dtype=types)

        else:
            # get channel values
            try:
                parents, dtypes = grp['parents'], grp['types']
            except KeyError:
                grp['parents'], grp['types'] = self._prepare_record(grp)
                parents, dtypes = grp['parents'], grp['types']

            try:
                parent, bit_offset = parents[ch_nr]
            except:
                parent, bit_offset = None, None

            if parent is not None:
                if 'record' not in grp:
                    if dtypes.itemsize:
                        record = fromstring(data, dtype=dtypes)
                    else:
                        record = None

                    if self.load_measured_data:
                        grp['record'] = record
                else:
                    record = grp['record']

                vals = record[parent]
                bits = channel['bit_count']
                data_type = channel['data_type']

                if bit_offset:
                    if data_type in v3c.SIGNED_INT:
                        dtype_ = vals.dtype
                        size = vals.dtype.itemsize
                        vals = vals.astype(dtype('<u{}'.format(size)))

                        vals = vals >> bit_offset

                        vals = vals.astype(dtype_)
                    else:
                        vals = vals >> bit_offset

                if data_type in v3c.INT_TYPES:
                    if bits not in v3c.STANDARD_INT_SIZES:
                        dtype_= vals.dtype
                        vals = vals & ((1<<bits) - 1)
                        if data_type in v3c.SIGNED_INT:
                            vals = vals.astype(dtype_)
            else:
                vals = self._get_not_byte_aligned_data(data, grp, ch_nr)

            if conversion is None:
                conversion_type = v3c.CONVERSION_TYPE_NONE
            else:
                conversion_type = conversion['conversion_type']

            if conversion_type == v3c.CONVERSION_TYPE_NONE:

                if channel['data_type'] == v3c.DATA_TYPE_STRING:
                    vals = [val.tobytes() for val in vals]
                    vals = array([x.decode('latin-1').strip(' \n\t\x00') for x in vals])
                    vals = encode(vals, 'latin-1')

                elif channel['data_type'] == v3c.DATA_TYPE_BYTEARRAY:
                    arrays = [vals, ]
                    types = [ (channel.name, vals.dtype, vals.shape[1:]), ]
                    if PYVERSION == 2:
                        types = fix_dtype_fields(types)
                    types = dtype(types)
                    vals = fromarrays(arrays, dtype=types)

            elif conversion_type == v3c.CONVERSION_TYPE_LINEAR:
                a = conversion['a']
                b = conversion['b']
                if (a, b) != (1, 0):
                    vals = vals * a
                    if b:
                        vals += b

            elif conversion_type in (v3c.CONVERSION_TYPE_TABI, v3c.CONVERSION_TYPE_TABX):
                nr = conversion['ref_param_nr']
                raw = array([conversion['raw_{}'.format(i)] for i in range(nr)])
                phys = array([conversion['phys_{}'.format(i)] for i in range(nr)])
                if conversion_type == v3c.CONVERSION_TYPE_TABI:
                    vals = interp(vals, raw, phys)
                else:
                    idx = searchsorted(raw, vals)
                    idx = clip(idx, 0, len(raw) - 1)
                    vals = phys[idx]

            elif conversion_type == v3c.CONVERSION_TYPE_VTAB:
                nr = conversion['ref_param_nr']
                raw = array([conversion['param_val_{}'.format(i)] for i in range(nr)])
                phys = array([conversion['text_{}'.format(i)] for i in range(nr)])
                info = {'raw': raw, 'phys': phys}

            elif conversion_type == v3c.CONVERSION_TYPE_VTABR:
                nr = conversion['ref_param_nr']

                texts = array([grp['texts']['conversion_tab'][ch_nr].get('text_{}'.format(i), {}).get('text', b'') for i in range(nr)])
                lower = array([conversion['lower_{}'.format(i)] for i in range(nr)])
                upper = array([conversion['upper_{}'.format(i)] for i in range(nr)])
                info = {'lower': lower, 'upper': upper, 'phys': texts}

            elif conversion_type in (v3c.CONVERSION_TYPE_EXPO, v3c.CONVERSION_TYPE_LOGH):
                func = log if conversion_type == v3c.CONVERSION_TYPE_EXPO else exp
                P1 = conversion['P1']
                P2 = conversion['P2']
                P3 = conversion['P3']
                P4 = conversion['P4']
                P5 = conversion['P5']
                P6 = conversion['P6']
                P7 = conversion['P7']
                if P4 == 0:
                    vals = func(((vals - P7) * P6 - P3) / P1) / P2
                elif P1 == 0:
                    vals = func((P3 / (vals - P7) - P6) / P4) / P5
                else:
                    raise ValueError('wrong conversion type {}'.format(conversion_type))

            elif conversion_type == v3c.CONVERSION_TYPE_RAT:
                P1 = conversion['P1']
                P2 = conversion['P2']
                P3 = conversion['P3']
                P4 = conversion['P4']
                P5 = conversion['P5']
                P6 = conversion['P6']
                if not (P1, P2, P3, P4, P5, P6) == (0, 1, 0, 0, 0, 1):
                    X = vals
                    vals = evaluate('(P1 * X**2 + P2 * X + P3) / (P4 * X**2 + P5 * X + P6)')

            elif conversion_type == v3c.CONVERSION_TYPE_POLY:
                P1 = conversion['P1']
                P2 = conversion['P2']
                P3 = conversion['P3']
                P4 = conversion['P4']
                P5 = conversion['P5']
                P6 = conversion['P6']
                
                X = vals
                
                coefs = (P2, P3, P5, P6)
                if coefs == (0, 0, 0, 0):
                    if not P1 == P4:
                        vals = evaluate('P4 * X / P1')
                else:
                    vals = evaluate('(P2 - (P4 * (X - P5 -P6))) / (P3* (X - P5 - P6) - P1)')

            elif conversion_type == v3c.CONVERSION_TYPE_FORMULA:
                formula = conversion['formula'].decode('latin-1').strip(' \n\t\x00')
                X1 = vals
                vals = evaluate(formula)

        if samples_only:
            res = vals
        else:
            if conversion:
                unit = conversion['unit'].decode('latin-1').strip(' \n\t\x00')
            else:
                unit = ''
            comment = channel['description'].decode('latin-1').strip(' \t\n\x00')

            t = self.get_master(gp_nr, data)

            res = Signal(samples=vals,
                         timestamps=t,
                         unit=unit,
                         name=channel.name,
                         comment=comment,
                         info=info)

            if raster and t:
                tx = linspace(0, t[-1], int(t[-1] / raster))
                res = res.interp(tx)

        return res


    def get_master(self, index, data=None):
        """ returns master channel samples for given group

        Parameters
        ----------
        index : int
            group index
        data : bytes
            data block raw bytes; default None

        Returns
        -------
        t : numpy.array
            master channel samples

        """
        if index in self._master_channel_cache:
            return self._master_channel_cache[index]
        group = self.groups[index]

        time_ch_nr = self.masters_db.get(index, None)
        cycles_nr = group['channel_group']['cycles_nr']

        if time_ch_nr is None:
            t = arange(cycles_nr, dtype=float64)
        else:
            time_conv = group['channel_conversions'][time_ch_nr]
            time_ch = group['channels'][time_ch_nr]

            if time_ch['bit_count'] == 0:
                if time_ch['sampling_rate']:
                    sampling_rate = time_ch['sampling_rate']
                else:
                    sampling_rate = 1
                t = arange(cycles_nr, dtype=float64) * sampling_rate
            else:
                # get data group parents and dtypes
                try:
                    parents, dtypes = group['parents'], group['types']
                except KeyError:
                    group['parents'], group['types'] = self._prepare_record(group)
                    parents, dtypes = group['parents'], group['types']

                # get data group record
                if data is None:
                    data = self._load_group_data(group)

                parent, bit_offset = parents.get(time_ch_nr, (None, None))
                if parent is not None:
                    not_found = object()
                    record = group.get('record', not_found)
                    if record is not_found:
                        if dtypes.itemsize:
                            record = fromstring(data, dtype=dtypes)
                        else:
                            record = None

                        if self.load_measured_data:
                            group['record'] = record
                    t = record[parent]
                else:
                    t = self._get_not_byte_aligned_data(data, group, time_ch_nr)

                # get timestamps
                time_conv_type = v3c.CONVERSION_TYPE_NONE if time_conv is None else time_conv['conversion_type']
                if time_conv_type == v3c.CONVERSION_TYPE_LINEAR:
                    time_a = time_conv['a']
                    time_b = time_conv['b']
                    t = t * time_a
                    if time_b:
                        t += time_b
        self._master_channel_cache[index] = t
        return t

    def iter_get_triggers(self):
        """ generator that yields triggers

        Returns
        -------
        trigger_info : dict
            trigger information with the following keys:

                * comment : trigger comment
                * time : trigger time
                * pre_time : trigger pre time
                * post_time : trigger post time
                * index : trigger index
                * group : data group index of trigger
        """
        for i, gp in enumerate(self.groups):
            trigger, trigger_text = gp['trigger']
            if trigger:
                if trigger_text:
                    comment = trigger_text['text'].decode('latin-1').strip(' \n\t\x00')
                else:
                    comment = ''

                for j in range(trigger['trigger_events_nr']):
                    trigger_info = {'comment': comment,
                                    'index' : j,
                                    'group': i,
                                    'time' : trigger['trigger_{}_time'.format(j)],
                                    'pre_time' : trigger['trigger_{}_pretime'.format(j)],
                                    'post_time' : trigger['trigger_{}_posttime'.format(j)]}
                    yield trigger_info

    def info(self):
        """get MDF information as a dict

        Examples
        --------
        >>> mdf = MDF3('test.mdf')
        >>> mdf.info()

        """
        info = {}
        info['version'] = self.identification['version_str'].strip(b'\x00').decode('latin-1').strip(' \n\t\x00')
        info['author'] = self.header['author'].strip(b'\x00').decode('latin-1').strip(' \n\t\x00')
        info['organization'] = self.header['organization'].strip(b'\x00').decode('latin-1').strip(' \n\t\x00')
        info['project'] = self.header['project'].strip(b'\x00').decode('latin-1').strip(' \n\t\x00')
        info['subject'] = self.header['subject'].strip(b'\x00').decode('latin-1').strip(' \n\t\x00')
        info['groups'] = len(self.groups)
        for i, gp in enumerate(self.groups):
            inf = {}
            info['group {}'.format(i)] = inf
            inf['cycles'] = gp['channel_group']['cycles_nr']
            inf['channels count'] = len(gp['channels'])
            for j, ch in enumerate(gp['channels']):
                inf['channel {}'.format(j)] = (ch.name, ch['channel_type'])

        return info

    def save(self, dst='', overwrite=False, compression=0):
        """Save MDF to *dst*. If *dst* is not provided the the destination file name is
        the MDF name. If overwrite is *True* then the destination file is overwritten,
        otherwise the file name is appened with '_xx', were 'xx' is the first conter that produces a new
        file name (that does not already exist in the filesystem)

        Parameters
        ----------
        dst : str
            destination file name, Default ''
        overwrite : bool
            overwrite flag, default *False*
        compression : int
            does nothing for mdf version3; introduced here to share the same API as mdf version 4 files

        """

        if self.file_history is None:
            self.file_history = TextBlock(text='''<FHcomment>
<TX>created</TX>
<tool_id>asammdf</tool_id>
<tool_vendor> </tool_vendor>
<tool_version>2.4.1</tool_version>
</FHcomment>''')
        else:
            text = self.file_history['text'] + '\n{}: updated byt Python script'.format(time.asctime()).encode('latin-1')
            self.file_history = TextBlock(text=text)

        if self.name is None and dst == '':
            raise MdfException('Must specify a destination file name for MDF created from scratch')

        dst = dst if dst else self.name
        if overwrite == False:
            if os.path.isfile(dst):
                cntr = 0
                while True:
                    name = os.path.splitext(dst)[0] + '_{}.mdf'.format(cntr)
                    if not os.path.isfile(name):
                        break
                    else:
                        cntr += 1
                warnings.warn('Destination file "{}" already exists and "overwrite" is False. Saving MDF file as "{}"'.format(dst, name))
                dst = name

        # all MDF blocks are appended to the blocks list in the order in which
        # they will be written to disk. While creating this list, all the relevant
        # block links are updated so that once all blocks have been added to the list
        # they can simply be written (using the bytes protocol).
        # DataGroup blocks are written first after the identification and header blocks.
        # When load_measured_data=False we need to restore the original data block addresses
        # within the data group block. This is needed to allow further work with the object
        # after the save method call (eq. new calls to get method). Since the data group blocks
        # are written first, it is safe to restor the original links when the data blocks
        # are written. For lado_measured_data=False, the blocks list will contain a tuple
        # instead of a DataBlock instance; the tuple will have the reference to the
        # data group object and the original link to the data block in the soource MDF file.

        with open(dst, 'wb') as dst:
            #store unique texts and their addresses
            defined_texts = {}
            # list of all blocks
            blocks = []

            address = 0

            blocks.append(self.identification)
            address += v3c.ID_BLOCK_SIZE

            blocks.append(self.header)
            address += self.header['block_len']

            self.file_history.address = address
            blocks.append(self.file_history)
            address += self.file_history['block_len']

            # DataGroup
            # put them first in the block list so they will be written first to disk
            # this way, in case of load_measured_data=False, we can safely restore
            # the original data block address
            for gp in self.groups:
                dg = gp['data_group']
                blocks.append(dg)
                dg.address = address
                address += dg['block_len']
            for i, dg in enumerate(self.groups[:-1]):
                dg['data_group']['next_dg_addr'] = self.groups[i+1]['data_group'].address
            self.groups[-1]['data_group']['next_dg_addr'] = 0

            for index, gp in enumerate(self.groups):
                gp_texts = gp['texts']

                # Texts
                for item_list in gp_texts.values():
                    for my_dict in item_list:
                        for key, tx_block in my_dict.items():
                            #text blocks can be shared
                            text = tx_block['text']
                            if text in defined_texts:
                                tx_block.address = defined_texts[text]
                            else:
                                defined_texts[text] = address
                                tx_block.address = address
                                blocks.append(tx_block)
                                address += tx_block['block_len']

                # ChannelConversions
                cc = gp['channel_conversions']
                for i, conv in enumerate(cc):
                    if conv:
                        conv.address = address
                        if conv['conversion_type'] == v3c.CONVERSION_TYPE_VTABR:
                            for key, item in gp_texts['conversion_tab'][i].items():
                                conv[key] = item.address

                        blocks.append(conv)
                        address += conv['block_len']

                # Channel Extension
                cs = gp['channel_extensions']
                for source in cs:
                    if source:
                        source.address = address
                        blocks.append(source)
                        address += source['block_len']

                # Channel Dependency
                cd = gp['channel_dependencies']
                for dep in cd:
                    if dep:
                        dep.address = address
                        blocks.append(dep)
                        address += dep['block_len']

                # Channels
                ch_texts = gp_texts['channels']
                for i, channel in enumerate(gp['channels']):
                    channel.address = address
                    channel_texts = ch_texts[i]

                    blocks.append(channel)
                    address += v3c.CN_BLOCK_SIZE

                    for key in ('long_name_addr', 'comment_addr', 'display_name_addr'):
                        if key in channel_texts:
                            channel[key] = channel_texts[key].address
                        else:
                            channel[key] = 0

                    channel['conversion_addr'] = cc[i].address if cc[i] else 0
                    channel['source_depend_addr'] = cs[i].address if cs[i] else 0
                    if cd[i]:
                        channel['ch_depend_addr'] = cd[i].address
                    else:
                        channel['ch_depend_addr'] = 0

                for channel, next_channel in pair(gp['channels']):
                    channel['next_ch_addr'] = next_channel.address
                next_channel['next_ch_addr'] = 0

                # ChannelGroup
                cg = gp['channel_group']
                cg.address = address
                blocks.append(cg)
                address += cg['block_len']

                cg['first_ch_addr'] = gp['channels'][0].address
                cg['next_cg_addr'] = 0
                if 'comment_addr' in gp['texts']['channel_group'][0]:
                    cg['comment_addr'] = gp_texts['channel_group'][0]['comment_addr'].address

                # TriggerBLock
                trigger, trigger_text = gp['trigger']
                if trigger:
                    if trigger_text:
                        trigger_text.address = address
                        blocks.append(trigger_text)
                        address += trigger_text['block_len']
                        trigger['comment_addr'] = trigger_text.address
                    else:
                        trigger['comment_addr'] = 0

                    trigger.address = address
                    blocks.append(trigger)
                    address += trigger['block_len']

                # DataBlock
                original_data_addr = gp['data_group']['data_block_addr']
                gp['data_group']['data_block_addr'] = address if gp['size'] else 0
                address += gp['size']
                if self.load_measured_data:
                    blocks.append(gp['data_block'])
                else:
                    # trying to call bytes([gp, address]) will result in an exception
                    # that be used as a flag for non existing data block in case
                    # of load_measured_data=False, the address is the actual address
                    # of the data group's data within the original file
                    blocks.append([gp, original_data_addr])

            # update referenced channels addresses within the channel dependecies
            for gp in self.groups:
                for dep in gp['channel_dependencies']:
                    if dep:
                        for i, (ch_nr, dg_nr) in enumerate(dep.referenced_channels):
                            grp = self.groups[dg_nr]
                            ch = grp['channels'][ch_nr]
                            dep['ch_{}'.format(i)] = ch.address
                            dep['cg_{}'.format(i)] = grp['channel_group'].address
                            dep['dg_{}'.format(i)] = grp['data_group'].address

            # DataGroup
            for gp in self.groups:
                gp['data_group']['first_cg_addr'] = gp['channel_group'].address
                gp['data_group']['trigger_addr'] = gp['trigger'][0].address if gp['trigger'][0] else 0

            if self.groups:
                self.header['first_dg_addr'] = self.groups[0]['data_group'].address
                self.header['dg_nr'] = len(self.groups)
                self.header['comment_addr'] = self.file_history.address
                self.header['program_addr'] = 0

            write = dst.write
            for block in blocks:
                try:
                    write(bytes(block))
                except:
                    # this will only be executed for data blocks when load_measured_data=False
                    gp, address = block
                    # restore data block address from original file so that
                    # future calls to get will still work after the save
                    gp['data_group']['data_block_addr'] = address
                    data = self._load_group_data(gp)
                    write(data)


if __name__ == '__main__':
    pass
