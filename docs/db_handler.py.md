# db_handler.py Documentation

## Overview
The `db_handler.py` module provides comprehensive database management functionality for the CSEL (Cyberpatriot Scoring Engine: Linux) system. It handles all data persistence, including system settings, vulnerability configurations, and scoring data using SQLAlchemy ORM with SQLite backend.

## Purpose
This module serves as the data layer that:
- Manages database schema and models
- Handles data persistence and retrieval
- Provides configuration management
- Manages vulnerability definitions
- Handles scoring data storage
- Provides data validation and integrity

## File Details

### Imports and Dependencies
```python
import sys, os, subprocess
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as sa
from tkinter import StringVar, IntVar
```

### Database Configuration
- **Database Type**: SQLite
- **Location**: `/etc/CYBERPATRIOT/save_data.db`
- **ORM**: SQLAlchemy
- **Session Management**: Scoped sessions

## Database Models

### SettingsModel
**Purpose**: Stores system-wide configuration settings

**Table Name**: `Settings`

**Fields**:
- `id` (Integer, Primary Key): Unique identifier
- `style` (String, 128 chars): GUI theme selection
- `desktop` (Text): Desktop path for file operations
- `silent_mode` (Boolean): Silent mode toggle
- `server_mode` (Boolean): Server mode toggle
- `server_name` (String, 255 chars): FTP server name
- `server_user` (String, 255 chars): FTP username
- `server_pass` (String, 128 chars): FTP password
- `tally_points` (Integer): Total possible points
- `tally_vuln` (Integer): Total vulnerabilities
- `current_points` (Integer): Current score
- `current_vuln` (Integer): Current vulnerability count

### CategoryModels
**Purpose**: Stores vulnerability category definitions

**Table Name**: `Vulnerability Categories`

**Fields**:
- `id` (Integer, Primary Key): Unique identifier
- `name` (String, 128 chars): Category name (unique)
- `description` (Text): Category description

**Predefined Categories**:
- **Account Management**: User and group management
- **Local Policy**: Security policy settings
- **Program Management**: Program and service management
- **File Management**: File system operations
- **Firewall Management**: Network security

### VulnerabilityTemplateModel
**Purpose**: Stores vulnerability template definitions

**Table Name**: `Vulnerability Template`

**Fields**:
- `id` (Integer, Primary Key): Unique identifier
- `name` (String, 128 chars): Vulnerability name (unique)
- `category` (Integer, Foreign Key): Category ID reference
- `definition` (Text): Vulnerability definition
- `description` (Text): Detailed description
- `checks` (Text): Required check parameters

## Core Classes

### Settings Class
**Purpose**: Manages system settings and configuration

#### `__init__(self)`
**Functionality**:
- Initializes database connection
- Creates default settings if none exist
- Loads existing settings from database

#### `get_settings(self, config=True)`
**Purpose**: Retrieves system settings

**Parameters**:
- `config` (bool): Whether to return Tkinter variables

**Returns**:
- **config=True**: Dictionary of Tkinter StringVar/IntVar objects
- **config=False**: Dictionary of raw values

**Usage**:
```python
settings = Settings()
config_vars = settings.get_settings(True)  # For GUI
raw_values = settings.get_settings(False)  # For processing
```

#### `update_table(self, entry)`
**Purpose**: Updates system settings

**Parameters**:
- `entry` (dict): Dictionary of setting values

**Functionality**:
- Updates all setting fields
- Handles type conversions
- Commits changes to database

#### `update_score(self, entry)`
**Purpose**: Updates current scoring data

**Parameters**:
- `entry` (dict): Dictionary with current points and vulnerabilities

**Functionality**:
- Updates current score tracking
- Maintains scoring history
- Enables score monitoring

### Categories Class
**Purpose**: Manages vulnerability categories

#### `__init__(self)`
**Functionality**:
- Initializes category system
- Creates default categories if none exist
- Loads existing categories from database

**Predefined Categories**:
```python
categories = {
    "Account Management": "User and group management scoring",
    "Local Policy": "Security policy scoring",
    "Program Management": "Program and service scoring",
    "File Management": "File system operation scoring",
    "Firewall Management": "Network security scoring"
}
```

