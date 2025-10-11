import subprocess
import shlex

def run_shell_command(command_string):
    """
    Executes a shell command and returns its output, error, and exit code.

    Args:
        command_string: The command to execute as a string.

    Returns:
        A tuple containing:
        - stdout (str): The standard output of the command.
        - stderr (str): The standard error of the command.
        - exit_code (int): The exit code of the command.
    """
    try:
        # Use shlex.split to handle quoted arguments correctly and prevent
        # shell injection vulnerabilities.
        args = shlex.split(command_string)

        # Execute the command using subprocess.run
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,  # Capture stdout/stderr as strings
            check=False # Do not raise an exception for non-zero exit codes
        )

        return result.stdout, result.stderr, result.returncode

    except Exception as e:
        # Handle exceptions that might occur during command execution
        return "", str(e), -1

# --- Example Usage ---

# 1. Successful command
print("--- Running a successful command ---")
stdout, stderr, exit_code = run_shell_command("ls -l")
if exit_code == 0:
    print("Command executed successfully.")
    print("Exit Code:", exit_code)
    print("STDOUT:")
    print(stdout)
else:
    print("Command failed.")
    print("Exit Code:", exit_code)
    print("STDERR:")
    print(stderr)

print("\n" + "="*20 + "\n")

# 2. Command that produces an error
print("--- Running a command that fails ---")
stdout, stderr, exit_code = run_shell_command("ls non_existent_directory")
if exit_code == 0:
    print("Command executed successfully.")
    print("Exit Code:", exit_code)
    print("STDOUT:")
    print(stdout)
else:
    print("Command failed.")
    print("Exit Code:", exit_code)
    print("STDERR:")
    print(stderr)
