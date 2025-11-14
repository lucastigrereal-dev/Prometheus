#!/usr/bin/env python3
"""
Install and run Prometheus components inside a Claude Code environment.

- Installs the open-interpreter package via pip.
- Checks if Docker is available; if so, launches an n8n container.
- Uses environment variables for configuration, with sensible defaults.

Run this script with Python 3.
"""
import os
import subprocess
import sys

def run_command(cmd, check=True, ignore_errors=False):
    """Run a shell command and return the completed process."""
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        return result
    except subprocess.CalledProcessError as e:
        if not ignore_errors:
            print(f"Error running command: {cmd}\n{e.stderr.strip()}")
        raise


def ensure_open_interpreter():
    print("Installing open-interpreter ...")
    # Upgrade pip to ensure compatibility
    try:
        run_command("python3 -m pip install --upgrade pip", check=False)
    except Exception:
        pass
    # Install or upgrade open-interpreter
    run_command("python3 -m pip install --upgrade open-interpreter", check=True)
    print("open-interpreter installation completed.")


def docker_available():
    result = subprocess.run("docker --version", shell=True, capture_output=True, text=True)
    return result.returncode == 0


def setup_n8n():
    # Configuration with environment variables or defaults
    user = os.environ.get("N8N_BASIC_AUTH_USER", "prometheus")
    password = os.environ.get("N8N_BASIC_AUTH_PASSWORD", "password123")
    tz = os.environ.get("TZ", "America/Sao_Paulo")

    home = os.path.expanduser("~")
    n8n_data = os.path.join(home, ".n8n")
    os.makedirs(n8n_data, exist_ok=True)

    print("Preparing n8n container ...")
    # Stop and remove existing container if it exists
    run_command("docker stop n8n_instance", check=False, ignore_errors=True)
    run_command("docker rm n8n_instance", check=False, ignore_errors=True)

    # Start new n8n container
    cmd = (
        f"docker run -d --name n8n_instance "
        f"-p 5678:5678 "
        f"-v '{n8n_data}':/home/node/.n8n "
        f"-e N8N_BASIC_AUTH_USER='{user}' "
        f"-e N8N_BASIC_AUTH_PASSWORD='{password}' "
        f"-e TZ='{tz}' "
        f"n8nio/n8n:latest"
    )
    run_command(cmd)
    print(f"n8n is running on http://localhost:5678 with username '{user}' and password '{password}'.")


def main():
    ensure_open_interpreter()

    if docker_available():
        setup_n8n()
    else:
        print("Docker is not installed or not available in PATH. Skipping n8n setup.")
        print("Please install Docker to enable the n8n automation server.")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print("\nAn unexpected error occurred:\n", err)
        sys.exit(1)
