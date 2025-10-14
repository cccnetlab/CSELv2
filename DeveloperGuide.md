# CSELv2.1 Developer Guide
## Adding Dependencies
In order for **build.py** to recognize new dependencies, make sure the new requirements are installable via pip, and add them to **requirements.txt** using format:
    
    # Name of Dependency
    dependency>=x.x.x

## Updating Distribution Compatibility

For linux distributions:
- Build.py(Need to update *install_tkinter()* for untested distributions)