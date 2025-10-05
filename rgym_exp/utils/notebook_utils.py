"""
Utility functions for Jupyter/Colab notebooks.
"""

import sys
import subprocess
from typing import List, Optional


def run_with_live_output(
    command: List[str],
    cwd: Optional[str] = None,
    env: Optional[dict] = None
) -> int:
    """
    Run a subprocess command with live output in Jupyter/Colab notebooks.

    Args:
        command: Command and arguments as a list
        cwd: Working directory (optional)
        env: Environment variables (optional)

    Returns:
        Exit code of the process

    Example:
        >>> run_with_live_output(['python', '-m', 'rgym_exp.runner.swarm_launcher'])
    """
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Merge stderr into stdout
        universal_newlines=True,
        bufsize=1,  # Line buffered
        cwd=cwd,
        env=env
    )

    try:
        # Read output line by line and print immediately
        for line in iter(process.stdout.readline, ''):
            if line:
                print(line, end='', flush=True)

        # Wait for process to complete
        process.wait()

        return process.returncode

    except KeyboardInterrupt:
        print("\n" + "="*60)
        print("⚠️ Process interrupted by user")
        print("="*60)
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        return -1

    finally:
        if process.stdout:
            process.stdout.close()


def install_package_with_live_output(package: str):
    """
    Install a package with live output.

    Args:
        package: Package name or pip install string

    Example:
        >>> install_package_with_live_output('numpy>=1.20')
    """
    print(f"Installing {package}...")
    return run_with_live_output([sys.executable, '-m', 'pip', 'install', package])
