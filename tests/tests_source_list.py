import unittest
from cvra_packager.packager import *
try:
    from unittest.mock import *
except ImportError:
    # unittest.mock is only available in python >= 3.3
    from mock import *

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

    @patch('cvra_packager.packager.open_package')
    def test_source_in_filemap(self, open_package_mock):
        """
        Tests that we can create a package with dependencies in a specified folder.
        """
        package = {'sources':['application.c'],'depends':['pid']}
        pid_package = {'sources':['pid.c']}
        open_package_mock.return_value = pid_package

        filemap = {'pid':'foo'}

        result = generate_source_list(package, 'sources', filemap=filemap)

        self.assertEqual(['./application.c', 'foo/pid/pid.c'], result)

        # Checks that the opened file is foo/pid/package.yml
        open_package_mock.assert_called_with('pid', filemap)

    @patch('cvra_packager.packager.open_package')
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

    @patch('cvra_packager.packager.open_package')
    def test_skip_package_if_no_yml(self, open_package_mock):
        """
        Checks that a package file without any yml file is simply skipped.
        """

        # Simple package which will try to open a dependency package.yml
        package = {'sources':['application.c'],'depends':['pid']}

        # Simulates a non existing package.yml
        open_package_mock.side_effect = IOError()

        result = generate_source_list(package, 'sources')

        self.assertEqual(['./application.c'], result)

    def test_source_dict_contains_correct_categories(self):
        """
        Tests that the source dictionnary contains all needed categories even
        when the package doesn't.
        """
        result = generate_source_dict({})
        self.assertIn('source', result)
        self.assertIn('tests', result)
        self.assertIn('target', result)
        self.assertIn('include_directories', result)

    def test_source_target_are_discovered(self):
        """
        Tests that the target categories are detected.
        """
        result = generate_source_dict({'target.x86':[], 'target.linux':[]})
        self.assertIn('x86', result['target'])
        self.assertIn('linux', result['target'])

    def test_source_target_is_correct(self):
        """
        Checks that the target.* fields are correctly read (issue #12)
        """
        result = generate_source_dict({'target.x86':['main.c']})
        self.assertEqual(['./main.c'], result['target']['x86'])

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


    @patch('cvra_packager.packager.open_package')
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

    @patch('cvra_packager.packager.open_package')
    def test_include_directory_for_tests(self, open_package_mock):
        """
        Tests that the include directories for tests are included as well.
        """
        package = {'sources':['application.c'],'depends':['pid']}
        pid_package = {'sources':['pid.c'], 'include_directories.test':['poney']}
        open_package_mock.return_value = pid_package

        result = generate_source_dict(package)
        expected = [os.path.join(DEPENDENCIES_DIR, 'pid', 'poney')]

        self.assertEqual(result['include_directories'].test, expected)
