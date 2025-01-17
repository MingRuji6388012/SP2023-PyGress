# Copyright (c) 2016. Mount Sinai School of Medicine
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function, division, absolute_import
from itertools import chain
from six import add_metaclass, string_types
from six.moves import zip

class MetaclassCollectSlots(type):
    """
    Metaclass which concatenates all __slots__ fields
    from the inheritance hierarchy into a single class member
    called _fields (which is also how namedtuple objects expose their
    field names).
    """
    def __init__(self, name, bases, dictionary):
        """
        Get all field names of this class by traversing
        its inheritance hierarchy in reverse order and
        concatenating the names in __slots__.
        """
        type.__init__(self, name, bases, dictionary)
        inherited_class_order = reversed(self.__mro__)
        self._fields = tuple(
            chain.from_iterable(
                getattr(cls, '__slots__', [])
                for cls in inherited_class_order))

@add_metaclass(MetaclassCollectSlots)
class CompactObject(object):
    """
    Base class for objects which define their fields
    via __slots__ to decrease memory footporint and
    speed up field access.
    """
    __slots__ = []

    def _values_generator(self):
        return (getattr(self, name) for name in self._fields)

    @property
    def _values(self):
        return tuple(self._values_generator())

    def __str__(self):
        field_strings = []
        for name, value in zip(self._fields, self._values):
            format_string = (
                "%s='%s'" if isinstance(value, string_types) else "%s=%s")
            field_strings.append(format_string % (name, value))
        return "%s(%s)" % (
            self.__class__.__name__,
            ", ".join(field_strings))

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self._values)

    def __eq__(self, other):
        return self.__class__ is other.__class__ and all(
            value_self == value_other
            for (value_self, value_other) in
            zip(self._values_generator(), other._values_generator()))
