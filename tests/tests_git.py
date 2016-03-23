import unittest
from cvra_packager.packager import *

try:
    from unittest.mock import *
except ImportError:
    # unittest.mock is only available in python >= 3.3
    from mock import *

class GitCloneTestCase(unittest.TestCase):
    @patch('subprocess.call')
    def test_arguments_are_passed_correctly(self, call):
        url = 'https://github.com/cvra/pid'
        dest = 'dependencies/pid'
        expected = 'git clone --recursive https://github.com/cvra/pid dependencies/pid'.split()
        clone(url, dest)
        call.assert_called_with(expected)

class GitSumboduleTestCase(unittest.TestCase):
    @patch('subprocess.call')
    def test_arguments(self, call):
        url = 'https://github.com/cvra/pid'
        dest = 'dependencies/pid'
        expected = 'git submodule add https://github.com/cvra/pid dependencies/pid'.split()
        submodule_add(url, dest)
        call.assert_called_with(expected)

