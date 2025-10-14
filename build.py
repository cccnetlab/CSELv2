#!/usr/bin/env python3

"""
Build script for CSEL using PyInstaller
Compiles configurator and scoring_engine with proper asset bundling
"""

import os
import sys
import subprocess
import shutil
import platform


def clean_build():
    """
    Remove previous build binaries and artifacts by cleaning the build and dist directories
    and any existing spec files.
    """

    print("Cleaning previous builds...")
    dirs_to_remove = ["build", "dist"]
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  Removed {dir_name}/")

    # Remove spec files
    for spec_file in ["configurator.spec", "scoring_engine.spec"]:
        if os.path.exists(spec_file):
            os.remove(spec_file)
            print(f"  Removed {spec_file}")


def build_configurator():
    """
    Build configurator binary with PyInstaller
    """

    print("\n" + "=" * 60)
    print("Building configurator...")
    print("=" * 60)

    cmd = [
        "pyinstaller",
        "--onefile",
        "--name=configurator",
        "--add-data=assets/icons:assets/icons",
        "--add-data=src/db_handler.py:src",
        "--add-data=src/admin_test.py:src",
        "src/configurator.py",
    ]

    print("Command:", " ".join(cmd))
    result = subprocess.run(cmd, check=True)

    if result.returncode == 0:
        print("\n✓ Configurator built successfully: dist/configurator")
    return result.returncode


def build_scoring_engine():
    """
    Build scoring_engine binary with PyInstaller
    """

    print("\n" + "=" * 60)
    print("Building scoring_engine...")
    print("=" * 60)

    cmd = [
        "pyinstaller",
        "--onefile",
        "--name=scoring_engine",
        "--add-data=src/db_handler.py:src",
        "--add-data=src/admin_test.py:src",
        "src/scoring_engine.py",
    ]

    print("Command:", " ".join(cmd))
    result = subprocess.run(cmd, check=True)

    if result.returncode == 0:
        print("\n✓ Scoring engine built successfully: dist/scoring_engine")
    return result.returncode

def get_linux_distribution():
    """
    Returns the lowercase name of the Linux distribution (e.g., 'ubuntu', 'debian', 'fedora', 'arch').
    Tries lsb_release first, then falls back to /etc/os-release.

    Returns:
        str: Linux distribution name in lowercase, or empty string if undetermined.
    """

    import subprocess
    try:
        # Check for lsb_release, else install
        import lsb_release
    except ImportError:
        if shutil.which("lsb_release") is None:
            print("lsb_release not found. Attempting to install lsb-release package...")
            try:
                subprocess.check_call(["sudo", "apt-get", "update"])
                subprocess.check_call(["sudo", "apt-get", "install", "-y", "lsb-release"])
            except Exception:
                print("Failed to install lsb-release. Please install it manually.")
                return ""
    try:
        # Try to use lsb_release to gather distro info
        output = subprocess.check_output(['lsb_release', '-si'], text=True).strip().lower()
        return output
    except Exception:
        # Fallback to /etc/os-release
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("ID="):
                        return line.strip().split("=")[1].replace('"', '').lower()
        except Exception:
            pass
    return ""

def install_tkinter(os_type, distro):
    """
    Install tkinter via system package manager based on OS and distribution

    Args:
        os_type (str): Operating system type (e.g., 'Linux', 'Windows')
        distro (str): Linux distribution name in lowercase (e.g., 'ubuntu', 'debian')
    """
    
    if os_type == "Linux":
        if distro in ["ubuntu", "debian", "linuxmint"]:
            print("Installing python3-tk via apt-get...")
            subprocess.run(["sudo", "apt-get", "update"])
            subprocess.run(["sudo", "apt-get", "install", "-y", "python3-tk"])
        elif distro in ["fedora"]:
            print("Installing python3-tkinter via dnf...")
            subprocess.run(["sudo", "dnf", "install", "-y", "python3-tkinter"])
        elif distro in ["centos", "rhel"]:
            print("Installing python3-tkinter via yum...")
            subprocess.run(["sudo", "yum", "install", "-y", "python3-tkinter"])
        elif distro in ["arch"]:
            print("Installing tk via pacman...")
            subprocess.run(["sudo", "pacman", "-Sy", "tk"])
        else:
            print("Unknown Linux distribution. Please install tkinter manually (python3-tk or tkinter).")
    elif os_type == "Windows": # TODO: Check windows support
        print("On Windows, tkinter is usually included with Python. If missing, reinstall Python and ensure 'tcl/tk' is selected during installation.")
    else:
        print("Unsupported OS for automatic tkinter installation.")

