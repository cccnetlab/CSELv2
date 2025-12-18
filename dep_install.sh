#!/usr/bin/env bash
set -euo pipefail

# dep_install.sh - Complete dependency installer for CSEL
# Installs system packages and sets up Python virtual environment with all required packages
# Usage: bash dep_install.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"
REQUIREMENTS_FILE="${SCRIPT_DIR}/requirements.txt"

# System packages to install
PKGS=(python3-tk libpwquality-tools pamtester python3-venv python3-pip libpam-pwquality)
LSB_PKG=lsb-release

echo "=========================================="
echo "CSEL Dependency Installer"
echo "=========================================="

# Check for apt-get (Debian/Ubuntu only)
if ! command -v apt-get >/dev/null 2>&1; then
	echo "ERROR: apt-get not found. This script supports Debian/Ubuntu only." >&2
	exit 1
fi

# Determine if we need sudo
SUDO=''
if [ "${EUID:-$(id -u)}" -ne 0 ]; then
	SUDO='sudo'
fi

# ==================== SYSTEM PACKAGES ====================

echo ""
echo "Step 1: Installing system packages..."
echo "=========================================="

echo "Updating package lists..."
${SUDO} apt-get update -y

install_if_missing() {
	local pkg=$1
	if dpkg -s "$pkg" >/dev/null 2>&1; then
		echo "  ✓ $pkg is already installed"
		return 0
	fi
	echo "  Installing $pkg..."
	if [ -n "${SUDO}" ]; then
		${SUDO} env DEBIAN_FRONTEND=noninteractive apt-get install -y "$pkg"
	else
		DEBIAN_FRONTEND=noninteractive apt-get install -y "$pkg"
	fi
}

ensure_lsb_release() {
	# Ensure lsb-release is installed and at least version 0.1.0
	if dpkg -s "$LSB_PKG" >/dev/null 2>&1; then
		ver=$(dpkg-query -W -f='${Version}' "$LSB_PKG" 2>/dev/null || echo "0")
		if dpkg --compare-versions "$ver" ge "0.1.0"; then
			echo "  ✓ lsb-release version OK: $ver"
			return 0
		else
			echo "  lsb-release version $ver is older than 0.1.0 — upgrading"
		fi
	else
		echo "  lsb-release not installed — installing"
	fi
	if [ -n "${SUDO}" ]; then
		${SUDO} env DEBIAN_FRONTEND=noninteractive apt-get install -y "$LSB_PKG"
	else
		DEBIAN_FRONTEND=noninteractive apt-get install -y "$LSB_PKG"
	fi
}

echo "Ensuring lsb-release >= 0.1.0..."
ensure_lsb_release

for p in "${PKGS[@]}"; do
	install_if_missing "$p"
done

echo ""
echo "✓ System packages installed successfully"

# ==================== VIRTUAL ENVIRONMENT ====================

echo ""
echo "Step 2: Setting up Python virtual environment..."
echo "=========================================="

# Create venv if it doesn't exist
if [ ! -d "${VENV_DIR}" ]; then
	echo "Creating virtual environment at ${VENV_DIR}..."
	python3 -m venv "${VENV_DIR}"
	echo "  ✓ Virtual environment created"
else
	echo "  ✓ Virtual environment already exists at ${VENV_DIR}"
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source "${VENV_DIR}/bin/activate"

# Upgrade pip in the venv
echo "Upgrading pip..."
python -m pip install --upgrade pip

# ==================== PYTHON PACKAGES ====================

echo ""
echo "Step 3: Installing Python packages from requirements.txt..."
echo "=========================================="

if [ ! -f "${REQUIREMENTS_FILE}" ]; then
	echo "WARNING: requirements.txt not found at ${REQUIREMENTS_FILE}" >&2
	echo "Skipping Python package installation."
else
	echo "Installing packages from ${REQUIREMENTS_FILE}..."
	python -m pip install -r "${REQUIREMENTS_FILE}"
	echo ""
	echo "✓ Python packages installed successfully"
fi

# ==================== SUMMARY ====================

echo ""
echo "=========================================="
echo "✓ All dependencies installed successfully!"
echo "=========================================="
echo ""
echo "System packages installed:"
dpkg -l python3-tk lsb-release libpwquality-tools pamtester python3-venv python3-pip 2>/dev/null | grep "^ii" || true
echo ""
echo "Python packages in venv:"
python -m pip list
echo ""
echo "=========================================="
echo "To activate the virtual environment, run:"
echo "  source ${VENV_DIR}/bin/activate"
echo ""
echo "To run build.py with the venv:"
echo "  source ${VENV_DIR}/bin/activate && python build.py"
echo "  OR"
echo "  ${VENV_DIR}/bin/python build.py"
echo "=========================================="

