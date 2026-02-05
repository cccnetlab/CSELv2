# CSEL Quick Setup Guide

This guide explains how to set up CSEL on a fresh Linux machine.

## Prerequisites

- Ubuntu/Debian-based Linux distribution (Linux Mint, Ubuntu, etc.)
- Internet connection for downloading packages
- Sudo/root access

## One-Command Setup

For a completely fresh machine, run:

```bash
sudo bash setup.sh
```

This master script will automatically:
1. Install all system dependencies (python3-tk, lsb-release, libpwquality-tools, etc.)
2. Create Python virtual environment (`.venv/`)
3. Install all Python packages from `requirements.txt`
4. Build scoring engine and configurator binaries
5. Set up systemd service for the scoring engine
6. Create `/etc/CYBERPATRIOT` and `/var/www/CYBERPATRIOT` directories
7. Copy icon assets to system directories
8. Create desktop shortcuts for easy access

## Manual Setup (Step-by-Step)

If you prefer to run each step manually:

### 1. Install Dependencies
```bash
bash dep_install.sh
```

### 2. Activate Virtual Environment
```bash
source .venv/bin/activate
```

### 3. Build Binaries
```bash
python build.py
```

### 4. Set Up Service
```bash
sudo python service_setup.py
```

## Using CSEL

### First Time Setup

**The automated setup script (`sudo bash setup.sh`) will guide you through:**

1. **Configurator Launch** - The script will automatically launch the configurator:
   - Configure your scoring vulnerabilities
   - Set points for each vulnerability
   - Click "Commit" to save your configuration

2. **Start the Scoring Engine** - The script will offer to start the service:
   - Choose 'Y' to start immediately
   - Or start manually later (see below)

3. **View Scoring Report**:
   - After the engine runs, a `ScoringReport.desktop` will appear on your Desktop
   - Double-click it to view your current score in a browser

### Making Configuration Changes

**⚠️ IMPORTANT:** If you modify vulnerabilities in the Configurator after the initial setup, you **MUST restart the scoring engine service** for changes to take effect.

**To apply changes:**

1. Run the Configurator:
   - Double-click `Desktop/CSEL_Configurator.desktop`
   - OR: `sudo -E ./dist/configurator_DO_NOT_TOUCH`

2. Make your changes and click "Commit"

3. **Restart the scoring engine:**
   ```bash
   sudo systemctl restart scoring_engine
   ```
   OR use the desktop shortcut: `CSEL_Scoring_Engine.desktop` → Option 3 (Restart)

### Managing the Scoring Engine

**Using the Desktop Shortcut:**
- Double-click `CSEL_Scoring_Engine.desktop` for an interactive menu with options to:
  - Start/Stop/Restart the service
  - View status and logs
  - Enable/disable auto-start on boot

**Using systemctl directly:**
```bash
sudo systemctl start scoring_engine    # Start the engine
sudo systemctl stop scoring_engine     # Stop the engine
sudo systemctl restart scoring_engine  # Restart the engine
sudo systemctl status scoring_engine   # Check status
sudo systemctl enable scoring_engine   # Auto-start on boot
sudo systemctl disable scoring_engine  # Don't auto-start on boot
```

**View logs:**
```bash
sudo journalctl -u scoring_engine -f   # Follow logs in real-time
sudo journalctl -u scoring_engine -n 100  # Last 100 lines
```

## File Structure

After setup, your installation will have:

```
CSELv2/
├── setup.sh                          # Master setup script
├── dep_install.sh                    # Dependency installer
├── build.py                          # Binary builder
├── service_setup.py                  # Service installer
├── control_scoring_engine.sh         # Service control script
├── .venv/                            # Python virtual environment
├── dist/                             # Built binaries
│   ├── configurator_DO_NOT_TOUCH
│   └── scoring_engine_DO_NOT_TOUCH
├── src/                              # Source code
│   ├── scoring_engine.py
│   ├── configurator.py
│   └── db_handler.py
└── assets/                           # Icons and resources
```

## System Files Created

- `/etc/CYBERPATRIOT/` - Scoring engine data
- `/etc/CYBERPATRIOT_DO_NOT_REMOVE/` - Icon assets
- `/var/www/CYBERPATRIOT/` - HTML scoring report
- `/etc/systemd/system/scoring_engine.service` - Service configuration
- `/usr/local/bin/scoring_engine_DO_NOT_TOUCH` - Symlink to binary
- `~/Desktop/CSEL_*.desktop` - Desktop shortcuts
- `~/Desktop/ScoringReport.desktop` - Score viewer (created when engine runs)

## Troubleshooting

### Service won't start
```bash
sudo systemctl status scoring_engine  # Check for errors
sudo journalctl -u scoring_engine -n 50  # View recent logs
```

### Binaries not found
```bash
# Rebuild binaries
source .venv/bin/activate
python build.py
```

### Permission errors
```bash
# Ensure you're running with sudo
sudo systemctl start scoring_engine
sudo -E ./dist/configurator_DO_NOT_TOUCH
```

### Desktop shortcuts not working
```bash
# Make them executable
chmod +x ~/Desktop/CSEL_*.desktop
```

## Uninstall

To remove CSEL:

```bash
# Stop and disable service
sudo systemctl stop scoring_engine
sudo systemctl disable scoring_engine

# Remove service file and symlink
sudo rm /etc/systemd/system/scoring_engine.service
sudo rm /usr/local/bin/scoring_engine_DO_NOT_TOUCH
sudo systemctl daemon-reload

# Remove system directories
sudo rm -rf /etc/CYBERPATRIOT
sudo rm -rf /etc/CYBERPATRIOT_DO_NOT_REMOVE
sudo rm -rf /var/www/CYBERPATRIOT

# Remove desktop shortcuts
rm ~/Desktop/CSEL_*.desktop
rm ~/Desktop/ScoringReport.desktop

# Remove project directory
cd ..
rm -rf CSELv2
```

## Support

For issues or questions, refer to:
- `docs/` directory for detailed documentation
- `CHANGELOG.md` for version history
- GitHub repository issues