#### `get_categories(self)`
**Purpose**: Retrieves all categories

**Returns**: SQLAlchemy query result with all categories

### OptionTables Class
**Purpose**: Manages vulnerability configurations and scoring options

#### `__init__(self, vulnerability_templates=None)`
**Purpose**: Initializes vulnerability system

**Parameters**:
- `vulnerability_templates` (dict): Template definitions

**Functionality**:
- Creates vulnerability templates
- Initializes option tables
- Sets up database schema

#### `initialize_option_table(self)`
**Purpose**: Creates dynamic option tables for each vulnerability

**Functionality**:
- Reads vulnerability templates
- Creates database tables dynamically
- Sets up check parameters
- Initializes default entries

#### `get_option_template(self, vulnerability)`
**Purpose**: Gets vulnerability template definition

**Parameters**:
- `vulnerability` (str): Vulnerability name

**Returns**: VulnerabilityTemplateModel object

#### `get_option_template_by_category(self, category)`
**Purpose**: Gets vulnerabilities by category

**Parameters**:
- `category` (int): Category ID

**Returns**: SQLAlchemy query result

#### `get_option_table(self, vulnerability, config=True)`
**Purpose**: Gets vulnerability configuration data

**Parameters**:
- `vulnerability` (str): Vulnerability name
- `config` (bool): Whether to return Tkinter variables

**Returns**:
- **config=True**: Dictionary of Tkinter variables
- **config=False**: Dictionary of raw values

**Data Structure**:
```python
{
    vuln_id: {
        "Enabled": IntVar/Boolean,
        "Points": IntVar/Integer,
        "Checks": {
            "check_name": StringVar/IntVar/String/Integer
        }
    }
}
```

#### `add_to_table(self, vulnerability, **kwargs)`
**Purpose**: Adds new vulnerability entry

**Parameters**:
- `vulnerability` (str): Vulnerability name
- `**kwargs`: Additional parameters

**Returns**: Created vulnerability object

#### `update_table(self, vulnerability, entry)`
**Purpose**: Updates vulnerability configuration

**Parameters**:
- `vulnerability` (str): Vulnerability name
- `entry` (dict): Configuration data

**Functionality**:
- Updates enabled status
- Updates point values
- Updates check parameters
- Commits changes

#### `remove_from_table(self, vulnerability, vuln_id)`
**Purpose**: Removes vulnerability entry

**Parameters**:
- `vulnerability` (str): Vulnerability name
- `vuln_id` (int): Entry ID to remove

**Functionality**:
- Deletes from database
- Commits changes
- Maintains referential integrity

#### `cleanup(self)`
**Purpose**: Cleans up database session

**Functionality**:
- Flushes pending changes
- Maintains session state
- Optimizes performance

## Dynamic Table Creation

### `create_option_table(name, option_categories, option_models)`
**Purpose**: Creates dynamic database tables for vulnerabilities

**Parameters**:
- `name` (str): Table name
- `option_categories` (dict): Field definitions
- `option_models` (dict): Model storage

**Functionality**:
- Creates SQLAlchemy model dynamically
- Defines table schema
- Handles different data types
- Registers with ORM

**Field Types**:
- **Int**: Integer columns
- **Str**: Text columns
- **Enabled**: Boolean for enable/disable
- **Points**: Integer for scoring

**Example**:
```python
attr_dict = {
    "__tablename__": "Add User",
    "id": sa.Column(sa.Integer, primary_key=True),
    "Enabled": sa.Column(sa.Boolean, nullable=False, default=False),
    "Points": sa.Column(sa.Integer, nullable=False, default=0),
    "User Name": sa.Column(sa.Text, default="")
}
```

## Data Management Features

### Type Handling
- **StringVar**: For text input fields
- **IntVar**: For numeric input fields
- **Boolean**: For enable/disable toggles
- **Text**: For long text content

### Validation
- **Required Fields**: Ensures critical data is present
- **Type Checking**: Validates data types
- **Range Validation**: Checks numeric ranges
- **Referential Integrity**: Maintains foreign key relationships

