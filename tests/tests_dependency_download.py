import unittest
from packager import *

try:
    from unittest.mock import *
except ImportError:
    # unittest.mock is only available in python >= 3.3
    from mock import *

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
    def test_cannot_find_package_file_in_dependency(self, open_package, exists):
        """
        Checks that a package where we cannot find a package.yml is simply skipped.
        """

        # Raise IOError when the packager tries to open the package.yml file of
        # PID or poney
        open_package.side_effect = IOError()
        exists.return_value = False # not yet downloaded

        package = {"depends":["pid", "poney"]}
        download_dependencies(package, method=self.clone)
        self.clone.assert_any_call('https://github.com/cvra/pid', 'dependencies/pid')
        self.clone.assert_any_call('https://github.com/cvra/poney', 'dependencies/poney')


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

    @patch('os.path.exists')
    @patch('packager.open_package')
    def test_dependencies_filemap(self, open_package, exists):
        """
        Checks that we can correctly map the downloaded file to the correct
        location.
        """
        open_package.return_value = {}
        exists.return_value = False # not yet downloaded

        package = {"depends":["pid"]}
        m = {'pid':'foo'}

        download_dependencies(package, method=self.clone, filemap=m)

        self.clone.assert_any_call('https://github.com/cvra/pid', 'foo/pid')



