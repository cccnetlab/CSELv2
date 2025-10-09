# configurator.py Documentation

## Overview
The `configurator.py` module provides a comprehensive graphical user interface for configuring the CSEL (Cyberpatriot Scoring Engine: Linux) system. It allows administrators to set up vulnerability assessments, configure scoring parameters, manage system settings, and generate reports.

## Purpose
This module serves as the main configuration interface that:
- Provides a tabbed GUI for different configuration categories
- Manages vulnerability definitions and scoring parameters
- Handles system settings and preferences
- Generates configuration reports
- Manages the scoring engine deployment

## File Details

### Imports and Dependencies
```python
import os
import subprocess
import sys
import time
import shutil
import tkinter
import traceback
from crontab import CronTab
import pwd, grp, psutil
from tkinter import *
from tkinter import ttk as ttk
from tkinter import filedialog
from tkinter import messagebox
from ttkthemes import ThemedStyle
```

### Global Variables
- `Settings`: Database handler for system settings
- `Categories`: Database handler for vulnerability categories
- `Vulnerabilities`: Database handler for vulnerability options
- `vuln_settings`: Dictionary storing vulnerability configurations
- `themeList`: Available GUI themes

## Vulnerability Template System

### Vulnerability Definitions
The module defines a comprehensive set of vulnerability types organized by category:

#### Account Management Vulnerabilities
- **Critical Users**: Penalizes removal of critical users
- **Add Admin**: Scores elevation of users to administrator
- **Remove Admin**: Scores demotion of administrators
- **Add User**: Scores user creation
- **Remove User**: Scores user deletion
- **User Change Password**: Scores password changes
- **Add User to Group**: Scores group membership additions
- **Remove User from Group**: Scores group membership removals

#### Local Policy Vulnerabilities
- **Minimum Password Age**: Scores password age settings (30-60 days)
- **Maximum Password Age**: Scores password age settings (60-90 days)
- **Minimum Password Length**: Scores password length (10-20 characters)
- **Maximum Login Tries**: Scores login attempt limits (5-10)
- **Lockout Duration**: Scores lockout duration (30 minutes)
- **Lockout Reset Duration**: Scores lockout reset (30 minutes)
- **Password History**: Scores password history (5-10)
- **Audit**: Scores audit policy enablement
- **Disable SSH Root Login**: Scores SSH root login disablement
- **Check Kernel**: Scores kernel updates

#### Program Management Vulnerabilities
- **Good Program**: Scores program installation
- **Bad Program**: Scores program removal
- **Update Program**: Scores program updates
- **Critical Services**: Penalizes service modifications
- **Services**: Scores service configuration changes
- **Critical Programs**: Penalizes program removal
- **Update Check Period**: Scores update check configuration

#### File Management Vulnerabilities
- **Forensic**: Scores forensic question answers
- **Bad File**: Scores file deletion
- **Check Hosts**: Scores hosts file clearing
- **Add Text to File**: Scores text additions to files
- **Remove Text From File**: Scores text removal from files
- **File Permissions**: Scores file permission changes
- **Check Startup**: Scores startup program removal

#### Firewall Management Vulnerabilities
- **Turn On Firewall**: Scores firewall enablement
- **Check Port Open**: Scores port opening
- **Check Port Closed**: Scores port closing

## GUI Components

### VerticalScrolledFrame Class
**Purpose**: Creates a scrollable frame for long content

**Key Features**:
- Pure Tkinter implementation
- Vertical scrolling only
- Automatic canvas resizing
- Proper scrollbar integration

**Usage**:
```python
class VerticalScrolledFrame(Frame):
    def __init__(self, parent, *args, **kw):
        # Creates canvas and scrollbar
        # Manages scrolling behavior
        # Handles resize events
```

### Config Class (Main Window)
**Purpose**: Main configuration window with tabbed interface

**Key Features**:
- Tabbed interface for different categories
- Theme support with multiple options
- Real-time configuration updates
- Report generation capabilities

**Tabs**:
1. **Main Page**: System settings and preferences
2. **Account Management**: User and group management
3. **Local Policy**: Security policy settings
4. **Program Management**: Program and service management
5. **File Management**: File system operations
6. **Firewall Management**: Network security
7. **Report**: Configuration reporting

## Core Functions

### `add_option(frame, entry, name, row, return_frame)`
**Purpose**: Adds vulnerability options to configuration pages

**Parameters**:
- `frame`: Parent frame for the option
- `entry`: Vulnerability configuration data
- `name`: Vulnerability name
- `row`: Grid row position
- `return_frame`: Return frame reference

**Functionality**:
- Creates checkbox for enabling/disabling
- Adds description label
- Creates modify button for complex options
- Adds points input field
- Separates options with horizontal lines

### `modify_settings(name, entry, packing)`
**Purpose**: Opens detailed configuration for complex vulnerabilities

**Parameters**:
- `name`: Vulnerability name
- `entry`: Vulnerability configuration
- `packing`: Parent frame reference

**Functionality**:
- Creates scrollable modification interface
- Provides add/remove functionality
- Handles different input types
- Saves changes to database

### `load_modify_settings(frame, entry, name, idx)`
**Purpose**: Loads individual vulnerability settings for modification

**Parameters**:
- `frame`: Parent frame
- `entry`: Vulnerability entry
- `name`: Vulnerability name
- `idx`: Entry index

