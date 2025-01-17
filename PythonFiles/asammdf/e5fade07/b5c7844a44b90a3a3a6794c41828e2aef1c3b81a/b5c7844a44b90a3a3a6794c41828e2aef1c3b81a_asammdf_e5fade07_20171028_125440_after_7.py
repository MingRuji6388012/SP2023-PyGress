# -*- coding: utf-8 -*-
"""
MDF v3 constants
"""
# byte order
BYTE_ORDER_INTEL = 0
BYTE_ORDER_MOTOROLA = 1

# data types
DATA_TYPE_UNSIGNED = 0
DATA_TYPE_SIGNED = 1
DATA_TYPE_FLOAT = 2
DATA_TYPE_DOUBLE = 3
DATA_TYPE_STRING = 7
DATA_TYPE_BYTEARRAY = 8
DATA_TYPE_UNSIGNED_INTEL = 13
DATA_TYPE_UNSIGNED_MOTOROLA = 9
DATA_TYPE_SIGNED_INTEL = 14
DATA_TYPE_SIGNED_MOTOROLA = 10
DATA_TYPE_FLOAT_INTEL = 15
DATA_TYPE_FLOAT_MOTOROLA = 11
DATA_TYPE_DOUBLE_INTEL = 16
DATA_TYPE_DOUBLE_MOTOROLA = 12

SIGNED_INT = {
    DATA_TYPE_SIGNED,
    DATA_TYPE_SIGNED_INTEL,
    DATA_TYPE_SIGNED_MOTOROLA,
}
STANDARD_INT_SIZES = {8, 16, 32, 64}

INT_TYPES = {
    DATA_TYPE_UNSIGNED,
    DATA_TYPE_SIGNED,
    DATA_TYPE_UNSIGNED_INTEL,
    DATA_TYPE_UNSIGNED_MOTOROLA,
    DATA_TYPE_SIGNED_INTEL,
    DATA_TYPE_SIGNED_MOTOROLA,
}

# channel types
CHANNEL_TYPE_VALUE = 0
CHANNEL_TYPE_MASTER = 1

# channel conversion types
CONVERSION_TYPE_NONE = 65535
CONVERSION_TYPE_LINEAR = 0
CONVERSION_TYPE_TABI = 1
CONVERSION_TYPE_TABX = 2
CONVERSION_TYPE_POLY = 6
CONVERSION_TYPE_EXPO = 7
CONVERSION_TYPE_LOGH = 8
CONVERSION_TYPE_RAT = 9
CONVERSION_TYPE_FORMULA = 10
CONVERSION_TYPE_VTAB = 11
CONVERSION_TYPE_VTABR = 12

RAT_CONV_TEXT = '(P1 * X**2 + P2 * X + P3) / (P4 * X**2 + P5 * X + P6)'
POLY_CONVE_SHORT_TEXT = 'P4 * X / P1'
POLY_CONV_LONG_TEXT = '(P2 - (P4 * (X - P5 -P6))) / (P3* (X - P5 - P6) - P1)'

DEPENDENCY_TYPE_NONE = 0
DEPENDENCY_TYPE_VECTOR = 1
DEPENDENCY_TYPE_NDIM = 256

# flags
FLAG_PRECISION = 1
FLAG_PHY_RANGE_OK = 2
FLAG_VAL_RANGE_OK = 8

# channel source types
SOURCE_ECU = 2
SOURCE_VECTOR = 19

# bus types
BUS_TYPE_NONE = 0
BUS_TYPE_CAN = 2
BUS_TYPE_FLEXRAY = 5

# file IO seek types
SEEK_START = 0
SEEK_REL = 1
SEEK_END = 2

# blocks size
ID_BLOCK_SIZE = 64
HEADER_COMMON_SIZE = 164
HEADER_POST_320_EXTRA_SIZE = 44
CE_BLOCK_SIZE = 128
FH_BLOCK_SIZE = 56
DG31_BLOCK_SIZE = 24
DG32_BLOCK_SIZE = 28
HD_BLOCK_SIZE = 104
CN_BLOCK_SIZE = 228
CG_BLOCK_SIZE = 26
CG33_BLOCK_SIZE = 30
DT_BLOCK_SIZE = 24
CC_COMMON_BLOCK_SIZE = 46
CC_COMMON_SHORT_SIZE = 42
CC_ALG_BLOCK_SIZE = 88
CC_LIN_BLOCK_SIZE = 62
CC_POLY_BLOCK_SIZE = 94
CC_EXPO_BLOCK_SIZE = 102
CC_FORMULA_BLOCK_SIZE = 304
SR_BLOCK_SIZE = 156

# max int values
MAX_UINT8 = 2 << 8 - 1
MAX_UINT16 = 2 << 16 - 1
MAX_UNIT32 = 2 << 32 - 1
MAX_UINT64 = 2 << 64 - 1

# data location
LOCATION_ORIGINAL_FILE = 0
LOCATION_TEMPORARY_FILE = 1
LOCATION_MEMORY = 2

# blocks struct fmts and keys
ID_FMT = '<8s8s8s4H2s26s2H'
ID_KEYS = ('file_identification',
           'version_str',
           'program_identification',
           'byte_order',
           'float_format',
           'mdf_version',
           'code_page',
           'reserved0',
           'reserved1',
           'unfinalized_standard_flags',
           'unfinalized_custom_flags')

