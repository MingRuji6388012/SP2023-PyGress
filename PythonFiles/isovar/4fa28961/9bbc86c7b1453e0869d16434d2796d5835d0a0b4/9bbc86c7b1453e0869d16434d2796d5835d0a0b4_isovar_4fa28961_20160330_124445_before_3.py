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
from isovar.reference_context import (
    reading_frame_to_offset
)
from nose.tools import eq_


def test_reading_frame_to_offset():
    eq_(reading_frame_to_offset(0), 0)
    eq_(reading_frame_to_offset(1), 2)
    eq_(reading_frame_to_offset(2), 1)