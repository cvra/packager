import unittest
from packager import *

try:
    from unittest.mock import *
except ImportError:
    # unittest.mock is only available in python >= 3.3
    from mock import *

class OpenPackageTestCase(unittest.TestCase):
    package_content = """
    source:
        - pid.c
        - pidconfig.c
    """
    expected = {"source":['pid.c', 'pidconfig.c']}

    def test_load_simple_package(self):
        """
        Tests that loading a package given its simple description (name string)
        works as expected.
        """
        with patch('packager.open', mock_open(read_data=self.package_content), create=True) as m:
            package = open_package('pid')
            m.assert_called_with('dependencies/pid/package.yml')

        self.assertEqual(self.expected, package)


    def test_load_filemap(self):
        """
        Checks that the filemap is respected.
        """

        with patch('packager.open', mock_open(read_data=self.package_content), create=True) as m:
            package = open_package('pid', {'pid':'foo'})
            m.assert_called_with('foo/pid/package.yml')

        expected = {"source":['pid.c', 'pidconfig.c']}
        self.assertEqual(self.expected, package)

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

class DependencyLocationBuilderTestCase(unittest.TestCase):

    def test_can_create_empty_dict(self):
        """
        This test checks if the default value for the location map is correctly
        defined to DEPENDENCIES_DIR.
        """
        locations = create_dependency_location_map({})
        self.assertEqual(locations['foo'], DEPENDENCIES_DIR)

    def test_can_create_from_simple_dict(self):
        """
        Checks if we can create the dictionnary from a map with only one item.
        """
        locations = create_dependency_location_map({'foo':['bar']})
        self.assertEqual('foo', locations['bar'])

    def test_can_create_from_complex_dict(self):
        """
        Checks if we can create a module map from a more complex description.
        """
        original_map = {}
        original_map['control'] = ['pid', 'odometry']
        original_map['foo'] = ['bar']

        locations = create_dependency_location_map(original_map)

        self.assertEqual("control", locations["pid"])
        self.assertEqual("control", locations["odometry"])
        self.assertEqual("foo", locations["bar"])
