from click.testing import CliRunner
from droidbuilder.main import cli
from unittest.mock import patch, MagicMock, mock_open

@patch("subprocess.run")
@patch("os.path.exists", return_value=True)
@patch("droidbuilder.installer._get_sdk_manager", return_value="/mock/sdkmanager")
def test_search_packages_no_query(mock_get_sdk_manager, mock_exists, mock_run):
    runner = CliRunner()
    mock_logger = MagicMock()

    # Mock the subprocess result
    mock_result = MagicMock()
    mock_result.stdout = "package1\npackage2\npackage3"
    mock_run.return_value = mock_result

    with patch('droidbuilder.commands.search_packages.logger', mock_logger):
        result = runner.invoke(cli, ['search-packages'])
        assert result.exit_code == 0
        mock_logger.info.assert_any_call("Available packages:")
        mock_logger.info.assert_any_call("package1")
        mock_logger.info.assert_any_call("package2")
        mock_logger.info.assert_any_call("package3")

@patch("subprocess.run")
@patch("os.path.exists", return_value=True)
@patch("droidbuilder.installer._get_sdk_manager", return_value="/mock/sdkmanager")
def test_search_packages_with_query(mock_get_sdk_manager, mock_exists, mock_run):
    runner = CliRunner()
    mock_logger = MagicMock()

    # Mock the subprocess result
    mock_result = MagicMock()
    mock_result.stdout = "package1\npackage2\nother-package"
    mock_run.return_value = mock_result

    with patch('droidbuilder.commands.search_packages.logger', mock_logger):
        result = runner.invoke(cli, ['search-packages', 'package'])
        assert result.exit_code == 0
        mock_logger.info.assert_any_call("Filtering results for 'package':")
        mock_logger.info.assert_any_call("package1")
        mock_logger.info.assert_any_call("package2")
        mock_logger.info.assert_any_call("other-package")

