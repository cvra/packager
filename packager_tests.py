#!/usr/bin/env python
import unittest
from packager import *

try:
    from unittest.mock import *
except ImportError:
    # unittest.mock is only available in python >= 3.3
    from mock import *

class RepoUrlTest(unittest.TestCase):
    def test_simple_repository(self):
        "Checks that a simple repository URL is handled correctly."
        expected = "https://github.com/cvra/pid"
        self.assertEqual(expected, url_for_package("pid"))

    def test_forked_repository(self):
        "Checks that a forked package is handled correctly"
        package_descr = {'fork':'antoinealb'}
        package = {'pid':package_descr}
        expected = "https://github.com/antoinealb/pid"
        self.assertEqual(expected, url_for_package(package))

    def test_custom_url(self):
        " Checks that a custom URL is returned unchanged. "
        URL = "https://myawesomegit.com/pid"
        package = {"pid":{"url":URL}}
        self.assertEqual(URL, url_for_package(package))

    def test_invalid_pkg_raise_execption(self):
        " Checks that an invalid package raises a ValueError. "
        # This package descr is invalid : it is not a package name nor does it
        # contain an URL/fork
        package = {"pid":{"foo":"bar"}}
        with self.assertRaises(ValueError):
            url_for_package(package)

class PackageNameTest(unittest.TestCase):
    def test_pkgname_trivial_case(self):
        """ Checks that the package name is extracted correctly from a trivial
        description (just a string). """
        package = "pid"
        self.assertEqual(package, package_name_from_desc(package))

    def test_pkgname_complex_description_works(self):
        """ Are complex description handled correctly too ? """
        package = {"pid":{"fork":"antoinealb"}}
        self.assertEqual("pid", package_name_from_desc(package))

    def test_pkgfile_trivial_case(self):
        """ Checks that we can correctly generate the package file path. """
        package = "pid"
        expected = "dependencies/pid/package.yml"
        self.assertEqual(expected, pkgfile_for_package(package))

    def test_pkgfile_complex_case(self):
        """
        Checks that we can correctly find the package.yml file for complex packages.
        """
        package = {"pid":{"fork":"antoinealb"}}
        expected = "dependencies/pid/package.yml"
        self.assertEqual(expected, pkgfile_for_package(package))

    def test_path_for_package_simple_case(self):
        """
        Checks that we can find the path to a package directory (trivial case).
        """
        package = "pid"
        expected = "dependencies/pid"
        self.assertEqual(expected, path_for_package(package))

    def test_path_for_package_complex_case(self):
        """ Checks package path for complex description. """
        package = {"pid":{"fork":"antoinealb"}}
        self.assertEqual("dependencies/pid", path_for_package(package))


class DependencyTestCase(unittest.TestCase):

    def setUp(self):
        self.clone = Mock()

    def test_no_dependency_no_clone(self):
        """
        Checks that a package without dependencies will not create any download
        operation.
        """
        package = {} # no dependencies
        download_dependencies(package, method=self.clone)

        self.assertEqual([], self.clone.call_args_list)

    @patch('os.path.exists')
    @patch('packager.open_package')
    def test_dependency_already_there(self, open_package, exists):
        """
        Checks that if a package is already downloaded we don't download it
        again.
        """
        open_package.return_value = {}
        exists.return_value = True

        package = {"depends":["pid"]}
        download_dependencies(package, method=self.clone)

        self.assertEqual([], self.clone.call_args_list)

    @patch('os.path.exists')
    @patch('packager.open_package')
    def test_dependency_download_single_level(self, open_package, exists):
        """
        Checks that we correctly download a needed dependency.
        """
        open_package.return_value = {}
        exists.return_value = False # not yet downloaded

        package = {"depends":["pid"]}
        download_dependencies(package, method=self.clone)

        self.clone.assert_called_with('https://github.com/cvra/pid', 'dependencies/pid')

    @patch('os.path.exists')
    @patch('packager.open_package')
    def test_dependency_has_a_dependency_itself(self, open_package, exists):
        """
        Checks that if a dependency of the package has itself a dependency it
        will be cloned too.
        """

        exists.return_value = False # we did not download anything yet

        # simulates loading a package with dependency
        pid_package = {'depends':['test-runner']}
        testrunner_package = {}
        open_package.side_effect = [pid_package, testrunner_package]

        package = {"depends":['pid']}
        download_dependencies(package, method=self.clone)

        self.clone.assert_any_call('https://github.com/cvra/pid', 'dependencies/pid')
        self.clone.assert_any_call('https://github.com/cvra/test-runner', 'dependencies/test-runner')

    @patch('os.path.exists')
    @patch('packager.open_package')
    def test_multiple_dependencies(self, open_package, exists):
        """
        Checks that we correctly download a needed dependency.
        """
        open_package.return_value = {}
        exists.return_value = False # not yet downloaded

        package = {"depends":["pid", "test-runner"]}
        download_dependencies(package, method=self.clone)

        self.clone.assert_any_call('https://github.com/cvra/pid', 'dependencies/pid')
        self.clone.assert_any_call('https://github.com/cvra/test-runner', 'dependencies/test-runner')


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

