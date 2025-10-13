import unittest
from droidbuilder.utils.dependencies import get_explicit_dependencies

class TestDependencies(unittest.TestCase):

    def test_get_explicit_dependencies(self):
        conf = {
            "app": {
                "dependency": {
                    "runtime_packages": ["package_a", "package_b"],
                    "buildtime_packages": ["lib_x", "lib_y"]
                },
                "dependency_mapping": {
                    "lib_x": "http://example.com/lib_x.tar.gz"
                }
            }
        }
        runtime_packages, buildtime_packages, dependency_mapping = get_explicit_dependencies(conf)

        self.assertEqual(runtime_packages, ["package_a", "package_b"])
        self.assertEqual(buildtime_packages, ["lib_x", "lib_y"])
        self.assertEqual(dependency_mapping, {"lib_x": "http://example.com/lib_x.tar.gz"})

    def test_get_explicit_dependencies_empty(self):
        conf = {"app": {}}
        runtime_packages, buildtime_packages, dependency_mapping = get_explicit_dependencies(conf)

        self.assertEqual(runtime_packages, [])
        self.assertEqual(buildtime_packages, [])
        self.assertEqual(dependency_mapping, {})
