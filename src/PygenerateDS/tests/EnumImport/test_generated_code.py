#!/usr/bin/env python

"""
synopsis:
    Run unit tests for enum import.
usage:
    On the command line:
        $ cd generateds/tests
        $ python EnumImport/test_generated_code.py
    But, usually, run these tests by running the main generateds unit tests:
        $ cd generateds/tests
        $ python test.py
notes:
    Only Python 3, not Python 2, is supported for unit tests.
"""

from __future__ import print_function
import sys
import os
import unittest


class EnumTest(unittest.TestCase):

    def setUp(self):
        os.chdir('EnumImport')

    def tearDown(self):
        os.chdir('..')

    def test_enum_import(self):

        def import_check():
            from enum_import00 import EnumType01_1
            return EnumType01_1

        self.assertRaises(ImportError, import_check)

    def test_enum_type(self):
        sys.path.append('.')
        from enum_import00 import Type00_2
        testType = Type00_2()
        self.assertEqual(type(testType.get_attr1()), int)


# Make the test suite.
def suite():
    loader = unittest.defaultTestLoader
    testsuite = loader.loadTestsFromTestCase(EnumTest)
    return testsuite


# Make the test suite and run the tests.
def test():
    testsuite = suite()
    runner = unittest.TextTestRunner(sys.stdout, verbosity=2)
    runner.run(testsuite)


if __name__ == "__main__":
    test()
