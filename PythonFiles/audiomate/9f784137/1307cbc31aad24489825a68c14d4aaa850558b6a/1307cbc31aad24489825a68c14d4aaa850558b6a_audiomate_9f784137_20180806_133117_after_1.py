"""
The assets module contains data-structures that are contained in a corpus.
"""

from .file import File  # noqa: F401
from .utterance import Utterance  # noqa: F401

from .issuer import Gender  # noqa: F401
from .issuer import AgeGroup  # noqa: F401
from .issuer import Issuer  # noqa: F401
from .issuer import Speaker  # noqa: F401
from .issuer import Artist  # noqa: F401

from .label import Label  # noqa: F401
from .label import LabelList  # noqa: F401

from .features import FeatureContainer  # noqa: F401
from .features import PartitioningFeatureIterator  # noqa: F401

# Definition of common Label-List identifiers
LL_DOMAIN = 'domain'
LL_DOMAIN_MUSIC = 'music'
LL_DOMAIN_SPEECH = 'speech'
LL_DOMAIN_NOISE = 'noise'

LL_WORD_TRANSCRIPT = 'word-transcript'
LL_WORD_TRANSCRIPT_RAW = 'word-transcript-raw'
LL_WORD_TRANSCRIPT_ALIGNED = 'word-transcript-aligned'

LL_PHONE_TRANSCRIPT = 'phone-transcript'
LL_PHONE_TRANSCRIPT_ALIGNED = 'phone-transcript-aligned'

LL_GENRE = 'genre'

LL_SOUND_CLASS = 'sound-class'
