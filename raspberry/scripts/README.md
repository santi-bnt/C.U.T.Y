# Setup Helpers

Run dev_setup.ps1 explicitly from Windows to create/reuse root .venv and install the Raspberry project plus existing test dependencies. Run bash raspberry/scripts/setup_raspberry.sh explicitly on Linux/Pi to create/reuse raspberry/.venv and install raspberry/requirements.txt.

These helpers do not configure hardware, generate firmware, copy secrets, enable systemd, or start the app. They require an existing Python installation and may download the project's existing dependencies.
