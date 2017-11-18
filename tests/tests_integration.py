import unittest
from cvra_packager.packager import *
from os.path import join

try:
    from unittest.mock import *
except ImportError:
    # unittest.mock is only available in python >= 3.3
    from mock import *


class ArgumentParsingTestCase(unittest.TestCase):
    def test_initial_value_is_clone(self):
        """
        Checks that the initial download method is clone.
        """
        commandline = "".split()
        args = parse_args(commandline)
        self.assertEqual(args.download_method, clone)

    def test_can_use_submodules(self):
        """
        Checks that we can use git submodules using the long option.
        """
        commandline = "--submodules".split()
        args = parse_args(commandline)
        self.assertEqual(args.download_method, submodule_add)


class IntegrationTesting(unittest.TestCase):
    @patch('cvra_packager.packager.render_template_to_file')
    def test_all_templates_are_rendered(self, render_mock):
        """
        Tests that all templates specified in package.yml are rendered
        appropriately.
        """

        from cvra_packager.packager import main as packager_main

        pkgfile_content = '''
        dependency-dir: src
        templates:
            Makefile.jinja: Makefile
            Test.jinja: Test
        '''

        with patch('cvra_packager.packager.open', mock_open(read_data=pkgfile_content), create=True):
            packager_main()

        empty_context = {'source': [],
                         'target': {},
                         'tests': [],
                         'include_directories': ['src']
                         }

        render_mock.assert_any_call('Makefile.jinja', 'Makefile', empty_context)
        render_mock.assert_any_call('Test.jinja', 'Test', empty_context)

    @patch('cvra_packager.packager.render_template_to_file')
    def test_unit_tests_template(self, render_mock):
        """
        Tests that including tests in a package triggers the rendering of a
        CMakeLists.txt to build the unit tests.
        """
        from cvra_packager.packager import main as packager_main

        pkgfile_content = '''
        tests:
            - pid_test.cpp
        '''

        with patch('cvra_packager.packager.open', mock_open(read_data=pkgfile_content), create=True):
            packager_main()

        expected_context = {'source': [],
                            'target': {},
                            'tests': [join('.','pid_test.cpp')],
                            'include_directories': ['dependencies']
                            }
        render_mock.assert_any_call('CMakeLists.txt.jinja', 'CMakeLists.txt', expected_context)

    def test_can_find_template(self):
        """
        Checks that we can find template using create_jinja_env.

        If the environment is not correctly prepared, it will raise a
        TemplateNotFound exception.
        """
        env = create_jinja_env()
        template = env.get_template('CMakeLists.txt.jinja')

