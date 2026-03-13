#!/usr/bin/env bash
set -euo pipefail

# cleanup.sh - Uninstall CSEL and reset machine to pre-installation state
# This script removes all components installed by setup.sh
# Usage: sudo bash cleanup.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "CSEL Cleanup and Uninstall Script"
echo "=========================================="
echo ""
echo "⚠️  WARNING: This will remove ALL CSEL components:"
echo "  • Systemd service"
echo "  • Desktop shortcuts"
echo "  • System directories (/etc/CYBERPATRIOT, /var/www/CYBERPATRIOT)"
echo "  • Symlinks and binaries"
echo "  • Database (all configurations)"
echo "  • Control scripts"
echo ""
read -p "Are you sure you want to continue? (yes/NO): " confirm

if [ "${confirm,,}" != "yes" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

# Check for root privileges
if [ "${EUID:-$(id -u)}" -ne 0 ]; then
    echo "ERROR: This script must be run with sudo"
    echo "Usage: sudo bash cleanup.sh"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER="${SUDO_USER:-${USER}}"
USER_HOME=$(eval echo ~"${ACTUAL_USER}")
DESKTOP_DIR="${USER_HOME}/Desktop"

echo ""
echo "Starting cleanup..."
echo ""

# ==================== STEP 1: Stop and Disable Service ====================
echo "Step 1: Stopping and disabling scoring engine service..."
echo "=========================================="

if systemctl list-unit-files | grep -q "scoring_engine.service"; then
    # Stop the service if running
    if systemctl is-active --quiet scoring_engine; then
        echo "Stopping scoring engine service..."
        systemctl stop scoring_engine || true
    fi
    
    # Disable the service
    if systemctl is-enabled --quiet scoring_engine 2>/dev/null; then
        echo "Disabling scoring engine service..."
        systemctl disable scoring_engine || true
    fi
    
    echo "✓ Service stopped and disabled"
else
    echo "✓ Service not found (already removed or never installed)"
fi

# ==================== STEP 2: Remove Service Files ====================
echo ""
echo "Step 2: Removing systemd service files..."
echo "=========================================="

SERVICE_FILE="/etc/systemd/system/scoring_engine.service"
if [ -f "${SERVICE_FILE}" ]; then
    rm -f "${SERVICE_FILE}"
    systemctl daemon-reload
    echo "✓ Removed ${SERVICE_FILE}"
else
    echo "✓ Service file not found"
fi

# ==================== STEP 3: Remove Symlink ====================
echo ""
echo "Step 3: Removing symlink..."
echo "=========================================="

SYMLINK="/usr/local/bin/scoring_engine_DO_NOT_TOUCH"
if [ -L "${SYMLINK}" ] || [ -f "${SYMLINK}" ]; then
    rm -f "${SYMLINK}"
    echo "✓ Removed ${SYMLINK}"
else
    echo "✓ Symlink not found"
fi

# ==================== STEP 4: Remove Desktop Shortcuts ====================
echo ""
echo "Step 4: Removing desktop shortcuts..."
echo "=========================================="

SHORTCUTS=(
    "${DESKTOP_DIR}/Start_Scoring_Engine.desktop"
    "${DESKTOP_DIR}/Stop_Scoring_Engine.desktop"
    "${DESKTOP_DIR}/ScoringReport.desktop"
    "${DESKTOP_DIR}/CSEL_Configurator.desktop"
    "${DESKTOP_DIR}/CSEL_Scoring_Engine.desktop"
)

for shortcut in "${SHORTCUTS[@]}"; do
    if [ -f "${shortcut}" ]; then
        rm -f "${shortcut}"
        echo "✓ Removed $(basename "${shortcut}")"
    fi
done

echo "✓ Desktop shortcuts cleaned up"

# ==================== STEP 5: Remove System Directories ====================
echo ""
echo "Step 5: Removing system directories..."
echo "=========================================="

DIRS_TO_REMOVE=(
    "/etc/CYBERPATRIOT"
    "/etc/CYBERPATRIOT_DO_NOT_REMOVE"
    "/var/www/CYBERPATRIOT"
)

for dir in "${DIRS_TO_REMOVE[@]}"; do
    if [ -d "${dir}" ]; then
        rm -rf "${dir}"
        echo "✓ Removed ${dir}"
    else
        echo "✓ ${dir} not found"
    fi
done

# ==================== STEP 6: Remove Control Script ====================
echo ""
echo "Step 6: Removing control script..."
echo "=========================================="

CONTROL_SCRIPT="${SCRIPT_DIR}/control_scoring_engine.sh"
if [ -f "${CONTROL_SCRIPT}" ]; then
    rm -f "${CONTROL_SCRIPT}"
    echo "✓ Removed control_scoring_engine.sh"
else
    echo "✓ Control script not found"
fi

# ==================== STEP 7: Remove Binaries ====================
echo ""
echo "Step 7: Removing built binaries..."
echo "=========================================="

if [ -d "${SCRIPT_DIR}/dist" ]; then
    rm -rf "${SCRIPT_DIR}/dist"
    echo "✓ Removed dist/ directory"
else
    echo "✓ dist/ directory not found"
fi

if [ -d "${SCRIPT_DIR}/build" ]; then
    rm -rf "${SCRIPT_DIR}/build"
    echo "✓ Removed build/ directory"
fi

# Remove .spec files
for spec in "${SCRIPT_DIR}"/*.spec; do
    if [ -f "${spec}" ]; then
        rm -f "${spec}"
        echo "✓ Removed $(basename "${spec}")"
    fi
done

# ==================== STEP 8: Reset Database ====================
echo ""
echo "Step 8: Resetting database..."
echo "=========================================="

if [ -f "${SCRIPT_DIR}/reset_database.py" ]; then
    # Check if venv exists
    if [ -d "${SCRIPT_DIR}/.venv" ]; then
        echo "Running database reset script..."
        # Run reset_database with 'yes' confirmation
        echo "yes" | "${SCRIPT_DIR}/.venv/bin/python" "${SCRIPT_DIR}/reset_database.py" || {
            echo "⚠️  Database reset had issues, but continuing..."
        }
        echo "✓ Database reset complete"
    else
        echo "⚠️  Virtual environment not found, skipping database reset"
        echo "   (Database files may still exist in /etc/CYBERPATRIOT if it wasn't removed)"
    fi
else
    echo "⚠️  reset_database.py not found, skipping database reset"
fi

# ==================== STEP 9: Clean logs ====================
echo ""
echo "Step 9: Cleaning logs..."
echo "=========================================="

LOG_FILE="${SCRIPT_DIR}/scoring_engine.log"
if [ -f "${LOG_FILE}" ]; then
    rm -f "${LOG_FILE}"
    echo "✓ Removed scoring_engine.log"
else
    echo "✓ No log file found"
fi

# ==================== STEP 10: Optional - Remove Virtual Environment ====================
echo ""
echo "Step 10: Virtual environment..."
echo "=========================================="
echo ""
read -p "Remove Python virtual environment (.venv/)? (y/N): " remove_venv

if [ "${remove_venv,,}" = "y" ]; then
    if [ -d "${SCRIPT_DIR}/.venv" ]; then
        rm -rf "${SCRIPT_DIR}/.venv"
        echo "✓ Removed .venv/ directory"
    else
        echo "✓ Virtual environment not found"
    fi
else
    echo "✓ Keeping virtual environment (can be reused for next setup)"
fi

# ==================== SUMMARY ====================
echo ""
echo "=========================================="
echo "✓ CSEL Cleanup Complete!"
echo "=========================================="
echo ""
echo "What was removed:"
echo "  • Systemd service and service files"
echo "  • Symlink at /usr/local/bin"
echo "  • Desktop shortcuts"
echo "  • System directories (/etc/CYBERPATRIOT, /var/www/CYBERPATRIOT)"
echo "  • Built binaries (dist/, build/)"
echo "  • Control scripts"
echo "  • Database (reset to empty state)"
echo "  • Log files"

if [ "${remove_venv,,}" != "y" ]; then
    echo ""
    echo "Kept for next setup:"
    echo "  • Virtual environment (.venv/)"
    echo "  • Source code (src/)"
    echo "  • Setup scripts (setup.sh, dep_install.sh, etc.)"
fi

echo ""
echo "Your machine is now clean and ready for testing setup.sh"
echo ""
echo "To test setup again, run:"
echo "  sudo bash setup.sh"
echo ""
echo "=========================================="
