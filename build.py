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

    # Remove spec files from 
    for spec_file in ["configurator.spec", "scoring_engine.spec"]:
        if os.path.exists(spec_file):
            os.remove(spec_file)
            print(f"  Removed {spec_file}")

def build_configurator():
    """
    Build configurator binary with PyInstaller
    """

    print("\n" + "=" * 60)
    print("\nBuilding configurator...")
    print("\n" + "=" * 60)

    # Use venv's pyinstaller if it exists, otherwise use system pyinstaller
    venv_pyinstaller = os.path.join(os.path.dirname(__file__), ".venv", "bin", "pyinstaller")
    pyinstaller_cmd = venv_pyinstaller if os.path.exists(venv_pyinstaller) else "pyinstaller"

    cmd = [
        pyinstaller_cmd,
        "--onefile",
        "--name=configurator_DO_NOT_TOUCH",
        "--distpath=dist",
        "--add-data=assets/icons:assets/icons",
        "--add-data=dist/scoring_engine_DO_NOT_TOUCH:dist",
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
    print("\n" + "=" * 60)

    # Use venv's pyinstaller if it exists, otherwise use system pyinstaller
    venv_pyinstaller = os.path.join(os.path.dirname(__file__), ".venv", "bin", "pyinstaller")
    pyinstaller_cmd = venv_pyinstaller if os.path.exists(venv_pyinstaller) else "pyinstaller"

    cmd = [
        pyinstaller_cmd,
        "--onefile",
        "--name=scoring_engine_DO_NOT_TOUCH",
        "--distpath=dist",
        "--add-data=src/db_handler.py:src",
        "--add-data=src/admin_test.py:src",
        "--hidden-import=lsb_release",
        "src/scoring_engine.py",
    ]

    print("Command:", " ".join(cmd))
    result = subprocess.run(cmd, check=True)

    if result.returncode == 0:
        print("\n✓ Scoring engine built successfully: dist/scoring_engine")
    return result.returncode

# def ensure_crontab_entry():
#     """
#     Ensure a specific crontab entry exists for the scoring_engine on startup. If not, add it.
#     """

#     print("\n" + "=" * 60)
#     print("\nChecking for crontab entry...")
#     print("\n" + "=" * 60)

#     cron_line = "@reboot dist/scoring_engine_DO_NOT_TOUCH"  # Run at startup
#     try:
#         # Get current root crontab
#         result = subprocess.run(["crontab", "-l", "-u", "root"], capture_output=True, text=True)
#         current_crontab = result.stdout if result.returncode == 0 else ""

#         # Check if the @reboot scoring_engine entry exists
#         if "scoring_engine_DO_NOT_TOUCH" in current_crontab and "@reboot" in current_crontab:
#             print("Crontab @reboot entry already exists.")
#             return

#         # Add the new entry
#         new_crontab = current_crontab.rstrip() + "\n" + cron_line + "\n"
#         proc = subprocess.run(["crontab", "-", "-u", "root"], input=new_crontab, text=True)
#         if proc.returncode == 0:
#             print("✓ Crontab entry added successfully.")
#         else:
#             raise Exception("Failed to add crontab entry.")
#     except Exception as e:
#         print(f"Error managing crontab: {e}")
#         sys.exit(1)

# def setup_cyberpatriot_directory(project_root="."):
#     """
#     Ensure /etc/CYBERPATRIOT_DO_NOT_REMOVE exists and copy icons there.

#     Args:
#         project_root (str): Root directory of the project(build.py should run in root by default).
#     """

#     print("\n" + "=" * 60)
#     print("\nChecking for CYBER assets directory...")
#     print("\n" + "=" * 60)

#     target_dir = "/etc/CYBERPATRIOT_DO_NOT_REMOVE" # Directory to store icons and score file
#     icons = [
#         "logo.png",
#         "CCC_logo.png",
#         "SoCalCCCC.png"
#     ]
#     icons_src_dir = os.path.join(project_root, "assets", "icons") # Source directory for icons

#     # Create directory and copy icons if it doesn't exist
#     if not os.path.isdir(target_dir):
#         print('Creating /etc/CYBERPATRIOT directory for icons...')
#         os.makedirs(target_dir, exist_ok=True) # Create the directory

#         # Copy icons one by one
#         for icon in icons:
#             src = os.path.join(icons_src_dir, icon)
#             dist = os.path.join(target_dir, icon)
#             shutil.copyfile(src, dist)
#         open(os.path.join(target_dir, "score.txt"), "a").close()  # Create score.txt
#         print("✓ CYBER directory and assets created successfully.")
#     else:
#         print("CYBER directory already exists. Skipping creation.")


def main():
    """
    Main build process
    """
    
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
        response = input("Clean previous builds? (Y/n): ")
        if response.lower() in ["", "y"]:
            clean_build()

        # Remind about dependencies
        print("\nNote: Ensure dependencies are installed by running:")
        print("  bash dep_install.sh")
        print("")
        response = input("Have you run dep_install.sh? (Y/n): ")
        if response.lower() == "n":
            print("\nPlease run 'bash dep_install.sh' first to install all dependencies.")
            sys.exit(0)

        # Build both binaries
        response = input("Build scoring_engine? (Y/n): ")
        if response.lower() in ["", "y"]:
            result1 = build_scoring_engine()
        else:
            print("Skipping scoring_engine build.")
            result1 = 0
        # response = input("Build configurator? (Y/n): ")
        # if response.lower() in ["", "y"]:
        #     result1 = build_configurator()
        # else:
        #     print("Skipping configurator build.")
        #     result1 = 0


        # # Check and install scoring_engine Cronjob as well as the CYBER directory for assets.
        # ensure_crontab_entry()

        # TODO: Create a symbolic link in /usr/local/bin or use systemctl to manage service instead of crontab
        # TODO: Migrate and cotinue consolidating install.sh

        if result1 == 0:
            print("\n" + "=" * 60)
            print("✓ Build and configuration completed/skipped successfully!")
            print("=" * 60)
            print("\nBinaries location:")
            print("/dist")
            print("\nNext steps:")
            print("  1. Install scoring engine as service: sudo python3 setup/setup_service.py")
            print("  2. Run configurator: sudo -E dist/configurator_DO_NOT_TOUCH")
            print("  3. For scoring, only the scoring engine needs to run continuously after the configurator is used to set vulnerabilities.")
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