class OpenPackageTestCase(unittest.TestCase):
    def test_load_simple_package(self):
        """
        Tests that loading a package given its simple description (name string)
        works as expected.
        """

        package_content = """
        source:
            - pid.c
            - pidconfig.c
        """

        with patch('packager.open', mock_open(read_data=package_content), create=True):
            package = open_package('pid')

        expected = {"source":['pid.c', 'pidconfig.c']}
        self.assertEqual(expected, package)

class GenerateSourceListTestCase(unittest.TestCase):
    def test_source_empty_package(self):
        """
        Tests that asking for a category not in the package returns an empty
        set.
        """
        package = {}
        result = generate_source_list(package, 'sources')
        self.assertEqual([], result)

    def test_source_package_no_dep(self):
        """
        Tests getting the sources from a package with no dependencies.
        """
        package = {'sources':['pid.c']}
        result = generate_source_list(package, 'sources')
        self.assertEqual(['./pid.c'], result)

    @patch('packager.open_package')
    def test_source_package_dep(self, open_package_mock):
        """
        Tests that dependencies sources are included in the result.
        """

        package = {'sources':['application.c'],'depends':['pid']}
        pid_package = {'sources':['pid.c']}
        open_package_mock.return_value = pid_package

        result = generate_source_list(package, 'sources')
        expected = ['./application.c', 'dependencies/pid/pid.c']

        self.assertEqual(sorted(expected), sorted(result))

    def test_source_dict_contains_correct_categories(self):
        """
        Tests that the source dictionnary contains all needed categories even
        when the package doesn't.
        """
        result = generate_source_dict({})
        self.assertIn('source', result)
        self.assertIn('tests', result)
        self.assertIn('target', result)
        self.assertIn('x86', result['target'])
        self.assertIn('arm', result['target'])
        self.assertIn('include_directories', result)

    def test_target_source_are_sorted(self):
        """
        Tests if the target source list is sorted.
        """
        package = {'target.arm':['b', 'a']}
        result = generate_source_dict(package)['target']['arm']
        self.assertEqual(result, sorted(result))

    def test_test_source_is_sorted_too(self):
        """
        Checks if the tests source list is sorted too.
        """
        package = {'tests':['b', 'a']}
        result = generate_source_dict(package)['tests']
        self.assertEqual(result, sorted(result))


    @patch('packager.open_package')
    def test_include_directory_dep(self, open_package_mock):
        """
        Tests that dependencies include directories are included in the result.
        """
        package = {'sources':['application.c'],'depends':['pid']}
        pid_package = {'sources':['pid.c'], 'include_directories':['poney']}
        open_package_mock.return_value = pid_package

        result = generate_source_list(package, 'include_directories')
        expected = [os.path.join(DEPENDENCIES_DIR, 'pid', 'poney')]

        self.assertEqual(result, expected)

class TemplateRenderingTestCase(unittest.TestCase):

    @patch('packager.open', new_callable=mock_open, create=True)
    @patch('packager.create_jinja_env')
    def test_can_render_template_correctly(self, create_env_mock, open_mock):
        """
        Checks that we can render template to files correctly.
        """
        # Setups a mock Jinja2 environment factory
        templates = {
                'test.jinja':'{{content}}'
                }
        loader = jinja2.DictLoader(templates)
        env = jinja2.Environment(loader=loader)
        create_env_mock.return_value = env

        # Dummy render context
        context = {'content':'OLOL'}

        render_template_to_file('test.jinja', 'dest', context)

        # Checks that the result was written to the correct file
        open_mock.assert_any_call('dest', 'w')
        open_mock().write.assert_any_call('OLOL')

class IntegrationTesting(unittest.TestCase):
    @patch('packager.render_template_to_file')
    def test_all_templates_are_rendered(self, render_mock):
        """
        Tests that all templates specified in package.yml are rendered
        appropriately.
        """

        from packager import main as packager_main

        pkgfile_content = '''
        templates:
            Makefile.jinja: Makefile
            Test.jinja: Test
        '''

        with patch('packager.open', mock_open(read_data=pkgfile_content), create=True):
            packager_main()

        empty_context = {'source': [],
                         'target': {'arm': [], 'x86': []},
                         'tests': [],
                         'include_directories': ['dependencies/']
                         }

        render_mock.assert_any_call('Makefile.jinja', 'Makefile', empty_context)
        render_mock.assert_any_call('Test.jinja', 'Test', empty_context)

    @patch('packager.render_template_to_file')
    def test_unit_tests_template(self, render_mock):
        """
        Tests that including tests in a package triggers the rendering of a
        CMakeLists.txt to build the unit tests.
        """
        from packager import main as packager_main

        pkgfile_content = '''
        tests:
            - pid_test.cpp
        '''

        with patch('packager.open', mock_open(read_data=pkgfile_content), create=True):
            packager_main()

        expected_context = {'source': [],
                            'target': {'arm': [], 'x86': []},
                            'tests': ['./pid_test.cpp'],
                            'include_directories': ['dependencies/']
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


if __name__ == "__main__":
    unittest.main()

