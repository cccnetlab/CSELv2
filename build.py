#!/usr/bin/env python3

"""
Build script for CSEL using PyInstaller
Compiles configurator and scoring_engine with proper asset bundling
"""

import os
import sys
import subprocess
import shutil


def clean_build():
    """Remove previous build artifacts"""
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
    """Build configurator binary with PyInstaller"""
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
    """Build scoring_engine binary with PyInstaller"""
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


def main():
    """Main build process"""
    print("CSEL Build Script")
    print("=" * 60)

    # Verify we're in the project root
    if not os.path.exists("src/configurator.py"):
        print("ERROR: Must run from project root directory")
        sys.exit(1)

    # Verify virtual environment is active
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
