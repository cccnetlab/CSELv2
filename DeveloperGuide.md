# CSELv2.1 Developer Guide
## Filestructure summary
### src
Contains all python files essential to scoring enginer functionality.

### setup
Contains all files essential to setting up the proper binaries, dependencies, and folder structure.

#### build.py

- Removes previous build artifacts with clean_build().
- Checks for tktinter, lsb-release, and pip and installs them automatically.
- Parses through requirements.txt and uses pip to install dependencies.
- Compiles binaries for configurator.py and scoring_engine.py

*Note: Virtual Environments should be installed for cleaner build and isolation.*

## Adding Dependencies
In order for **build.py** to recognize new dependencies, make sure the new requirements are installable via pip, and add them to **requirements.txt** using format:
    
    # Name of Dependency
    dependency>=x.x.x

## Updating Distribution Compatibility

For linux distributions:
- Build.py(Need to update *install_tkinter()* for untested distributions)