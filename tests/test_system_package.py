import unittest
from unittest.mock import patch, MagicMock
from droidbuilder.utils.system_package import resolve_dependencies_recursively

class TestSystemPackage(unittest.TestCase):

    @patch('droidbuilder.cli_logger.logger')
    def test_resolve_dependencies_recursively_success(self, mock_logger):
        packages = ["pkg1", "pkg2==1.0"]
        dependency_mapping = {
            "pkg1": "http://example.com/pkg1.tar.gz",
            "pkg2": "http://example.com/pkg2.tar.gz"
        }
        resolved = resolve_dependencies_recursively(packages, dependency_mapping)

        self.assertEqual(set(resolved), {"pkg1", "pkg2"})
        mock_logger.error.assert_not_called()

    @patch('droidbuilder.cli_logger.logger')
    def test_resolve_dependencies_recursively_missing_mapping(self, mock_logger):
        packages = ["pkg1", "pkg2"]
        dependency_mapping = {
            "pkg1": "http://example.com/pkg1.tar.gz"
        }
        resolved = resolve_dependencies_recursively(packages, dependency_mapping)

        self.assertIsNone(resolved) # Should return None on failure
        mock_logger.error.assert_called_once()
        self.assertIn("System package 'pkg2' is not explicitly mapped", mock_logger.error.call_args[0][0])