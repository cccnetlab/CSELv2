# CSEL (Cyberpatriot Scoring Engine: Linux) Documentation

## Overview
The CSEL (Cyberpatriot Scoring Engine: Linux) is a comprehensive scoring system designed for Cyberpatriot competitions. It provides automated vulnerability assessment, real-time scoring, and detailed reporting for Linux-based systems.

## System Architecture
The CSEL system consists of six main components that work together to provide a complete scoring solution:

### Core Components

#### 1. Package Initialization (`__init__.py`)
- **Purpose**: Package metadata and version management
- **Version**: 1.1.0
- **Function**: Enables proper Python package structure and version tracking

#### 2. Administrative Privilege Management (`admin_test.py`)
- **Purpose**: Cross-platform privilege checking and elevation
- **Platforms**: Windows (UAC) and POSIX (root)
- **Function**: Ensures scoring engine runs with necessary permissions

#### 3. Main Scoring Engine (`scoring_engine.py`)
- **Purpose**: Core vulnerability assessment and scoring
- **Function**: Continuous monitoring, scoring, and report generation
- **Features**: Real-time HTML reports, desktop notifications, forensic validation

#### 4. User Credential Collection (`uniqueID.py`)
- **Purpose**: Team and user information collection
- **Function**: GUI for inputting team details and configuring FTP uploads
- **Features**: Form validation, unique filename generation, FTP configuration

#### 5. Configuration Management (`configurator.py`)
- **Purpose**: Comprehensive configuration interface
- **Function**: Vulnerability setup, scoring parameters, system settings
- **Features**: Tabbed GUI, theme support, report generation, deployment

#### 6. Database Management (`db_handler.py`)
- **Purpose**: Data persistence and management
- **Function**: SQLAlchemy ORM with SQLite backend
- **Features**: Dynamic table creation, configuration storage, scoring data

## Vulnerability Categories

### Account Management
- User creation and removal
- Group membership management
- Administrator privileges
- Password changes
- Critical user protection

### Local Policy
- Password policies (age, length, complexity)
- Login restrictions and lockouts
- Audit settings
- SSH security configurations
- Kernel updates

### Program Management
- Program installation and removal
- Service configuration
- Update management
- Critical program protection
- Startup applications

### File Management
- Forensic question validation
- File operations (add/remove text)
- File permissions
- Hosts file management
- Startup program removal

### Firewall Management
- Firewall enablement
- Port configuration (open/closed)
- Network security validation
- Service accessibility

## System Workflow

### 1. Initial Setup
1. **User Credentials**: Run `uniqueID.py` to collect team information
2. **Configuration**: Run `configurator.py` to set up vulnerabilities and scoring
3. **Deployment**: Commit configuration to deploy scoring engine
4. **Monitoring**: Scoring engine runs continuously with real-time reports

### 2. Scoring Process
1. **Privilege Check**: Ensure administrative access
2. **Data Loading**: Load system information and configurations
3. **Vulnerability Assessment**: Check each configured vulnerability
4. **Score Calculation**: Award points for fixes, deduct for penalties
5. **Report Generation**: Create HTML reports with real-time updates
6. **Notification**: Send desktop notifications for score changes

### 3. Configuration Management
1. **Vulnerability Setup**: Define what to score and how many points
2. **System Settings**: Configure paths, themes, and preferences
3. **FTP Configuration**: Set up automatic score uploads
4. **Report Generation**: Create configuration reports
5. **Deployment**: Deploy changes to the scoring system

## Key Features

### Real-Time Scoring
- Continuous vulnerability monitoring
- Live HTML score reports
- Desktop notifications for changes
- Automatic score tracking

### Comprehensive Assessment
- 25+ vulnerability types
- 5 major categories
- Customizable scoring parameters
- Forensic question support

### User-Friendly Interface
- Tabbed configuration interface
- Multiple GUI themes
- Drag-and-drop functionality
- Real-time validation

### System Integration
- Administrative privilege management
- Cron job automation
- FTP upload support
- Desktop integration