### Session Management
- **Scoped Sessions**: Thread-safe database access
- **Automatic Cleanup**: Proper resource management
- **Transaction Handling**: ACID compliance
- **Connection Pooling**: Efficient resource usage

## Error Handling

### Database Errors
- **Connection Failures**: Graceful error handling
- **Schema Issues**: Automatic table creation
- **Data Validation**: Input sanitization
- **Transaction Rollback**: Data consistency

### Exception Management
- **Try-Catch Blocks**: Comprehensive error handling
- **Logging**: Error tracking and debugging
- **User Feedback**: Clear error messages
- **Recovery**: Automatic retry mechanisms

## Performance Optimization

### Query Optimization
- **Efficient Queries**: Optimized database access
- **Lazy Loading**: Load data only when needed
- **Caching**: Reduce database calls
- **Indexing**: Fast data retrieval

### Memory Management
- **Scoped Sessions**: Proper resource cleanup
- **Connection Pooling**: Efficient resource usage
- **Garbage Collection**: Automatic memory management
- **Resource Limits**: Prevent memory leaks

## Security Features

### Data Protection
- **Input Sanitization**: Prevent SQL injection
- **Type Validation**: Ensure data integrity
- **Access Control**: Secure database access
- **Encryption**: Protect sensitive data

### File Security
- **Secure Paths**: Safe file operations
- **Permission Management**: Proper file access
- **Backup Systems**: Data protection
- **Audit Logging**: Track changes

## Integration Points

### GUI Integration
- **Tkinter Variables**: Seamless GUI binding
- **Real-time Updates**: Live configuration changes
- **Data Validation**: Input validation
- **Error Display**: User-friendly messages

### System Integration
- **File Operations**: Database file management
- **Process Management**: System integration
- **Configuration**: System settings
- **Logging**: System logging

## Usage Examples

### Basic Usage
```python
# Initialize database
settings = Settings()
categories = Categories()
vulnerabilities = OptionTables()

# Get configuration
config = settings.get_settings(True)
vuln_config = vulnerabilities.get_option_table("Add User", True)

# Update settings
settings.update_table(config)
vulnerabilities.update_table("Add User", vuln_config)
```

### Advanced Usage
```python
# Create new vulnerability
vuln = vulnerabilities.add_to_table("Custom Vuln", 
                                   Enabled=True, 
                                   Points=10)

# Get by category
account_vulns = vulnerabilities.get_option_template_by_category(1)

# Remove entry
vulnerabilities.remove_from_table("Add User", vuln_id)
```

## Dependencies
- **SQLAlchemy**: ORM framework
- **SQLite**: Database backend
- **Tkinter**: GUI variable types
- **Standard Library**: System operations

## Related Files
- **configurator.py**: Uses for configuration management
- **scoring_engine.py**: Uses for scoring data
- **uniqueID.py**: May reference for user data
- **admin_test.py**: Used for privilege checking

## Database Schema
```sql
-- Settings table
CREATE TABLE Settings (
    id INTEGER PRIMARY KEY,
    style VARCHAR(128) NOT NULL DEFAULT 'black',
    desktop TEXT NOT NULL DEFAULT ' ',
    silent_mode BOOLEAN NOT NULL DEFAULT 0,
    server_mode BOOLEAN NOT NULL DEFAULT 0,
    server_name VARCHAR(255),
    server_user VARCHAR(255),
    server_pass VARCHAR(128),
    tally_points INTEGER NOT NULL DEFAULT 0,
    tally_vuln INTEGER NOT NULL DEFAULT 0,
    current_points INTEGER NOT NULL DEFAULT 0,
    current_vuln INTEGER NOT NULL DEFAULT 0
);

-- Categories table
CREATE TABLE "Vulnerability Categories" (
    id INTEGER PRIMARY KEY,
    name VARCHAR(128) NOT NULL UNIQUE,
    description TEXT NOT NULL
);

-- Vulnerability templates table
CREATE TABLE "Vulnerability Template" (
    id INTEGER PRIMARY KEY,
    name VARCHAR(128) NOT NULL UNIQUE,
    category INTEGER REFERENCES "Vulnerability Categories"(id),
    definition TEXT NOT NULL,
    description TEXT,
    checks TEXT
);
```
