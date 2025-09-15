import unittest
from droidbuilder.utils.dependencies import get_explicit_dependencies

class TestDependencies(unittest.TestCase):

    def test_get_explicit_dependencies(self):
        conf = {
            "project": {
                "requirements": {
                    "python_packages": ["package_a", "package_b"],
                    "system_packages": ["lib_x", "lib_y"]
                },
                "dependency_mapping": {
                    "lib_x": "http://example.com/lib_x.tar.gz"
                },
                "python_dependency_mapping": {
                    "package_a": "http://example.com/package_a.zip"
                }
            }
        }
        python_packages, system_packages, dependency_mapping, python_dependency_mapping = get_explicit_dependencies(conf)

        self.assertEqual(python_packages, ["package_a", "package_b"])
        self.assertEqual(system_packages, ["lib_x", "lib_y"])
        self.assertEqual(dependency_mapping, {"lib_x": "http://example.com/lib_x.tar.gz"})
        self.assertEqual(python_dependency_mapping, {"package_a": "http://example.com/package_a.zip"})

    def test_get_explicit_dependencies_empty(self):
        conf = {"project": {}}
        python_packages, system_packages, dependency_mapping, python_dependency_mapping = get_explicit_dependencies(conf)

        self.assertEqual(python_packages, [])
        self.assertEqual(system_packages, [])
        self.assertEqual(dependency_mapping, {})
        self.assertEqual(python_dependency_mapping, {})
