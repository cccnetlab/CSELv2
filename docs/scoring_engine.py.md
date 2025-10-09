# scoring_engine.py Documentation

## Overview
The `scoring_engine.py` module is the core component of the CSEL (Cyberpatriot Scoring Engine: Linux) system. It performs continuous vulnerability assessment and scoring of Linux systems, generating real-time HTML reports and managing the scoring process for Cyberpatriot competitions.

## Purpose
This module serves as the main scoring engine that:
- Continuously monitors system security configurations
- Performs vulnerability assessments across multiple categories
- Generates real-time HTML scoring reports
- Manages point calculation and tracking
- Provides desktop notifications for score changes
- Handles forensic question validation

## File Details

### Imports and Dependencies
```python
import socket
import sys
import traceback
import os
import subprocess
import re
import time
import datetime
from inspect import getfullargspec
from tkinter import messagebox
import pwd, grp
import lsb_release
import platform
import configparser
from pwd import getpwnam
import shutil
```

### Global Variables
- `total_points`: Current total score
- `total_vulnerabilities`: Number of vulnerabilities found
- `prePoints`: Previous point total for comparison
- `scoreIndex`: Path to HTML score report file
- `menuSettings`: Configuration settings from database
- `Vulnerabilities`: Vulnerability definitions and options

## Core Functions

### HTML Report Generation

#### `draw_head()`
**Purpose**: Creates the initial HTML structure for the scoring report

**Parameters**: None

**Returns**: None

**Functionality**:
- Creates HTML file with proper DOCTYPE and styling
- Adds header with logos and title
- Sets up score display placeholders
- Configures refresh interval (60 seconds)

#### `draw_tail()`
**Purpose**: Finalizes the HTML report and sets up desktop access

**Parameters**: None

**Returns**: None

**Functionality**:
- Replaces score placeholders with actual values
- Creates desktop shortcut for easy access
- Sets proper file permissions and ownership
- Adds footer information

#### `write_to_html(message)`
**Purpose**: Appends content to the HTML report

**Parameters**:
- `message` (str): HTML content to append

**Returns**: None

**Functionality**:
- Opens HTML file in append mode
- Writes the message
- Closes file properly

### Scoring Functions

#### `record_hit(name, points)`
**Purpose**: Records a successful vulnerability fix and awards points

**Parameters**:
- `name` (str): Description of the vulnerability fixed
- `points` (int): Points awarded for the fix

**Returns**: None

**Functionality**:
- Adds green success message to HTML report
- Increments total points and vulnerability count
- Updates scoring statistics

#### `record_miss(name)`
**Purpose**: Records a missed vulnerability (only in non-silent mode)

**Parameters**:
- `name` (str): Description of the missed vulnerability

**Returns**: None

**Functionality**:
- Adds red miss message to HTML report (if not in silent mode)
- Used for debugging and training purposes

#### `record_penalty(name, points)`
**Purpose**: Records a penalty for critical system changes

**Parameters**:
- `name` (str): Description of the penalty
- `points` (int): Points deducted

**Returns**: None

**Functionality**:
- Adds red penalty message to HTML report
- Deducts points from total score
- Used for critical system modifications

### System Administration Functions

#### `check_runas()`
**Purpose**: Ensures the scoring engine runs with administrative privileges

**Parameters**: None

**Returns**: None

**Functionality**:
- Checks if running as administrator
- Displays error message if not admin
- Attempts to elevate privileges if needed
- Exits if elevation fails

#### `check_score()`
**Purpose**: Monitors score changes and provides notifications

**Parameters**: None

**Returns**: None

**Functionality**:
- Compares current score with previous score
- Sends desktop notifications for score changes
- Updates database with current scores
- Handles completion notifications

### Vulnerability Assessment Functions

#### Account Management Functions

##### `critical_users(vulnerability)`
**Purpose**: Checks for removal of critical users

**Parameters**:
- `vulnerability` (dict): Vulnerability configuration

**Returns**: None

**Functionality**:
- Gets list of all system users
- Checks if critical users still exist
- Applies penalties for removed critical users

##### `users_manipulation(vulnerability, name)`
**Purpose**: Handles user addition and removal scoring

**Parameters**:
- `vulnerability` (dict): Vulnerability configuration
- `name` (str): Operation type ("Add User" or "Remove User")

**Returns**: None

**Functionality**:
- Checks system groups for user presence
- Awards points for correct user management
- Records misses for incorrect operations

##### `group_manipulation(vulnerability, name)`
**Purpose**: Handles group membership changes

**Parameters**:
- `vulnerability` (dict): Vulnerability configuration
- `name` (str): Operation type

**Returns**: None

**Functionality**:
- Manages admin promotion/demotion
- Handles group membership changes
- Awards points for correct group management

#### Security Policy Functions

##### `local_group_policy(vulnerability, name)`
**Purpose**: Validates local security policy settings

**Parameters**:
- `vulnerability` (dict): Vulnerability configuration
- `name` (str): Policy type to check

**Returns**: None

**Functionality**:
- Checks password age settings (min/max)
- Validates login attempt limits
- Verifies lockout duration settings
- Checks password complexity requirements
- Validates audit settings

##### `disable_SSH_Root_Login(vulnerability)`
**Purpose**: Checks SSH root login configuration

**Parameters**:
- `vulnerability` (dict): Vulnerability configuration

**Returns**: None

**Functionality**:
- Reads SSH configuration file
- Checks PermitRootLogin setting
- Awards points for proper SSH security

#### Firewall Management Functions

##### `firewallVulns(vulnerability, name)`
**Purpose**: Checks firewall status

