#!/usr/bin/env python3
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

    @patch("packager.clone")
    def test_no_depencendy_no_clone(self, clone_mock):
        """
        Checks that a package without dependencies will not create any git clone.
        """
        package = {} # no dependencies
        with patch("os.path.exists", Mock(return_value=False)):
            download_dependencies(package)

        self.assertEqual([], clone_mock.call_args_list)

    @patch('os.path.exists')
    @patch('packager.open_package')
    @patch("packager.clone")
    def test_dependency_already_there(self, clone, open_package, exists):
        """
        Checks that if a package is already downloaded we don't download it
        again.
        """
        open_package.return_value = {}
        exists.return_value = True

        package = {"depends":["pid"]}
        download_dependencies(package)

        self.assertEqual([], clone.call_args_list)

    @patch('os.path.exists')
    @patch('packager.open_package')
    @patch('packager.clone')
    def test_dependency_download_single_level(self, clone, open_package, exists):
        """
        Checks that we correctly download a needed dependency.
        """
        open_package.return_value = {}
        exists.return_value = False # not yet downloaded

        package = {"depends":["pid"]}
        download_dependencies(package)

        clone.assert_called_with('https://github.com/cvra/pid', 'dependencies/pid')

    @patch('os.path.exists')
    @patch('packager.open_package')
    @patch('packager.clone')
    def test_dependency_has_a_dependency_itself(self, clone, open_package, exists):
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
        download_dependencies(package)

        clone.assert_any_call('https://github.com/cvra/pid', 'dependencies/pid')
        clone.assert_any_call('https://github.com/cvra/test-runner', 'dependencies/test-runner')




if __name__ == "__main__":
    unittest.main()

