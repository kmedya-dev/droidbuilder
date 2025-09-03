from click.testing import CliRunner
from droidbuilder.main import cli
from unittest.mock import patch, MagicMock

def test_list_templates():
    runner = CliRunner()
    mock_logger = MagicMock()
    with patch('droidbuilder.commands.list_templates.logger', mock_logger):
        result = runner.invoke(cli, ['list-templates'])
        assert result.exit_code == 0
        mock_logger.info.assert_any_call('android')
