# admin_test.py Documentation

## Overview
The `admin_test.py` module provides cross-platform administrative privilege checking and elevation functionality for the CSEL scoring engine. It ensures that the scoring engine runs with the necessary permissions to perform system-level operations required for vulnerability assessment.

## Purpose
This module handles:
- Detection of current user's administrative privileges
- Automatic elevation of privileges when needed
- Cross-platform compatibility (Windows and POSIX systems)
- Error handling for privilege escalation failures

## File Details

### Imports and Dependencies
```python
import os
import sys
import traceback
import types
```

### Functions

#### `isUserAdmin()`
**Purpose**: Checks if the current user has administrative privileges

**Parameters**: None

**Returns**: 
- `bool`: True if user has admin privileges, False otherwise

**Platform Support**:
- **Windows**: Uses `ctypes.windll.shell32.IsUserAnAdmin()` (requires Windows XP SP2+)
- **POSIX (Linux/Unix)**: Checks if `os.getuid() == 0` (root user)
- **Other**: Raises `RuntimeError` for unsupported operating systems

**Error Handling**:
- Catches exceptions on Windows and assumes non-admin status
- Prints traceback for debugging purposes

**Usage Example**:
```python
if not admin_test.isUserAdmin():
    print("Administrator access required")
    sys.exit(1)
```

#### `runAsAdmin(cmdLine=None, wait=True)`
**Purpose**: Elevates the current process to run with administrative privileges

**Parameters**:
- `cmdLine` (list, optional): Command line arguments to run. Defaults to current script with arguments
- `wait` (bool): Whether to wait for the elevated process to complete. Defaults to True

**Returns**:
- `int` or `None`: Exit code of the elevated process (if wait=True), None otherwise

**Platform Support**:
- **Windows Only**: Uses Windows API for privilege elevation
- **Other Platforms**: Raises `RuntimeError`

**Implementation Details**:
- Uses `ShellExecuteEx` with `runas` verb to trigger UAC elevation prompt
- Handles process creation and monitoring
- Supports both synchronous and asynchronous execution

**Error Handling**:
- Validates command line parameter types
- Handles Windows API errors gracefully

**Usage Example**:
```python
if not admin_test.isUserAdmin():
    exit_code = admin_test.runAsAdmin()
    sys.exit(exit_code)
```

## Key Features

### Cross-Platform Support
- **Windows**: Full UAC integration with proper elevation prompts
- **Linux/Unix**: Root privilege detection using standard POSIX methods
- **Error Handling**: Graceful fallback for unsupported platforms

### Security Considerations
- Uses Windows security APIs properly
- Handles privilege escalation securely
- Provides clear error messages for debugging

### Integration
- Designed to be imported and used by other modules
- Provides simple boolean check for privilege status
- Automatic elevation when needed

## Usage in CSEL Context

### Scoring Engine Integration
The scoring engine uses this module to ensure it has the necessary permissions to:
- Access system files and directories
- Modify system configurations
- Check user accounts and groups
- Monitor system services
- Perform security assessments

### Error Handling
- Graceful degradation when elevation fails
- Clear error messages for troubleshooting
- Proper exit codes for process management

## Dependencies
- **Windows**: `ctypes`, `win32con`, `win32event`, `win32process`, `win32comext.shell`
- **POSIX**: Standard library only (`os` module)

## Limitations
- Windows elevation requires UAC to be enabled
- Some operations may still fail even with elevation due to system policies
- Cross-platform behavior may vary based on system configuration

## Related Files
- Used by `scoring_engine.py` for privilege checking
- Referenced by `configurator.py` for admin requirements
- Part of the core security infrastructure of CSEL