**Parameters**:
- `vulnerability` (dict): Vulnerability configuration
- `name` (str): Firewall operation type

**Returns**: None

**Functionality**:
- Runs `ufw status` command
- Checks if firewall is active
- Awards points for enabled firewall

##### `portVulns(vulnerability)`
**Purpose**: Checks port accessibility

**Parameters**:
- `vulnerability` (dict): Vulnerability configuration

**Returns**: None

**Functionality**:
- Tests TCP and UDP port connectivity
- Awards points for correct port configurations
- Records misses for incorrect port settings

#### Program Management Functions

##### `programs(vulnerability, name)`
**Purpose**: Manages program installation scoring

**Parameters**:
- `vulnerability` (dict): Vulnerability configuration
- `name` (str): Program operation type

**Returns**: None

**Functionality**:
- Checks for installed programs
- Validates program versions
- Awards points for correct program management

##### `manage_services(vulnerability)`
**Purpose**: Manages service configuration scoring

**Parameters**:
- `vulnerability` (dict): Vulnerability configuration

**Returns**: None

**Functionality**:
- Checks service status and startup mode
- Awards points for correct service configuration
- Records misses for incorrect settings

#### File Management Functions

##### `forensic_question(vulnerability)`
**Purpose**: Validates forensic question answers

**Parameters**:
- `vulnerability` (dict): Vulnerability configuration

**Returns**: None

**Functionality**:
- Reads forensic question files
- Checks for correct answers
- Awards points for correct responses

##### `add_text_to_file(vulnerability)`
**Purpose**: Checks for text additions to files

**Parameters**:
- `vulnerability` (dict): Vulnerability configuration

**Returns**: None

**Functionality**:
- Reads specified files
- Searches for required text additions
- Awards points for correct modifications

##### `remove_text_from_file(vulnerability)`
**Purpose**: Checks for text removal from files

**Parameters**:
- `vulnerability` (dict): Vulnerability configuration

**Returns**: None

**Functionality**:
- Reads specified files
- Verifies text removal
- Awards points for correct modifications

### Utility Functions

#### `check_tcp(host, port)`
**Purpose**: Tests TCP port connectivity

**Parameters**:
- `host` (str): Target hostname or IP
- `port` (int): Port number to test

**Returns**: 
- `bool`: True if port is open, False otherwise

#### `check_udp(host, port)`
**Purpose**: Tests UDP port connectivity

**Parameters**:
- `host` (str): Target hostname or IP
- `port` (int): Port number to test

**Returns**: 
- `bool`: True if port is open, False otherwise

#### `audit_check()`
**Purpose**: Checks if audit service is running

**Parameters**: None

**Returns**: 
- `bool`: True if audit service is active, False otherwise

### Data Loading Functions

#### `load_policy_settings()`
**Purpose**: Loads system policy settings

**Parameters**: None

**Returns**: 
- `list`: List of policy settings from login.defs and PAM

#### `load_programs()`
**Purpose**: Loads list of installed programs

**Parameters**: None

**Returns**: 
- `set`: Set of installed program names

#### `load_services()`
**Purpose**: Loads system service information

**Parameters**: None

**Returns**: 
- `list`: List of service status information

### Main Scoring Categories

#### `account_management(vulnerabilities)`
**Purpose**: Handles all account management scoring

**Parameters**:
- `vulnerabilities` (list): List of account management vulnerabilities

**Returns**: None

**Functionality**:
- Processes user management operations
- Handles group membership changes
- Manages password changes
- Tracks critical user removals

#### `local_policies(vulnerabilities)`
**Purpose**: Handles local security policy scoring

**Parameters**:
- `vulnerabilities` (list): List of policy vulnerabilities

**Returns**: None

**Functionality**:
- Validates password policies
- Checks login restrictions
- Verifies audit settings
- Manages SSH configurations

#### `program_management(vulnerabilities)`
**Purpose**: Handles program and service management scoring

**Parameters**:
- `vulnerabilities` (list): List of program vulnerabilities

**Returns**: None

**Functionality**:
- Manages program installation/removal
- Handles service configuration
- Tracks critical program changes
- Validates program versions

#### `file_management(vulnerabilities)`
**Purpose**: Handles file system scoring

**Parameters**:
- `vulnerabilities` (list): List of file vulnerabilities

**Returns**: None

**Functionality**:
- Manages forensic questions
- Handles file modifications
- Checks file permissions
- Validates startup applications

#### `firewall_management(vulnerabilities)`
**Purpose**: Handles firewall and network scoring

**Parameters**:
- `vulnerabilities` (list): List of firewall vulnerabilities

**Returns**: None

**Functionality**:
- Manages firewall status
- Handles port configurations
- Validates network security

## Main Execution Loop

The scoring engine runs in a continuous loop that:
1. Checks for administrative privileges
2. Loads system data and configurations
3. Generates HTML report header
4. Processes each vulnerability category
5. Handles critical functions
6. Finalizes HTML report
7. Checks for score changes
8. Waits before next iteration

## Error Handling
- Comprehensive try-catch blocks throughout
- Logs errors to `scoring_engine.log`
- Displays user-friendly error messages
- Graceful degradation on failures

## Integration
- Uses database handler for configuration
- Integrates with admin test module
- Provides desktop notifications
- Generates web-accessible reports

## Security Considerations
- Requires administrative privileges
- Validates all system access
- Handles sensitive system information
- Provides secure file operations

## Performance
- Runs continuously with configurable intervals
- Efficient system data loading
- Optimized vulnerability checking
- Minimal resource usage
