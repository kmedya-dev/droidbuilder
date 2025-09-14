from click.testing import CliRunner
from droidbuilder.main import cli
from unittest.mock import patch, MagicMock


@patch("droidbuilder.installer.search_tool")
def test_search_command(mock_search_tool):
    runner = CliRunner()
    result = runner.invoke(cli, ["search", "jdk"])
    assert result.exit_code == 0
    mock_search_tool.assert_called_once_with("jdk")