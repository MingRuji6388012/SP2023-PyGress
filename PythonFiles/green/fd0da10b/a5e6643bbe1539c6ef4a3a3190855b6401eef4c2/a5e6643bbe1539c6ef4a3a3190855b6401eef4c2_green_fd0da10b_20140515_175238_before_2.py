from __future__ import unicode_literals
import unittest

from green.version import __version__, pretty_version
import green.version



class TestVersion(unittest.TestCase):

    def test_versionType(self):
        "__version__ is a string"
        self.assertEqual(type(__version__), type(''))


    def test_versionSet(self):
        "__version__ is not blank"
        self.assertTrue(len(__version__) > 0)


    def test_pretty_version(self):
        pv = pretty_version()
        self.assertTrue('Green' in pv)
        self.assertTrue('Python' in pv)
        if green.version.coverage:
            self.assertTrue('Coverage' in pv)

