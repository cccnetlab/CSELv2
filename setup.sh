#!/usr/bin/env bash
set -euo pipefail

# setup.sh - Master setup script for CSEL on a fresh Linux machine
# This script orchestrates all setup steps in the correct order
# Usage: sudo bash setup.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"

echo "=========================================="
echo "CSEL Master Setup Script"
echo "=========================================="
echo "This will set up the complete CSEL environment"
echo ""

# Check for root privileges
if [ "${EUID:-$(id -u)}" -ne 0 ]; then
    echo "ERROR: This script must be run with sudo"
    echo "Usage: sudo bash setup.sh"
    exit 1
fi

# Check if running on supported distribution
if ! command -v apt-get >/dev/null 2>&1; then
    echo "ERROR: This script requires a Debian/Ubuntu-based distribution"
    exit 1
fi

# ==================== STEP 1: Install Dependencies ====================
echo ""
echo "Step 1: Installing system and Python dependencies..."
echo "=========================================="

if [ -f "${SCRIPT_DIR}/dep_install.sh" ]; then
    bash "${SCRIPT_DIR}/dep_install.sh"
    echo "✓ Dependencies installed"
else
    echo "ERROR: dep_install.sh not found"
    exit 1
fi

# ==================== STEP 2: Create CYBERPATRIOT Directory ====================
echo ""
echo "Step 2: Setting up CYBERPATRIOT directories..."
echo "=========================================="

# Create /etc/CYBERPATRIOT directory (used by scoring engine)
mkdir -p /etc/CYBERPATRIOT
echo "✓ Created /etc/CYBERPATRIOT"

# Create /var/www/CYBERPATRIOT for HTML reports
mkdir -p /var/www/CYBERPATRIOT
echo "✓ Created /var/www/CYBERPATRIOT"

# Create /etc/CYBERPATRIOT_DO_NOT_REMOVE for assets
ASSET_DIR="/etc/CYBERPATRIOT_DO_NOT_REMOVE"
if [ ! -d "${ASSET_DIR}" ]; then
    mkdir -p "${ASSET_DIR}"
    
    # Copy icons
    ICONS_SRC="${SCRIPT_DIR}/assets/icons"
    if [ -d "${ICONS_SRC}" ]; then
        cp "${ICONS_SRC}/logo.png" "${ASSET_DIR}/" 2>/dev/null || true
        cp "${ICONS_SRC}/CCC_logo.png" "${ASSET_DIR}/" 2>/dev/null || true
        cp "${ICONS_SRC}/SoCalCCCC.png" "${ASSET_DIR}/" 2>/dev/null || true
        
        # Also copy to /var/www for HTML access
        cp "${ICONS_SRC}/CCC_logo.png" /var/www/CYBERPATRIOT/ 2>/dev/null || true
        cp "${ICONS_SRC}/SoCalCCCC.png" /var/www/CYBERPATRIOT/ 2>/dev/null || true
        echo "✓ Copied icon assets"
    fi
    
    # Create placeholder score file
    touch "${ASSET_DIR}/score"
    echo "✓ Created /etc/CYBERPATRIOT_DO_NOT_REMOVE"
fi

# ==================== STEP 3: Build Binaries ====================
echo ""
echo "Step 3: Building binaries with PyInstaller..."
echo "=========================================="

if [ -f "${SCRIPT_DIR}/build.py" ]; then
    # Activate venv and build
    source "${VENV_DIR}/bin/activate"
    
    # Run build.py non-interactively
    # Answers: Clean builds? (y), Have you run dep_install? (y), Build scoring_engine? (y), Build configurator? (y)
    printf "y\ny\ny\n" | "${VENV_DIR}/bin/python" "${SCRIPT_DIR}/build.py" || {
        echo "ERROR: Build failed"
        exit 1
    }
    echo "✓ Binaries built successfully"
else
    echo "ERROR: build.py not found"
    exit 1
fi

# ==================== STEP 4: Setup Service ====================
echo ""
echo "Step 4: Setting up systemd service..."
echo "=========================================="

if [ -f "${SCRIPT_DIR}/service_setup.py" ]; then
    # Run service setup (skip interactive prompts)
    "${VENV_DIR}/bin/python" "${SCRIPT_DIR}/service_setup.py" <<EOF
n
EOF
    echo "✓ Service configured"
else
    echo "ERROR: service_setup.py not found"
    exit 1
fi

# ==================== STEP 5: Create Desktop Shortcuts ====================
echo ""
echo "Step 5: Creating desktop shortcuts..."
echo "=========================================="

# Get the actual user (not root)
ACTUAL_USER="${SUDO_USER:-${USER}}"
USER_HOME=$(eval echo ~"${ACTUAL_USER}")
DESKTOP_DIR="${USER_HOME}/Desktop"

# Ensure Desktop directory exists
mkdir -p "${DESKTOP_DIR}"

