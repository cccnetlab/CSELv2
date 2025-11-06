#!/usr/bin/env python3

"""
Setup scoring_engine to run as a systemd service on startup. Creates a symbolic link to the /usr/local/bin directory.
"""

import os
import sys
import shutil
import subprocess

def launch_binaries(service_name="scoring_engine"):
    """
    Launch the configurator and start the service.

    Args:
        service_name (str): Name of the systemd service to start.
    """

    # Launch the binaries
    try:
        PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
        configurator_path = os.path.join(PROJECT_ROOT, "dist", "configurator_DO_NOT_TOUCH")
        print(f"\nLaunching configurator for one-time setup...")
        
        # Run configurator, use '-E' to preserve the environment for the GUI.
        subprocess.run(["sudo", "-E", configurator_path], check=True)
        
        print("✓ Configurator finished.")
    except Exception as e:
        print(f"Configurator launch failed (this may be OK if already configured): {e}")

    # --- Optional: Start the Service ---
    try:
        print(f"\nStarting the scoring engine service via systemctl...")
        
        # Tell systemd to start the service, don't run it yourself.
        subprocess.run(["systemctl", "start", service_name], check=True)
        
        print("✓ Service started successfully.")
        print(f"Check status with: sudo systemctl status {service_name}")
    except Exception as e:
        print(f"Failed to start service: {e}")

def setup_cyberpatriot_assets(project_root):
    """
    Ensure /etc/CYBERPATRIOT_DO_NOT_REMOVE exists, copy icons, and create score file.

    Args:
        project_root (str): Path to the project root directory.

    Returns:
        None
    """
    target_dir = "/etc/CYBERPATRIOT_DO_NOT_REMOVE"
    icons = [
        "logo.png",
        "iguana.png",
        "CCC_logo.png",
        "SoCalCCCC.png"
    ]
    icons_src_dir = os.path.join(project_root, "assets", "icons")

    if not os.path.isdir(target_dir):
        print("Creating /etc/CYBERPATRIOT_DO_NOT_REMOVE directory for icons...")
        os.makedirs(target_dir, exist_ok=True)
        for icon in icons:
            src = os.path.join(icons_src_dir, icon)
            dst = os.path.join(target_dir, icon)
            shutil.copyfile(src, dst)
            print(f"Copied {icon} to {target_dir}")
        open(os.path.join(target_dir, "score"), "a").close()  # touch score file

        # Launch the configurator binary
        configurator_bin = os.path.join(project_root, "dist", "configurator")
        if os.path.exists(configurator_bin):
            print("Launching configurator for one-time setup...")
            subprocess.run([configurator_bin])
        else:
            print(f"Configurator binary not found at {configurator_bin}")

        sys.exit(1)

def main():
    # Get project root, which is this script's root directory
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

    # Check for root privileges
    if os.geteuid() != 0:
        print("This script must be run as root.")
        print("Please run with: sudo python3 setup_service.py")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("\nSetting up scoring_engine as a systemd service...")
    print("\n" + "=" * 60)

    # Set pathnames for service file and binary
    target_path = "/usr/local/bin/scoring_engine_DO_NOT_TOUCH"
    source_path = os.path.join(PROJECT_ROOT, "dist", "scoring_engine_DO_NOT_TOUCH")

    # Create symbolic link to /usr/local/bin
    try:
        # If symlink already exists, remove it to ensure it's not broken
        if os.path.lexists(target_path): # Use lexists to check symlink itself
            os.remove(target_path)
            
        os.symlink(source_path, target_path) # Create fresh symlink
        print(f"✓ Created/Updated symbolic link: {target_path}")
    except Exception as e:
        print(f"ERROR: Failed to create symbolic link: {e}")
        sys.exit(1)

    # Configure systemd service file
    service_name = "scoring_engine"
    service_file_path = f"/etc/systemd/system/{service_name}.service"
    description = "CSEL Scoring Engine Service"
    working_dir = "/usr/local/bin" # TODO: Change this for relative pathing in configurator

    # The content of the .service file
    service_content = f"""
    [Unit]
    Description={description}
    After=network.target

    [Service]
    ExecStart={target_path}
    WorkingDirectory={working_dir}
    Restart=on-failure

    # Optional: Run as a specific user
    # User=myuser

    [Install]
    WantedBy=multi-user.target
    """

    # Attempt to create the service file
    try:
        print(f"Creating service file at: {service_file_path}")
        with open(service_file_path, "w") as f:
            f.write(service_content)
        print("Successfully created service file.")
        
    except IOError as e:
        print(f"Error writing service file: {e}")
        sys.exit(1)
        
    # Reload and enable the service
    try:
        print("Reloading systemd daemon...")
        subprocess.run(["systemctl", "daemon-reload"], check=True) # check=True will raise an error if the command fails
        print("Successfully reloaded daemon.")
        
        print(f"Enabling service: {service_name}.service")
        subprocess.run(["systemctl", "enable", f"{service_name}.service"], check=True) # check=True again
        print("Successfully enabled service.")
        
        print(f"You can now start your service with: sudo systemctl start {service_name}")
        
    except subprocess.CalledProcessError as e:
        print(f"A system command failed: {e}")
        print("Please check the service file content and system permissions.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    # Setup CyberPatriot assets if not already present
    setup_cyberpatriot_assets(PROJECT_ROOT)

    # Finally, launch the binaries
    response = input("\nWould you like to launch the binaries now? (y/N): ")
    if response.lower() != 'y':
        print("Setup complete. You can launch the binaries later.")
        sys.exit(0)
    else:
        launch_binaries()

if __name__ == "__main__":
    main()