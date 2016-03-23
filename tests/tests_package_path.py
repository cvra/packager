import unittest
from cvra_packager.packager import *

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

    def test_path_for_package_with_a_map(self):
        """
        Checks that the module path is really taken from the dictionnary.
        """
        package = "pid"
        m = {"pid":"control"}
        self.assertEqual("control/pid", path_for_package(package, m))