# Create Start Scoring Engine desktop shortcut
cat > "${DESKTOP_DIR}/Start_Scoring_Engine.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Start Scoring Engine
Comment=Start the CSEL Scoring Engine Service
Exec=bash -c 'sudo systemctl start scoring_engine && echo "Scoring engine started!" && sleep 2'
Icon=${ASSET_DIR}/SoCalCCCC.png
Terminal=true
Categories=Utility;
EOF
chmod +x "${DESKTOP_DIR}/Start_Scoring_Engine.desktop"
chown "${ACTUAL_USER}":"${ACTUAL_USER}" "${DESKTOP_DIR}/Start_Scoring_Engine.desktop"
echo "✓ Created Start Scoring Engine desktop shortcut"

# Create Stop Scoring Engine desktop shortcut
cat > "${DESKTOP_DIR}/Stop_Scoring_Engine.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Stop Scoring Engine
Comment=Stop the CSEL Scoring Engine Service
Exec=bash -c 'sudo systemctl stop scoring_engine && echo "Scoring engine stopped!" && sleep 2'
Icon=${ASSET_DIR}/SoCalCCCC.png
Terminal=true
Categories=Utility;
EOF
chmod +x "${DESKTOP_DIR}/Stop_Scoring_Engine.desktop"
chown "${ACTUAL_USER}":"${ACTUAL_USER}" "${DESKTOP_DIR}/Stop_Scoring_Engine.desktop"
sudo -u "${ACTUAL_USER}" gio set "${DESKTOP_DIR}/Stop_Scoring_Engine.desktop" metadata::trusted true
echo "✓ Created Stop Scoring Engine desktop shortcut"

# ==================== STEP 6: Run Configurator ====================
echo ""
echo "Step 6: Running configurator for initial setup..."
echo "=========================================="
echo ""
echo "IMPORTANT: You must configure vulnerabilities before starting the scoring engine."
echo "The configurator will now launch. Please:"
echo "  1. Set up your desired vulnerabilities"
echo "  2. Configure points and settings"
echo "  3. Press 'Commit' when finished"
echo ""
read -p "Press Enter to launch the configurator..."

# Launch configurator with proper environment (needs root for writing to /etc/)
sudo -E "${VENV_DIR}/bin/python" "${SCRIPT_DIR}/src/configurator.py" || {
    echo ""
    echo "WARNING: Configurator exited. You can run it again later with:"
    echo "  sudo -E ${SCRIPT_DIR}/dist/configurator_DO_NOT_TOUCH"
    echo "  OR double-click: Desktop/CSEL_Configurator.desktop"
}

echo ""
echo "✓ Configurator setup complete"

# ==================== STEP 7: Start Scoring Engine ====================
echo ""
echo "Step 7: Starting scoring engine service..."
echo "=========================================="
echo ""
read -p "Start the scoring engine service now? (Y/n): " start_choice

if [ "${start_choice,,}" != "n" ]; then
    echo "Starting scoring engine service..."
    systemctl start scoring_engine
    sleep 2
    systemctl status scoring_engine --no-pager || true
    echo ""
    echo "✓ Scoring engine started"
else
    echo "Skipped. You can start it later with:"
    echo "  sudo systemctl start scoring_engine"
    echo "  OR double-click: Desktop/Start_Scoring_Engine.desktop"
fi

# ==================== SUMMARY ====================
echo ""
echo "=========================================="
echo "✓ CSEL Setup Complete!"
echo "=========================================="
echo ""
echo "What was installed:"
echo "  • System dependencies (python3-tk, lsb-release, etc.)"
echo "  • Python virtual environment at ${VENV_DIR}"
echo "  • Python packages from requirements.txt"
echo "  • Scoring engine binariy in dist/"
echo "  • Systemd service: scoring_engine.service"
echo "  • Desktop shortcuts on ${DESKTOP_DIR}"
echo ""
echo "Desktop shortcuts created:"
echo "  • Start_Scoring_Engine.desktop - Start the scoring service"
echo "  • Stop_Scoring_Engine.desktop - Stop the scoring service"
echo "  • ScoringReport.desktop - View score (appears after engine runs)"
echo ""
echo "IMPORTANT - Making Changes:"
echo "  If you modify vulnerabilities in the Configurator, you MUST restart"
echo "  the scoring engine service for changes to take effect:"
echo ""
echo "    sudo systemctl restart scoring_engine"
echo ""
echo "  Or stop and start using the desktop shortcuts"
echo ""
echo "Service management:"
echo "  • Start:   sudo systemctl start scoring_engine"
echo "  • Stop:    sudo systemctl stop scoring_engine"
echo "  • Restart: sudo systemctl restart scoring_engine"
echo "  • Status:  sudo systemctl status scoring_engine"
echo "  • Logs:    sudo journalctl -u scoring_engine -f"
echo ""
echo "View scoring report:"
echo "  After the scoring engine runs, a ScoringReport.desktop icon will"
echo "  appear on your Desktop. Double-click it to view your current score."
echo ""
echo "=========================================="
