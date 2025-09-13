import os
import shutil
from click.testing import CliRunner
from droidbuilder.main import cli

def test_clean_command():
    """Test that the clean command removes specified directories."""
    runner = CliRunner()

    # Create dummy directories and files
    dirs_to_create = ["build", "dist", ".droidbuilder", ".pytest_cache", ".ruff_cache", "droidbuilder.egg-info"]
    for d in dirs_to_create:
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "dummy_file.txt"), "w") as f:
            f.write("dummy content")

    os.makedirs("droidbuilder/__pycache__", exist_ok=True)
    with open("droidbuilder/__pycache__/dummy_file.txt", "w") as f:
        f.write("dummy content")

    # Run the clean command
    result = runner.invoke(cli, ["clean"])

    # Assert that the command ran successfully
    assert result.exit_code == 0

    # Assert that the directories have been removed
    for d in dirs_to_create:
        assert not os.path.exists(d)

    assert not os.path.exists("droidbuilder/__pycache__")
