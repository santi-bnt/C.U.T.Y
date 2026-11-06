# Setup Helpers

Run dev_setup.ps1 explicitly from Windows to create/reuse raspberry/.venv and install raspberry/requirements.txt (the Raspberry project plus existing test dependencies). Run bash raspberry/scripts/setup_raspberry.sh explicitly on Linux/Pi for the same layout. Both helpers resolve paths from their own location and can be called from any working directory.

Application code and entry points live inside raspberry/. There are no root launcher shims or root requirements.txt. Run python -m cuty through the installed project in its virtual environment; the setup helper does not depend on a root cuty.py. Existing virtual environments are not moved or deleted by this reorganization.

These helpers do not configure hardware, generate firmware, copy secrets, enable systemd, or start the app. They require an existing Python installation and may download the project's existing dependencies.