### Data Management
- SQLite database backend
- Dynamic table creation
- Configuration persistence
- Data validation and integrity

## Technical Specifications

### Requirements
- **Operating System**: Linux (Ubuntu/Debian recommended)
- **Python Version**: 3.6+
- **Privileges**: Administrative/root access
- **Dependencies**: See requirements.txt

### Dependencies
- **GUI**: Tkinter, ttkthemes
- **Database**: SQLAlchemy, SQLite
- **System**: psutil, crontab
- **Network**: socket, subprocess
- **Security**: pwd, grp, lsb_release

### File Structure
```
CSELv2/
├── src/
│   ├── __init__.py          # Package initialization
│   ├── admin_test.py        # Privilege management
│   ├── scoring_engine.py    # Main scoring engine
│   ├── uniqueID.py          # User credential collection
│   ├── configurator.py      # Configuration interface
│   └── db_handler.py        # Database management
├── assets/
│   └── icons/               # GUI assets
├── docs/                    # Documentation
├── scripts/                 # Deployment scripts
└── data/                    # Data files
```

## Security Considerations

### Privilege Management
- Requires administrative access for system operations
- Uses UAC elevation on Windows
- Validates root access on Linux
- Secure file operations

### Data Protection
- Input validation and sanitization
- Secure database operations
- File permission management
- Audit logging

### System Security
- Minimal privilege requirements
- Secure configuration storage
- Protected file operations
- Network security validation

## Performance Optimization

### Efficient Operations
- Lazy loading of system data
- Optimized database queries
- Minimal resource usage
- Efficient file operations

### Scalability
- Configurable scoring intervals
- Modular vulnerability system
- Extensible architecture
- Performance monitoring

## Usage Examples

### Basic Setup
```bash
# 1. Collect user credentials
python3 src/uniqueID.py

# 2. Configure vulnerabilities
python3 src/configurator.py

# 3. Deploy and start scoring
# (Configuration is automatically deployed)
```

### Advanced Configuration
```python
# Custom vulnerability setup
vulnerabilities = OptionTables()
vuln_config = vulnerabilities.get_option_table("Add User", True)
vuln_config[1]["Enabled"].set(1)
vuln_config[1]["Points"].set(10)
vulnerabilities.update_table("Add User", vuln_config)
```

## Troubleshooting

### Common Issues
1. **Permission Errors**: Ensure running as administrator
2. **Database Errors**: Check file permissions in `/etc/CYBERPATRIOT/`
3. **GUI Issues**: Verify Tkinter installation
4. **Scoring Problems**: Check vulnerability configurations

### Log Files
- `scoring_engine.log`: Main scoring engine logs
- Database: `/etc/CYBERPATRIOT/save_data.db`
- Reports: `/var/www/CYBERPATRIOT/ScoreReport.html`

## Development and Customization

### Adding New Vulnerabilities
1. Define vulnerability template in `configurator.py`
2. Add scoring logic in `scoring_engine.py`
3. Update database schema
4. Test and validate

### Custom Themes
1. Add theme to `themeList` in `configurator.py`
2. Define theme settings
3. Apply custom styling
4. Test across different systems

### Integration
- Modular design allows easy integration
- Well-defined APIs for data access
- Extensible vulnerability system
- Comprehensive documentation

## Support and Maintenance

### Documentation
- Comprehensive function documentation
- Usage examples and tutorials
- Troubleshooting guides
- API reference

### Updates
- Version tracking and management
- Backward compatibility
- Migration tools
- Update notifications

### Community
- Open source development
- Community contributions
- Bug reporting and fixes
- Feature requests

## Conclusion

The CSEL system provides a comprehensive, user-friendly solution for Cyberpatriot competition scoring. With its modular architecture, extensive vulnerability coverage, and real-time reporting capabilities, it offers both flexibility and reliability for educational cybersecurity competitions.

The system's design emphasizes ease of use, security, and performance, making it suitable for both competition use and educational purposes. Its comprehensive documentation and well-structured codebase ensure maintainability and extensibility for future enhancements.
