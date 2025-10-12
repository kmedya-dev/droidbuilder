import subprocess
import shlex
from ..cli_logger import logger

def run_shell_command(command, stream_output=False, env=None, input_data=None, cwd=None):
    """
    Executes a shell command, with options for streaming output and providing input.

    Args:
        command (list): The command to execute as a list of strings.
        stream_output (bool): If True, streams the output in real-time.
        env (dict, optional): A dictionary of environment variables.
        input_data (str, optional): Data to be passed to the command's stdin.
        cwd (str, optional): The working directory for the command.

    Returns:
        If stream_output is True, returns a generator that yields output lines.
        If stream_output is False, returns a tuple (stdout, stderr, return_code).
    """
    try:
        if stream_output:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True,
                env=env,
                cwd=cwd
            )

            def _generator():
                for line in process.stdout:
                    yield line
                process.communicate()
            return _generator(), process

        else:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                env=env,
                input=input_data,
                check=False,
                cwd=cwd
            )
            return result.stdout, result.stderr, result.returncode

    except FileNotFoundError as e:
        logger.error(f"Command not found: {e.filename}")
        if stream_output:
            return iter([]), type('obj', (object,), {'returncode': -1})
        else:
            return "", str(e), -1
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        if stream_output:
            return iter([]), type('obj', (object,), {'returncode': -1})
        else:
            return "", str(e), -1
