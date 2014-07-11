#!/usr/bin/env python3
import unittest
from packager import *

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





if __name__ == "__main__":
    unittest.main()