HEADER_COMMON_FMT = '<2sH3IH10s8s32s32s32s32s'
HEADER_COMMON_KEYS = ('id',
                      'block_len',
                      'first_dg_addr',
                      'comment_addr',
                      'program_addr',
                      'dg_nr',
                      'date',
                      'time',
                      'author',
                      'organization',
                      'project',
                      'subject')

HEADER_POST_320_EXTRA_FMT = 'Q2H32s'
HEADER_POST_320_EXTRA_KEYS = ('abs_time',
                              'tz_offset',
                              'time_quality',
                              'timer_identification')

FMT_CHANNEL = '<2sH5IH32s128s4H3d2IH'
KEYS_CHANNEL = ('id',
                'block_len',
                'next_ch_addr',
                'conversion_addr',
                'source_depend_addr',
                'ch_depend_addr',
                'comment_addr',
                'channel_type',
                'short_name',
                'description',
                'start_offset',
                'bit_count',
                'data_type',
                'range_flag',
                'min_raw_value',
                'max_raw_value',
                'sampling_rate',
                'long_name_addr',
                'display_name_addr',
                'aditional_byte_offset')

FMT_CHANNEL_GROUP = '<2sH3I3HI'
KEYS_CHANNEL_GROUP = ('id',
                      'block_len',
                      'next_cg_addr',
                      'first_ch_addr',
                      'comment_addr',
                      'record_id',
                      'ch_nr',
                      'samples_byte_nr',
                      'cycles_nr')

FMT_DATA_GROUP_32 = '<2sH4I2H4s'
KEYS_DATA_GROUP_32 = ('id',
                      'block_len',
                      'next_dg_addr',
                      'first_cg_addr',
                      'trigger_addr',
                      'data_block_addr',
                      'cg_nr',
                      'record_id_nr',
                      'reserved0')

FMT_DATA_GROUP = '<2sH4I2H'
KEYS_DATA_GROUP = ('id',
                   'block_len',
                   'next_dg_addr',
                   'first_cg_addr',
                   'trigger_addr',
                   'data_block_addr',
                   'cg_nr',
                   'record_id_nr')

FMT_SOURCE_COMMON = '<2s2H'
FMT_SOURCE_ECU = '<2s3HI80s32s4s'
FMT_SOURCE_EXTRA_ECU = '<HI80s32s4s'
KEYS_SOURCE_ECU = ('id',
                   'block_len',
                   'type',
                   'module_nr',
                   'module_address',
                   'description',
                   'ECU_identification',
                   'reserved0')

FMT_SOURCE_VECTOR = '<2s2H2I36s36s42s'
FMT_SOURCE_EXTRA_VECTOR = '<2I36s36s42s'
KEYS_SOURCE_VECTOR = ('id',
                      'block_len',
                      'type',
                      'CAN_id',
                      'CAN_ch_index',
                      'message_name',
                      'sender_name',
                      'reserved0')

KEYS_TEXT_BLOCK = ('id', 'block_len', 'text')

FMT_CONVERSION_COMMON = FMT_CONVERSION_NONE = '<2s2H2d20s2H'
FMT_CONVERSION_COMMON_SHORT = '<H2d20s2H'

KEYS_CONVESION_NONE = ('id',
                       'block_len',
                       'range_flag',
                       'min_phy_value',
                       'max_phy_value',
                       'unit',
                       'conversion_type',
                       'ref_param_nr')

FMT_CONVERSION_FORMULA = '<2s2H2d20s2H256s'
KEYS_CONVESION_FORMULA = ('id',
                          'block_len',
                          'range_flag',
                          'min_phy_value',
                          'max_phy_value',
                          'unit',
                          'conversion_type',
                          'ref_param_nr',
                          'formula')

FMT_CONVERSION_LINEAR = '<2s2H2d20s2H2d'
KEYS_CONVESION_LINEAR = ('id',
                         'block_len',
                         'range_flag',
                         'min_phy_value',
                         'max_phy_value',
                         'unit',
                         'conversion_type',
                         'ref_param_nr',
                         'b',
                         'a')

FMT_CONVERSION_POLY_RAT = '<2s2H2d20s2H6d'
KEYS_CONVESION_POLY_RAT = ('id',
                           'block_len',
                           'range_flag',
                           'min_phy_value',
                           'max_phy_value',
                           'unit',
                           'conversion_type',
                           'ref_param_nr',
                           'P1',
                           'P2',
                           'P3',
                           'P4',
                           'P5',
                           'P6')

FMT_CONVERSION_EXPO_LOGH = '<2s2H2d20s2H7d'
KEYS_CONVESION_EXPO_LOGH = ('id',
                            'block_len',
                            'range_flag',
                            'min_phy_value',
                            'max_phy_value',
                            'unit',
                            'conversion_type',
                            'ref_param_nr',
                            'P1',
                            'P2',
                            'P3',
                            'P4',
                            'P5',
                            'P6',
                            'P7')

FMT_PROGRAM_BLOCK = '<2sH{}s'
KEYS_PROGRAM_BLOCK = ('id', 'block_len', 'data')

FMT_SAMPLE_REDUCTION_BLOCK = '<2sH3Id'
KEYS_SAMPLE_REDUCTION_BLOCK = ('id',
                               'block_len',
                               'next_sr_addr',
                               'data_block_addr',
                               'cycles_nr',
                               'time_interval')