**Functionality**:
- Creates input fields based on data types
- Handles file path selection
- Provides dropdowns for system data
- Manages remove functionality

### `add_row(frame, entry, name)`
**Purpose**: Adds new vulnerability entries

**Parameters**:
- `frame`: Parent frame
- `entry`: Vulnerability entry
- `name`: Vulnerability name

**Functionality**:
- Creates new database entry
- Generates input fields
- Handles different data types
- Provides remove functionality

### `remove_row(entry, idx, widget)`
**Purpose**: Removes vulnerability entries

**Parameters**:
- `entry`: Vulnerability entry
- `idx`: Entry index
- `widget`: Widget to destroy

**Functionality**:
- Removes from database
- Destroys GUI elements
- Updates configuration

## System Integration Functions

### `commit_config()`
**Purpose**: Deploys configuration and starts scoring engine

**Functionality**:
1. **Save Configuration**: Saves all settings to database
2. **Create Directories**: Sets up system directories
3. **Copy Files**: Deploys scoring engine and assets
4. **Set Permissions**: Configures file permissions
5. **Setup Cron**: Creates scheduled tasks
6. **Start Engine**: Launches scoring engine

**Directory Structure**:
- `/etc/CYBERPATRIOT/`: Configuration directory
- `/var/www/CYBERPATRIOT/`: Web assets directory

**Cron Jobs**:
- Every minute: `* * * * *`
- On reboot: `@reboot`

### `save_config()`
**Purpose**: Saves configuration to database

**Functionality**:
- Updates desktop path
- Creates forensic questions
- Calculates point totals
- Saves to database
- Cleans up resources

### `tally()`
**Purpose**: Calculates total points and vulnerabilities

**Functionality**:
- Counts enabled vulnerabilities
- Calculates point totals
- Updates display values
- Handles complex scoring

## Utility Functions

### `get_service_list()`
**Purpose**: Gets list of system services

**Returns**: List of service names

**Implementation**:
```python
def get_service_list():
    command = "systemctl list-unit-files --type=service --no-pager --plain --no-legend"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    services = []
    for line in result.stdout.splitlines():
        service_name = line.split()[0]
        services.append(service_name)
    return services
```

### `get_user_list()`
**Purpose**: Gets list of system users

**Returns**: List of usernames

### `get_group_list()`
**Purpose**: Gets list of system groups

**Returns**: List of group names

### `set_file_or_directory(var, switch, mode)`
**Purpose**: Handles file/directory selection

**Parameters**:
- `var`: Variable to store path
- `switch`: Directory/file mode
- `mode`: Operation mode

**Functionality**:
- Opens file/directory dialog
- Sets path variable
- Handles permissions for file operations

## Report Generation

### `generate_report(frame)`
**Purpose**: Generates configuration report

**Parameters**:
- `frame`: Frame to display report

**Functionality**:
- Saves current configuration
- Clears existing report
- Creates category-based report
- Shows enabled vulnerabilities
- Displays configuration details

### `generate_export(extension)`
**Purpose**: Exports configuration to HTML

**Parameters**:
- `extension`: File extension for export

**Functionality**:
- Creates HTML report
- Includes all configuration details
- Provides tabbed interface
- Saves to selected location

## Theme Management

### Available Themes
- **aquativo**: Modern blue theme
- **black**: Dark theme
- **clearlooks**: Clean look theme
- **elegance**: Elegant theme
- **equilux**: Dark elegant theme
- **keramik**: Ceramic theme
- **plastik**: Plastic theme
- **ubuntu**: Ubuntu-style theme

### Theme Configuration
Each theme includes custom settings for:
- Background colors
- Tab configurations
- Label styling
- Entry field appearance
- Button styling

## Error Handling

### `show_error(self, *args)`
**Purpose**: Displays error messages

**Functionality**:
- Formats traceback information
- Provides user-friendly messages
- Handles specific error types
- Shows error dialogs

## Security Features

### Administrative Privileges
- Checks for root access
- Requires sudo privileges
- Validates environment variables
- Prevents unauthorized access

### File Operations
- Proper permission setting
- Secure file copying
- Ownership management
- Access control

## Integration Points

### Database Integration
- Uses `db_handler` for data persistence
- Manages vulnerability configurations
- Handles system settings
- Provides data validation

### System Integration
- Manages cron jobs
- Handles process management
- Configures system services
- Manages file permissions

## Performance Considerations

### Lazy Loading
- Loads data only when needed
- Efficient memory usage
- Responsive interface
- Minimal resource consumption

### Data Management
- Efficient database operations
- Proper resource cleanup
- Optimized queries
- Memory management

## Usage Workflow

1. **Launch Configurator**: Start with administrative privileges
2. **Configure Settings**: Set up system preferences
3. **Define Vulnerabilities**: Configure scoring parameters
4. **Test Configuration**: Generate reports
5. **Deploy System**: Commit configuration
6. **Monitor Results**: View scoring reports

## Dependencies
- **Tkinter**: GUI framework
- **ttkthemes**: Theme support
- **crontab**: Cron job management
- **psutil**: Process management
- **pwd/grp**: User/group management
- **subprocess**: System command execution
- **db_handler**: Database operations

## Related Files
- **db_handler.py**: Database management
- **scoring_engine.py**: Scoring engine
- **uniqueID.py**: User credential collection
- **admin_test.py**: Privilege management