def check_requirements(requirements_file="requirements.txt"):
    """
    Ensure tkinter and pip is installed and install required packages from requirements.txt

    Args:
        requirements_file (str): Path to the requirements.txt file, should be located in the same directory.
    """
    
    print("\n" + "=" * 60)
    print("Checking for required packages...\n")
    print("\n" + "=" * 60)

    # Detect OS type
    os_type = platform.system()
    print(f"Detected OS: {os_type}")

    ## LINUX SPECIFIC: Check for and install lsb_release if missing, and store distro info.
    if os_type == "Linux":
        linux_distribution = get_linux_distribution()
        print(f"Detected Linux distribution: {linux_distribution}")
    else:
        linux_distribution = None

    # Check for tkinter by importing, install if missing
    try:
        import tkinter
    except ImportError:
        print("tkinter not found. Attempting to install system package...")
        install_tkinter()

        # Check if installation succeeded
        try:
            import tkinter
        except ImportError:
            print("ERROR: tkinter installation failed. Please install manually.")
            sys.exit(1)
    print("✓ tkinter is installed")

    # Check if pip is installed
    if shutil.which("pip") is None:
        print("pip not found. Attempting to install pip...")
        if os_type == "Linux":
            try:
                subprocess.check_call([sys.executable, "-m", "ensurepip"])
            except Exception:
                subprocess.check_call(["sudo", "apt-get", "update"])
                subprocess.check_call(["sudo", "apt-get", "install", "-y", "python3-pip"])
        elif os_type == "Windows": # TODO: Check windows support
            subprocess.check_call([sys.executable, "-m", "ensurepip"])
        else:
            raise RuntimeError("Unsupported OS for automatic pip installation.")

    print("✓ pip is installed")

    # Install requirements from requirements.txt
    pip_cmd = [sys.executable, "-m", "pip", "install", "-r", requirements_file]
    if os_type == "Windows": # TODO: Check windows support
        pip_cmd.append("--upgrade")
    subprocess.check_call(pip_cmd)

    print("\n✓ All required packages are installed\n")


def main():
    """Main build process"""
    print("CSEL Build Script")
    print("=" * 60)

    # Verify we're in the project root
    if not os.path.exists("src/configurator.py"):
        print("ERROR: Must run from project root directory")
        sys.exit(1)

    # Verify virtual environment is active to isolate dependencies
    if not hasattr(sys, "real_prefix") and not (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    ):
        print("\nWARNING: Virtual environment may not be activated")
        print("Consider running: source .venv/bin/activate")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != "y":
            sys.exit(0)

    try:
        # Clean previous builds
        clean_build()

        # Install required packages
        response = input("Run automatic setup and verification of required dependencies? (Recommended if not done before) (y/N): ")
        if response.lower() == "y":
            check_requirements()
        elif response.lower() != "n":
            print("Invalid input. Exiting.")
            sys.exit(1)
        else:
            print("Skipping dependency check. Ensure all dependencies are installed...\n")

        # Build both binaries
        result1 = build_configurator()
        result2 = build_scoring_engine()

        if result1 == 0 and result2 == 0:
            print("\n" + "=" * 60)
            print("✓ Build completed successfully!")
            print("=" * 60)
            print("\nBinaries location:")
            print("  dist/configurator")
            print("  dist/scoring_engine")
            print("\nNext steps:")
            print("  1. Test binaries: sudo -E dist/configurator")
            print("  2. Run install script: sudo scripts/install.sh")
        else:
            print("\n✗ Build failed with errors")
            sys.exit(1)

    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nBuild interrupted by user")
        sys.exit(130)


if __name__ == "__main__":
    main()
