# CSELv2.1 Developer Guide
## Filestructure summary
### src
Contains all python files essential to scoring engine functionality.

### useful_scripts
Contains extra scripts you can use to aid development.

### setup
Contains all files essential to setting up the proper binaries, dependencies, and folder structure.

#### build.py
Builds the files as binaries.

- Removes previous build artifacts with clean_build().
- Checks for tktinter, lsb-release, and pip and installs them automatically.
- Parses through requirements.txt and uses pip to install dependencies.
- Compiles binaries for configurator.py and scoring_engine.py

*Note: Virtual Environments should be installed for cleaner build and isolation.*

### service_setup.py
Sets up scoring_engine binary from dist/ as a service via symlink located in: **/usr/local/bin/scoring_engine_DO_NOT_TOUCH**

- Set the service to run on startup and reload using systemd(systemctl is the cli). Name: **scoring_engine.service**
- Sets up assets in **/etc/CYBERPATRIOT_DO_NOT_REMOVE**
- Optionally runs both binaries.

## Functionality

### configurator.py
Main job is to set and send configurations for the scoring engine to **db_handler** to persist and manage.

- **vulnerability_template** is fed into the db_handler, so any changes require a complete database recreation by deleting the old database located in the **/etc/CYBERPATRIOT/** directory and then running the configurator again.
- Tkinter is the main package that is responsible for creating many of the widgets, buttons, etc in the ui.
- *commit* will restart the scoring engine, comment out the line and stop the service *scoring_engine* for development purposes and re-enable after testing.

### db_handler.py
Maintains persistence for the scoring engine to check configurations from.

### scoring_engine.py

## Adding Dependencies
In order for **build.py** to recognize new dependencies, make sure the new requirements are installable via pip, and add them to **requirements.txt** using format:
    
    # Name of Dependency
    dependency>=x.x.x

## Updating Distribution Compatibility

For linux distributions:
- Build.py(Need to update *install_tkinter()* for untested distributions)

## Development Tips

- When developing, instead of compiling the files into binaries and services, just run **sudo .venv/bin/python3.12(or latest version) src/configurator.py(or scoring_engine.py)
- Test workflow: Open configurator, add a configuration for the feature you are testing, run or ensure scoring_engine.py is running, test for all edge cases.