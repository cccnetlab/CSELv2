#!/usr/bin/env python3

"""
This is the main scoring engine script for CSEL.
"""

import socket
import sys
import traceback
import os
import subprocess
import re
import time
import datetime
from inspect import getfullargspec
from tkinter import messagebox
import pwd, grp
#import lsb_release
import platform
import configparser
from pwd import getpwnam
import shutil
import warnings
import json
from inotify_simple import INotify, flags
from pathlib import Path
import xdg.BaseDirectory as xdg_base

# Add parent directory to path for relative imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import admin_test
from src import db_handler
from src import pamtester

def ostype() -> str:
    """
    Detect whether the current OS is Ubuntu or Linux Mint.
    Returns 'ubuntu', 'linuxmint', or the raw ID string if neither is matched.
    Raises EnvironmentError if the OS cannot be determined.
    """
    os_release = "/etc/os-release"
    if os.path.isfile(os_release):
        with open(os_release) as f:
            info = {}
            for line in f:
                line = line.strip()
                if "=" in line:
                    k, v = line.split("=", 1)
                    info[k] = v.strip('"').strip("'")
        detected = info.get("ID", "").lower()
    else:
        result = subprocess.run(
            ["lsb_release", "-si"],
            capture_output=True, text=True
        )
        detected = result.stdout.strip().lower()

    if detected in ("ubuntu", "linuxmint"):
        return detected
    elif detected:
        print(f"Warning: Unrecognized OS type '{detected}', proceeding with caution.")
        return detected
    else:
        raise EnvironmentError("Could not determine the OS type.")

# Detect OS immediately on startup — available globally as OSTYPE
OSTYPE = ostype()

### DEVELOPER TOOL ###
""" 
Set to True to enable developer mode features, 
will refresh database to match configurator updates on every iteration, 
so you can have the scoring engine running while commiting configurations.
"""
developerMode = False
########################

# Global flag to track if completion notification has been sent
completion_notification_sent = False

# ── Local policy inotify cache ────────────────────────────────────────────────
# Stores hit/miss/penalty results from local_policies() so the checks only
# re-run when /etc/pam.d, /etc/security, or /etc/login.defs actually change.
local_policy_cache: dict = {
    # Each entry: ('hit', name, points) | ('miss', name) | ('penalty', name, points)
    'events': [],
    'populated': False,  # True once the cache has been filled at least once
}
# Set True by the main loop when no policy file changes were detected and the
# cache is already populated — tells local_policies() to replay instead of re-run.
_local_policy_cache_valid: bool = False
# Set True only during an active (non-replay) local_policies() run so that
# record_hit / record_miss / record_penalty can store results into the cache.
_capturing_policy_events: bool = False
# ─────────────────────────────────────────────────────────────────────────────

# ── SSH config inotify cache ──────────────────────────────────────────────────
# Stores the PermitRootLogin check result so it only re-checks when sshd_config
# actually changes.
ssh_config_cache: dict = {
    'permit_root_login': None,  # None | 'found' | 'not_found'
    'permit_root_login_value': None,  # The actual value if found
    'populated': False,  # True once the cache has been filled at least once
}
# Set True by the main loop when no sshd_config changes were detected and the
# cache is already populated — tells check_ssh_permit_root_login() to use cache.
_ssh_config_cache_valid: bool = False
# ─────────────────────────────────────────────────────────────────────────────

# Path for storing password requirement configuration timestamps
TIMESTAMP_FILE = "/etc/CYBERPATRIOT/password_config_timestamps.json"

# Absolute file:// URI for the logo, resolved from assets/icons/logo.png relative to this repo
ICONS_URI = "file://" + str(Path(__file__).resolve().parent.parent / "assets" / "icons")


def load_config_timestamps():
    """
    Load password configuration timestamps from file.
    
    Returns:
        dict: Dictionary mapping usernames to their requirement configuration timestamps.
              Format: {username: {'timestamp': 'YYYY-MM-DD HH:MM:SS', 'requirements': {...}}}
    """
    try:
        if os.path.exists(TIMESTAMP_FILE):
            with open(TIMESTAMP_FILE, 'r') as f:
                return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load timestamp file: {e}")
    return {}


def save_config_timestamps(timestamps):
    """
    Save password configuration timestamps to file.
    
    Args:
        timestamps (dict): Dictionary mapping usernames to their timestamps.
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(TIMESTAMP_FILE), exist_ok=True)
        with open(TIMESTAMP_FILE, 'w') as f:
            json.dump(timestamps, f, indent=2)
    except IOError as e:
        print(f"Warning: Could not save timestamp file: {e}")


# check
# Scoring Report creation
def draw_head():
    """
    Creates the header of the scoring report HTML file.
    Writes to a temporary file (scoreIndex + ".tmp") so the public-facing
    scoreIndex is never overwritten until draw_tail() has a fully-scored,
    placeholder-free report ready to swap in atomically.
    """
    score_dir = os.path.dirname(scoreIndex)
    if not os.path.exists(score_dir):
        os.makedirs(score_dir, exist_ok=True)

    with open(scoreIndex + ".tmp", "w+") as file:
        file.write(
            '<!doctype html><html><head><title>CSEL Score Report</title><meta http-equiv="refresh" content="60"></head><body style="background-color:powderblue;">'
            "\n"
        )
        file.write(
            '<table align="center" cellpadding="10"><tr><td><img src="' + ICONS_URI + "/logo.png" + '"></td><td><div align="center"><H2>Cyberpatriot Scoring Engine:Linux v1.1</H2></div></td><td><img src="' + ICONS_URI + "/SoCalCCCC.png" + '"></td></tr></table><br><H2>Your Score: #TotalScore#/'
            + str(menuSettings["Tally Points"])
            + "</H2><H2>Vulnerabilities: #TotalVuln#/"
            + str(menuSettings["Tally Vulnerabilities"])
            + "</H2><hr>"
        )


def record_hit(name, points):
    """
    Records a successful scoring event.
    
    Args:
        name (str): The name of the scoring event.
        points (int): The points awarded for the event.
    """
    global total_points, total_vulnerabilities
    if _capturing_policy_events:
        local_policy_cache['events'].append(('hit', name, int(points)))
    write_to_html(
        ('<p style="color:green">' + name + " (" + str(points) + " points)</p>")
    )
    total_points += int(points)
    total_vulnerabilities += 1


def record_miss(name):
    """
    Records a missed scoring event.
    
    Args:
        name (str): The name of the missed scoring event.
    """
    if _capturing_policy_events:
        local_policy_cache['events'].append(('miss', name))
    if not menuSettings["Silent Mode"]:
        write_to_html(('<p style="color:red">MISS ' + name + " Issue</p>"))


def record_penalty(name, points):
    """
    Records a penalty event, deducting points.
    
    Args:
        name (str): The name of the penalty event.
        points (int): The points to deduct for the penalty.
    """
    global total_points
    if _capturing_policy_events:
        local_policy_cache['events'].append(('penalty', name, int(points)))
    write_to_html(
        ('<p style="color:red">' + name + " (" + str(points) + " points)</p>")
    )
    total_points -= int(points)


def display_html_sh(path):
    """
    For Ubuntu: copies ScoreReport.html directly to the user's Desktop.
    For other distros: creates a ScoringReport.desktop launcher on the Desktop.

    Args:
        path (str): The path to the user's desktop directory (trailing slash).
    """
    # Ensure the Desktop directory exists
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

    if OSTYPE == "ubuntu":
        src = "/var/www/CYBERPATRIOT/ScoreReport.html"
        dst = path + "ScoreReport.html"
        if os.path.exists(src):
            shutil.copy2(src, dst)
    else:
        with open(path + "ScoringReport.desktop", "w") as dt_f:
            dt_f.write(
                """[Desktop Entry]
Name = Scoring Report
Exec = xdg-open /var/www/CYBERPATRIOT/ScoreReport.html
Icon = /var/www/CYBERPATRIOT/ScoringEngineLinuxBig.png
Type = Application
Categories = Development;HTML;
Terminal = false"""
            )
        actual_user, _ = get_actual_user_info()
        subprocess.run(
            ["sudo", "-u", actual_user, "gio", "set",
             path + "ScoringReport.desktop", "metadata::trusted", "true"],
            check=False
        )


def draw_tail():
    """
    Completes the scoring report HTML file by adding the footer content.
    Resolves #TotalScore# and #TotalVuln# placeholders in the temp file,
    then atomically renames it over scoreIndex so the public-facing report
    is only ever replaced with a fully-scored, complete page.
    Sets permissions and ownership for the score index file.
    """
    write_to_html('<hr><div align="center"><b>Coastline College</b>')
    tmp = scoreIndex + ".tmp"
    replace_section(tmp, "#TotalScore#", str(total_points))
    replace_section(tmp, "#TotalVuln#", str(total_vulnerabilities))
    # Atomically swap the finished temp file into place
    os.replace(tmp, scoreIndex)
    actual_user, actual_uid = get_actual_user_info()
    os.chmod(scoreIndex, 0o777)
    os.chown(scoreIndex, actual_uid, actual_uid)
    # shutil.copy('/var/www/CYBERPATRIOT/ScoreReport.html', '/home/' + actual_user + '/Desktop/')
    # os.chown('/home/' + actual_user + '/Desktop/ScoreReport.html', actual_uid, actual_uid)
    display_html_sh("/home/" + actual_user + "/Desktop/")
    if OSTYPE == "ubuntu":
        desktop_file = "/home/" + actual_user + "/Desktop/ScoreReport.html"
    else:
        desktop_file = "/home/" + actual_user + "/Desktop/ScoringReport.desktop"
    if os.path.exists(desktop_file):
        os.chown(desktop_file, actual_uid, actual_uid)
        os.chmod(desktop_file, 0o770)


def initialize_score_report():
    """
    Creates/resets the ScoreReport.html with initial state (0 points/0 vulnerabilities).
    Called when configurator commits to show updated totals immediately.
    This creates a fresh HTML file that will be populated by the scoring engine.
    """
    # Get the latest settings from database
    settings_obj = db_handler.Settings()
    current_settings = settings_obj.get_settings(False)
    
    # Create the score report file path
    score_index_path = "/var/www/CYBERPATRIOT/ScoreReport.html"
    
    # Ensure the directory exists
    score_dir = os.path.dirname(score_index_path)
    if not os.path.exists(score_dir):
        os.makedirs(score_dir, exist_ok=True)
    
    # Create the HTML file with updated totals
    with open(score_index_path, "w+") as file:
        file.write(
            '<!doctype html><html><head><title>CSEL Score Report</title><meta http-equiv="refresh" content="60"></head><body style="background-color:powderblue;">'
            "\n"
        )
        file.write(
            '<table align="center" cellpadding="10"><tr><td><img src="' + LOGO_URI + '"></td><td><div align="center"><H2>Cyberpatriot Scoring Engine:Linux v1.1</H2></div></td><td><img src="' + ICONS_URI + "/SoCalCCCC.png" + '"></td></tr></table><br><H2>Your Score: 0/'
            + str(current_settings["Tally Points"])
            + "</H2><H2>Vulnerabilities: 0/"
            + str(current_settings["Tally Vulnerabilities"])
            + "</H2><hr>"
        )
        file.write(
            '<p style="color:blue;">Configuration updated. Scoring engine will begin checking vulnerabilities shortly...</p>'
        )
        file.write('<hr><div align="center"><b>Coastline College</b></div></body></html>')
    
    # Set proper permissions and ownership
    actual_user, actual_uid = get_actual_user_info()
    os.chmod(score_index_path, 0o777)
    os.chown(score_index_path, actual_uid, actual_uid)

    # Ensure desktop icon exists
    display_html_sh("/home/" + actual_user + "/Desktop/")
    if OSTYPE == "ubuntu":
        desktop_file = "/home/" + actual_user + "/Desktop/ScoreReport.html"
    else:
        desktop_file = "/home/" + actual_user + "/Desktop/ScoringReport.desktop"
    if os.path.exists(desktop_file):
        os.chown(desktop_file, actual_uid, actual_uid)
        os.chmod(desktop_file, 0o770)


# Extra Functions
def get_actual_user_info():
    """
    Resolves the real (non-root) user and their UID regardless of how the
    process was launched — via `sudo`, directly as root, or as a systemd service.

    Priority:
      1. ACTUAL_USER / ACTUAL_UID   (set by service_setup.py in the unit file)
      2. SUDO_USER  / SUDO_UID      (set by sudo when run manually)
      3. First human user found under /home with a valid UID >= 1000 (fallback)

    Returns:
        tuple[str, int]: (username, uid) of the actual user, or ("root", 0) if
                         none can be determined.
    """
    user = os.environ.get("ACTUAL_USER") or os.environ.get("SUDO_USER")
    uid_str = os.environ.get("ACTUAL_UID") or os.environ.get("SUDO_UID")

    if user and uid_str:
        try:
            return user, int(uid_str)
        except ValueError:
            pass

    # Fallback: walk /home and find first real user (UID >= 1000)
    if user:
        try:
            return user, pwd.getpwnam(user).pw_uid
        except KeyError:
            pass

    try:
        for entry in os.scandir("/home"):
            if entry.is_dir():
                try:
                    info = pwd.getpwnam(entry.name)
                    if info.pw_uid >= 1000:
                        print(f"WARNING: Falling back to /home user '{entry.name}' for file ownership.")
                        return entry.name, info.pw_uid
                except KeyError:
                    pass
    except OSError:
        pass

    print("WARNING: Could not determine actual user — file ownership will default to root.")
    return "root", 0


def check_runas():
    """
    Checks if the script is running with administrator privileges.
    If not, prompts the user to run as admin and exits.
    """
    if not admin_test.isUserAdmin():
        print("ERROR: Administrator Access Needed - Please make sure the scoring engine is running as admin.")
        exit(admin_test.runAsAdmin())


def check_score():
    global total_points, total_vulnerabilities, completion_notification_sent
    
    menuSettings["Current Vulnerabilities"] = total_vulnerabilities
    
    def send_notification(message):
        """Send notification as the actual user using sudo"""
        actual_user = os.environ.get("ACTUAL_USER")
        actual_uid = os.environ.get("ACTUAL_UID")
        
        if not actual_user or not actual_uid:
            # Fallback to SUDO_USER if ACTUAL_USER not set (running directly with sudo)
            actual_user = os.environ.get("SUDO_USER")
            if actual_user:
                try:
                    actual_uid = str(getpwnam(actual_user).pw_uid)
                except:
                    print("Warning: Cannot send notification - user info not available")
                    return
            else:
                print("Warning: Cannot send notification - user info not available")
                return
        
        try:            
            # Run notify-send as the actual user
            if(OSTYPE == "ubuntu"):
                subprocess.run([
                    "sudo", "-u", actual_user,
                    "env",
                    f"DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{actual_uid}/bus",
                    f"DISPLAY=:0",
                    f"XDG_RUNTIME_DIR=/run/user/{actual_uid}",
                    "notify-send",
                    "-i", "utilities-terminal",
                    "CyberPatriot",
                    message],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                # Set up environment for the user's D-Bus session
                env = os.environ.copy()
                env["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path=/run/user/{actual_uid}/bus"
                env["DISPLAY"] = ":0"
                env["XDG_RUNTIME_DIR"] = f"/run/user/{actual_uid}"
                subprocess.run(
                    ["sudo", "-u", actual_user, "notify-send", 
                    "-i", "utilities-terminal", 
                    "CyberPatriot", 
                    message],
                    env=env,
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except Exception as e:
            print(f"Notification failed: {e}")
    
    if total_points > menuSettings["Current Points"]:
        menuSettings["Current Points"] = total_points
        Settings.update_score(menuSettings)
        send_notification("You've gained points!")
        
    elif total_points < menuSettings["Current Points"]:
        menuSettings["Current Points"] = total_points
        Settings.update_score(menuSettings)
        send_notification("You've lost points!")
        # Reset completion notification if points are lost
        completion_notification_sent = False
        
    if (total_points == menuSettings["Tally Points"] and 
        total_vulnerabilities == menuSettings["Tally Vulnerabilities"]):
        # Only send notification if it hasn't been sent yet
        if not completion_notification_sent:
            send_notification("You've completed the image!")
            completion_notification_sent = True


def write_to_html(message):
    """
    Appends a message to the in-progress scoring report temp file.
    The temp file is atomically renamed to scoreIndex by draw_tail() once
    all scoring is complete and placeholders have been resolved.

    Args:
        message (str): The message to write to the HTML file.
    """
    with open(scoreIndex + ".tmp", "a") as file:
        file.write(message)


def replace_section(loc, search, replace):
    """
    Replaces a specific section in the scoring report HTML file.
    
    Args:
        loc (str): The location of the HTML file.
        search (str): The text to search for in the file.
        replace (str): The text to replace the searched text with.
    """
    lines = []
    with open(loc) as file:
        for line in file:
            line = line.replace(search, replace)
            lines.append(line)
    with open(loc, "w") as file:
        for line in lines:
            file.write(line)


# Option Check
def forensic_question(vulnerability):
    """
    Checks if forensic questions have been answered correctly.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    for idx, vuln in enumerate(vulnerability):
        if vuln != 1:
            location = vulnerability[vuln]["Location"]
            
            # Skip if location is empty or not configured
            if not location or not location.strip():
                continue
            
            # Skip if file doesn't exist
            if not os.path.exists(location):
                record_miss("File Management")
                continue
                
            try:
                file = open(location, "r")
                content = file.read().splitlines()
                file.close()
                
                for c in content:
                    if "ANSWER:" in c:
                        if vulnerability[vuln]["Answers"] in c:
                            record_hit(
                                "Forensic question number "
                                + str(idx)
                                + " has been answered.",
                                vulnerability[vuln]["Points"],
                            )
                        else:
                            record_miss("File Management")
                        break
                else:
                    # No "ANSWER:" line found in file
                    record_miss("File Management")
            except (IOError, PermissionError) as e:
                print(f"Warning: Could not read forensic file {location}: {e}")
                record_miss("File Management")


def critical_users(vulnerability):
    """
    Checks for critical users and records penalties if they are removed.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    users = pwd.getpwall()
    user_list = []
    for user in users:
        user_list.append(user.pw_name)
    for vuln in vulnerability:
        if vuln != 1:
            if vulnerability[vuln]["User Name"] not in user_list:
                record_penalty(
                    vulnerability[vuln]["User Name"] + " was removed.",
                    vulnerability[vuln]["Points"],
                )


def users_manipulation(vulnerability, name):
    """
    Checks for user manipulation actions (add/remove) and records hits/misses.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
        name (str): The action being checked (Add User or Remove User).
    """
    users = grp.getgrall()
    user_list = []
    for user in users:
        user_list.append(user[0])
    
    match name:
        case "Add User":
            for vuln in vulnerability:
                if vuln != 1:
                    if vulnerability[vuln]["User Name"] in user_list:
                        record_hit(
                            vulnerability[vuln]["User Name"] + " has been added.",
                            vulnerability[vuln]["Points"],
                        )
                    else:
                        record_miss("Account Management")
        case "Remove User":
            for vuln in vulnerability:
                if vuln != 1:
                    if vulnerability[vuln]["User Name"] not in user_list:
                        record_hit(
                            vulnerability[vuln]["User Name"] + " has been removed.",
                            vulnerability[vuln]["Points"],
                        )
                    else:
                        record_miss("Account Management")


def firewallVulns(vulnerability, name):
    """
    Checks the status of the firewall and records hits/misses based on its state.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
        name (str): The name of the vulnerability being checked.
    """
    try:
        # Run the ufw status command and capture the output
        completed_process = subprocess.run(
            ["sudo", "ufw", "status"], capture_output=True, text=True, check=True
        )
        if " active" in completed_process.stdout.strip():
            record_hit("Firewall has been turned on.", vulnerability[1]["Points"])
        else:
            record_miss("Firewall Management")
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"


def check_tcp(host, port):
    """
    Checks if a TCP port is open on a given host.
    
    Args:
        host (str): The hostname or IP address to check.
        port (int): The TCP port number to check.
    
    Returns:
        bool: True if the port is open, False otherwise.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)  # Set a timeout for the connection attempt
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0


def check_udp(host, port):
    """
    Checks if a UDP port has a listening process.
    
    UDP is connectionless, so we cannot reliably test connectivity by sending packets.
    Instead, we check if any process is actually listening on the port using ss/netstat.
    This is more reliable than trying to send empty packets which most services ignore.
    
    Args:
        host (str): The hostname or IP address to check (used for filtering).
        port (int): The UDP port number to check.
    
    Returns:
        bool: True if a process is listening on the port, False otherwise.
    """
    try:
        # Use ss to check if any process is listening on this UDP port
        result = subprocess.run(
            ["ss", "-ulnp"],  # -u=UDP, -l=listening, -n=numeric, -p=processes
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse output looking for the port
        # Format: "udp   UNCONN 0   0   127.0.0.53:53   0.0.0.0:*   users:..."
        for line in result.stdout.split('\n'):
            # Skip header and empty lines
            if not line.strip() or line.startswith('State') or line.startswith('Netid'):
                continue
            
            # Check if this line contains our port
            # Look for patterns like "0.0.0.0:53", "127.0.0.1:53", "[::]:53", etc.
            if f":{port}" in line or f":{port} " in line:
                # Additional check: if a specific host was requested (not 0.0.0.0 or ::)
                # verify it matches (but accept 0.0.0.0 and :: as wildcards)
                if host not in ["0.0.0.0", "127.0.0.1", "::", "::1"]:
                    # If specific host requested, check if line contains it
                    if host not in line:
                        continue
                return True
        
        return False
        
    except subprocess.CalledProcessError:
        # If ss command fails, fall back to socket method
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1)
        try:
            sock.sendto(b"", (host, port))
            data, addr = sock.recvfrom(1024)
            sock.close()
            return True
        except socket.timeout:
            sock.close()
            return False
        except Exception:
            sock.close()
            return False


def check_ufw_rule(port, protocol):
    """
    Checks UFW firewall rules to determine if a port is allowed or denied.
    Checks for both protocol-specific rules (e.g., "53/tcp") and generic port rules (e.g., "53").
    
    Args:
        port (int): The port number to check.
        protocol (str): The protocol ("TCP" or "UDP").
    
    Returns:
        str: "ALLOW" if port is explicitly allowed, "DENY" if explicitly denied,
             "DEFAULT" if no specific rule exists (falls back to UFW default policy).
    """
    try:
        # Run 'ufw status numbered' to get detailed rules
        result = subprocess.run(
            ["sudo", "ufw", "status", "numbered"],
            capture_output=True,
            text=True,
            check=True
        )
        
        output = result.stdout.lower()
        protocol_lower = protocol.lower()
        
        # Parse UFW rules looking for port/protocol matches
        # UFW output format examples:
        # "[ 1] 22/tcp                     ALLOW IN    Anywhere"
        # "[ 2] 53                         ALLOW IN    Anywhere"  (applies to both tcp and udp)
        for line in output.split('\n'):
            # Skip header lines and empty lines
            if not line.strip() or 'status:' in line or '---' in line or 'to' in line.lower() and 'action' in line.lower():
                continue
            
            # Check for protocol-specific rule (e.g., "53/tcp")
            if f"{port}/{protocol_lower}" in line:
                if "allow" in line:
                    return "ALLOW"
                elif "deny" in line or "reject" in line:
                    return "DENY"
            
            # Check for generic port rule (e.g., "53" which applies to both tcp and udp)
            # Use word boundaries to avoid matching partial port numbers (e.g., "53" shouldn't match "253")
            # Look for patterns like " 53 " or " 53/" or "[ 53]" or start with digit/bracket then port then space/slash
            import re
            port_pattern = rf'(?:^|\s|\[)\s*{port}(?:\s|$|/)'
            if re.search(port_pattern, line):
                # Make sure this isn't a port/protocol line we already checked
                if f"{port}/{protocol_lower}" not in line and f"{port}/tcp" not in line and f"{port}/udp" not in line:
                    if "allow" in line:
                        return "ALLOW"
                    elif "deny" in line or "reject" in line:
                        return "DENY"
        
        # No specific rule found, return default policy
        # If UFW is active and no rule matches, default is typically DENY
        # If UFW is inactive, we'll treat it as ALLOW
        if "status: active" in output:
            return "DEFAULT"  # Active firewall with no specific rule = default deny
        else:
            return "ALLOW"  # Inactive firewall = everything allowed
            
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not check UFW rules: {e}")
        return "ALLOW"  # If we can't check, assume allowed
    except Exception as e:
        print(f"Warning: Error checking UFW: {e}")
        return "ALLOW"


def portVulnsOld(vulnerability, name):
    """
    Checks for open or closed ports based on the provided vulnerabilities.
    Handles both TCP and UDP protocols, and supports IPv4/IPv6 addresses.
    
    A port is considered OPEN only if:
    - UFW allows the traffic (or UFW is inactive), AND
    - The port is actually listening (socket connection succeeds)
    
    A port is considered CLOSED if:
    - UFW blocks/denies the traffic, OR
    - The port is not listening
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
        name (str): The check type - "Check Port Open" or "Check Port Closed"
    """
    expect_open = (name == "Check Port Open")
    
    for vuln in vulnerability:
        if vuln != 1:
            # Get configuration values with defaults for missing fields
            protocol = vulnerability[vuln].get("Protocol", "TCP")
            host = vulnerability[vuln].get("IP", "")
            port_str = vulnerability[vuln].get("Port", "")
            program_name = vulnerability[vuln].get("Program Name", "")
            
            # Validate required fields
            if not host or not host.strip():
                print(f"Warning: Missing or empty IP for {name} vulnerability")
                record_miss("Firewall Management")
                continue
            
            if not port_str:
                print(f"Warning: Missing port for {name} vulnerability")
                record_miss("Firewall Management")
                continue
            
            try:
                port = int(port_str)
            except (ValueError, TypeError):
                print(f"Warning: Invalid port '{port_str}' for {name}")
                record_miss("Firewall Management")
                continue
            
            # Handle special IP notations
            # IPv6 localhost variants: [::], [::1], ::1, etc.
            if host.startswith("[") and host.endswith("]"):
                host = host[1:-1]  # Remove brackets: [::] -> ::
            
            # Map IPv6 localhost to IPv4 for compatibility
            if host in ["::", "::1"]:
                host = "127.0.0.1"
            
            print(f"Checking for host ip notation {host}")

            protocol_upper = str.upper(protocol)
            
            # Step 1: Check UFW firewall rules
            ufw_rule = check_ufw_rule(port, protocol_upper)
            
            # Step 2: Check if port is actually listening
            is_listening = False
            try:
                if protocol_upper == "TCP":
                    is_listening = check_tcp(host, port)
                elif protocol_upper == "UDP":
                    is_listening = check_udp(host, port)
                else:
                    print(f"Warning: Unknown protocol '{protocol}' for port check")
                    record_miss("Firewall Management")
                    continue
            except Exception as e:
                print(f"Error checking {protocol_upper} port {port} on {host}: {e}")
                record_miss("Firewall Management")
                continue
            
            # Step 3: Determine if port is truly open or closed
            # Port is OPEN if: UFW allows it AND it's listening
            # Port is CLOSED if: UFW denies it OR it's not listening
            if ufw_rule == "DENY":
                # UFW explicitly blocks this port
                is_open = False
            elif ufw_rule == "ALLOW":
                # UFW allows, check if listening
                is_open = is_listening
            else:  # ufw_rule == "DEFAULT"
                # No specific rule, UFW active means default deny
                # But if it's listening, something got through (maybe via ALLOW ALL or other rule)
                is_open = is_listening
            
            # Step 4: Determine if we should award points
            # For "Check Port Open": award if port IS open (UFW allows AND listening)
            # For "Check Port Closed": award if port IS NOT open (UFW denies OR not listening)
            should_award = (is_open == expect_open)
            
            if should_award:
                state = "open" if expect_open else "closed"
                display_name = program_name if program_name else f"Port {port}"
                record_hit(
                    f"{display_name} ({protocol_upper} port {port}) is {state}",
                    vulnerability[vuln]["Points"],
                )
            else:
                record_miss("Firewall Management")

def portVulns(vulnerability, name):
    """
    Checks open/closed port rules based solely on UFW policy.

    For "Check Port Open":
        HIT  — an explicit ALLOW rule exists for the port that covers the
               required protocol (a protocol-less rule e.g. "ALLOW 22" covers
               both TCP and UDP) and whose From is "Anywhere" or the configured IP.
        MISS — no such ALLOW rule exists.

    For "Check Port Closed":
        HIT  — no ALLOW rule exists for BOTH the IPv4 and IPv6 rule entries
               (UFW default-deny covers each, or an explicit DENY/REJECT exists).
               UFW inactive → MISS (no default-deny in effect).
        MISS — an ALLOW rule exists for the port on either IPv4 or IPv6.

    IP filtering (only when a specific IP is configured):
        A rule is considered only if its From field is "Anywhere"
        (rule applies to all sources) or exactly the configured IP.
        Empty IP / "0.0.0.0" / "::" → no IP filtering.

    Args:
        vulnerability (list): A list of vulnerabilities to check.
        name (str): "Check Port Open" or "Check Port Closed"
    """
    expect_open = (name == "Check Port Open")

    # Fetch and parse UFW rules once for all vulns in this call
    try:
        result = subprocess.run(
            ["sudo", "ufw", "status", "numbered"],
            capture_output=True, text=True, check=True
        )
        ufw_output = result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not get UFW status: {e}")
        for vuln in vulnerability:
            if vuln != 1:
                record_miss("Firewall Management")
        return
    except Exception as e:
        print(f"Warning: Unexpected error getting UFW status: {e}")
        for vuln in vulnerability:
            if vuln != 1:
                record_miss("Firewall Management")
        return

    ufw_active = "status: active" in ufw_output.lower()

    # Parse every rule line into structured dicts.
    # ufw status numbered output format (lower number = higher priority):
    #   [ 1] 22/tcp              ALLOW IN    Anywhere
    #   [ 2] 53                  ALLOW IN    Anywhere
    #   [ 3] 443/tcp             DENY IN     10.0.0.5
    #   [ 4] 22/tcp (v6)         ALLOW IN    Anywhere (v6)
    parsed_rules = []
    in_rules_section = False
    for line in ufw_output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Detect the header row
        if (stripped.lower().startswith("to")
                and "action" in stripped.lower()
                and "from" in stripped.lower()):
            in_rules_section = True
            continue
        if stripped.startswith("--"):
            continue
        if not in_rules_section:
            continue

        # Extract rule number and body from lines like "[ 1] 22/tcp  ALLOW IN  Anywhere"
        num_match = re.match(r'^\[\s*(\d+)\]\s*(.*)', stripped)
        if not num_match:
            continue
        rule_number = int(num_match.group(1))
        rule_body   = num_match.group(2)

        # Split into columns on runs of 2+ spaces
        cols = re.split(r' {2,}', rule_body)
        if len(cols) < 3:
            continue

        to_raw     = cols[0].strip()
        action_raw = cols[1].strip().lower()
        from_raw   = cols[2].strip().lower()

        # Detect IPv6 rule BEFORE stripping the annotation
        is_v6 = bool(re.search(r'\(v6\)', to_raw, re.IGNORECASE))

        # Strip IPv6 "(v6)" annotations for port/proto parsing
        to_raw   = re.sub(r'\s*\(v6\)\s*$', '', to_raw,   flags=re.IGNORECASE).strip()
        from_raw = re.sub(r'\s*\(v6\)\s*$', '', from_raw, flags=re.IGNORECASE).strip()

        # Determine action (ALLOW IN / DENY IN / REJECT IN …)
        if "allow" in action_raw:
            action = "allow"
        elif "deny" in action_raw or "reject" in action_raw:
            action = "deny"
        else:
            continue  # LIMIT and other actions are not scored

        # Parse To field: "22/tcp", "53/udp", "80", "Anywhere" …
        # Only port-targeted rules are relevant here.
        port_match = re.match(r'^(\d+)(?:/(tcp|udp))?$', to_raw, re.IGNORECASE)
        if not port_match:
            continue  # Not a port rule (e.g. "Anywhere", service name, etc.)

        rule_port  = int(port_match.group(1))
        # proto "any" means the rule has no protocol qualifier → covers both tcp and udp
        rule_proto = (port_match.group(2) or "any").lower()

        parsed_rules.append({
            'port':   rule_port,
            'proto':  rule_proto,   # "tcp" | "udp" | "any"
            'action': action,       # "allow" | "deny"
            'from':   from_raw,     # already lowercased
            'is_v6':  is_v6,        # True if rule applies to IPv6
        })

    # Score each configured vulnerability
    for vuln in vulnerability:
        if vuln != 1:
            protocol     = vulnerability[vuln].get("Protocol", "TCP").strip().lower()
            port_str     = vulnerability[vuln].get("Port", "")
            config_ip    = vulnerability[vuln].get("IP", "").strip().lower()
            program_name = vulnerability[vuln].get("Program Name", "")

            if not port_str:
                print(f"Warning: Missing port for {name}")
                record_miss("Firewall Management")
                continue

            try:
                port = int(port_str)
            except (ValueError, TypeError):
                print(f"Warning: Invalid port '{port_str}' for {name}")
                record_miss("Firewall Management")
                continue

            # IP filtering: disabled for empty / wildcard addresses
            ip_filter = config_ip not in ("", " ", "0.0.0.0", "::", "anywhere")

            def first_applicable_rule(is_v6_target):
                """
                Return the first (lowest-numbered) UFW rule that matches
                port + protocol + IP requirements for the given IP version.
                Rules are already stored in priority order from ufw status numbered output.
                """
                for r in parsed_rules:  # already in priority order — no sort needed
                    print("DEBUG: Evaluating rule:", r)
                    print(f"DEBUG: Configuration - port={port}, protocol={protocol}, ip_filter={ip_filter}, config_ip={config_ip}, is_v6_target={is_v6_target}")
                    if r['port'] != port:
                        continue
                    if r['is_v6'] != is_v6_target:
                        continue
                    # Protocol: rule proto 'any' covers both tcp and udp
                    if r['proto'] != 'any' and r['proto'] != protocol:
                        continue
                    # From: must satisfy IP requirement
                    if ip_filter:
                        # Specific IP configured — accept rules targeting that IP or Anywhere
                        if r['from'] not in ('anywhere', config_ip):
                            continue
                    else:
                        # No IP configured — only "Anywhere" rules apply
                        if r['from'] != 'anywhere':
                            continue
                    return r
                return None

            first_v4 = first_applicable_rule(False)
            # Only check v6 when no specific IP is configured; a specific IP is
            # always an IPv4 address so its UFW rule will never appear as a v6 rule.
            first_v6 = None if ip_filter else first_applicable_rule(True)

            has_v4_allow = first_v4 is not None and first_v4['action'] == 'allow'
            has_v6_allow = first_v6 is not None and first_v6['action'] == 'allow'
            has_allow    = has_v4_allow or has_v6_allow
            has_v4_deny  = first_v4 is not None and first_v4['action'] == 'deny'
            has_v6_deny  = first_v6 is not None and first_v6['action'] == 'deny'

            display_name = program_name if program_name else f"Port {port}"
            proto_label  = protocol.upper()

            if expect_open:
                # Port Open: need an explicit ALLOW rule
                if has_allow:
                    record_hit(
                        f"{display_name} ({proto_label}/{port}) is allowed by UFW",
                        vulnerability[vuln]["Points"],
                    )
                else:
                    record_miss("Firewall Management")

            else:
                # Port Closed: all applicable sides must have no ALLOW rule.
                # When an IP is specified only v4 is checked; otherwise both v4 and v6.
                if not ufw_active:
                    # UFW inactive — default deny is not in effect, can't confirm closed
                    record_miss("Firewall Management")
                elif has_v4_allow or has_v6_allow:
                    # At least one checked side still has an ALLOW rule
                    record_miss("Firewall Management")
                else:
                    if ip_filter:
                        # IP-specific check: only v4 matters
                        reason = "explicitly denied by UFW (IPv4)" if has_v4_deny else "not allowed (UFW default deny)"
                    else:
                        # No IP: both v4 and v6 checked
                        if has_v4_deny and has_v6_deny:
                            reason = "explicitly denied by UFW (IPv4 and IPv6)"
                        elif has_v4_deny:
                            reason = "explicitly denied by UFW (IPv4, IPv6 default deny)"
                        elif has_v6_deny:
                            reason = "explicitly denied by UFW (IPv6, IPv4 default deny)"
                        else:
                            reason = "not allowed (UFW default deny)"
                    record_hit(
                        f"{display_name} ({proto_label}/{port}) is closed — {reason}",
                        vulnerability[vuln]["Points"],
                    )


def audit_check():
    """
    Checks if the audit daemon is active.
    
    Returns:
        bool: True if the audit daemon is active, False otherwise.
    """
    try:
        cp = subprocess.run(
            ["systemctl", "is-active", "auditd"],
            capture_output=True,
            text=True,
            check=True,
        )
        captured = cp.stdout.strip()
        if "inactive" in captured:
            return False
        else:
            return True
    except:
        return False


# fix
def local_group_policy(vulnerability, name):
    """
    Checks local group policies and records hits/misses based on their settings.
    Uses user-specified values from the vulnerability configuration.
    First validates using /var/log/auth.log to ensure PAM configurations are valid.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
        name (str): The name of the policy being checked.
    """
    # ===== VALIDATION PHASE: Check if PAM configuration files are valid =====
    # If PAM configurations are invalid, no points should be awarded as the system
    # may not be enforcing the configured policies correctly.
    # Actively tests PAM by triggering authentication and checking the resulting log entries.
    
    try:
        auth_log_path = "/var/log/auth.log"
        
        pam_error_indicators = [
            "illegal module type",
            "unknown module type",
            "PAM unable to",
            "PAM service(",
            "PAM bad module",
            "PAM parse error",
            "PAM unknown option",
            "PAM adding faulty module",
            "PAM [error]",
            "Module is unknown",
            "failed to load module",
        ]
        
        try:
            # Step 1: Get the current line count of auth.log before our test
            with open(auth_log_path, 'r') as log_file:
                initial_lines = log_file.readlines()
                initial_line_count = len(initial_lines)
            
            # Step 2: Trigger PAM validation with a harmless command
            # Using 'sudo -n true' which:
            # - Tests sudo authentication without prompting for password (-n = non-interactive)
            # - Runs 'true' command (does nothing, always succeeds)
            # - Will fail with exit code 1 if password required, but still triggers PAM
            # - Causes PAM to process the auth stack and log any errors
            subprocess.run(
                ["sudo", "-n", "true"],
                capture_output=True,
                text=True,
                check=False  # Don't raise exception on non-zero exit (expected if password required)
            )
            
            # Give the system a moment to write to the log
            import time
            time.sleep(0.1)
            
            # Step 3: Read only the NEW lines added after our command
            with open(auth_log_path, 'r') as log_file:
                all_lines = log_file.readlines()
                new_lines = all_lines[initial_line_count:]  # Only lines added after our test
            
            # Step 4: Check the new lines for PAM errors
            for line in new_lines:
                line_lower = line.lower()
                for error_indicator in pam_error_indicators:
                    if error_indicator.lower() in line_lower:
                        print(f"WARNING: PAM configuration error detected during authentication test:")
                        print(f"  {line.strip()}")
                        print(f"No local policy points will be awarded due to invalid PAM configuration.")
                        record_miss("Local Policy")
                        return
                        
        except FileNotFoundError:
            print(f"WARNING: Could not find {auth_log_path}")
            print("Unable to validate PAM configuration. Proceeding with caution...")
            # Don't return here - allow scoring to continue if auth.log doesn't exist
        except PermissionError:
            print(f"WARNING: Permission denied reading {auth_log_path}")
            print("Unable to validate PAM configuration. Proceeding with caution...")
            # Don't return here - allow scoring to continue if we can't read the log
                    
    except Exception as e:
        print(f"WARNING: Unexpected error during PAM validation: {e}")
        print("Unable to validate PAM configuration. Proceeding with caution...")
        # Don't return here - allow scoring to continue on unexpected errors
    
    # ===== PARSING PHASE: Extract settings from valid configuration files =====
    # Create a dictionary from the list of tuples for easier lookup
    policy_settings_dict = dict(login_policy_settings_content)
    
    # Parse PAM data from common-password to extract module settings
    pam_settings_dict = {}
    for pam_line in pamd_policy_settings_content:
        # Replace literal \t with actual tabs, then split by tabs and whitespace
        normalized_line = pam_line.replace('\\t', '\t')
        # Split by both tabs and multiple spaces to handle different formatting
        parts = re.split(r'[\t\s]+', normalized_line.strip())
        parts = [p for p in parts if p]  # Remove empty strings
        
        if len(parts) >= 3:
            module_type = parts[0]  # e.g., "password"
            control = parts[1]      # e.g., "[success=1 default=ignore]"
            module_path = parts[2]  # e.g., "pam_unix.so"
            
            # Extract module options (everything after the module path)
            if len(parts) > 3:
                options = ' '.join(parts[3:])
                
                # Parse common PAM options
                if 'remember=' in options:
                    try:
                        remember_match = re.search(r'remember=(\d+)', options)
                        if remember_match:
                            pam_settings_dict['remember'] = remember_match.group(1)
                    except Exception as e:
                        print(f"Error parsing remember: {e}")
                        
                if 'unlock_time=' in options:
                    try:
                        unlock_match = re.search(r'unlock_time=(\d+)', options)
                        if unlock_match:
                            pam_settings_dict['unlock_time'] = unlock_match.group(1)
                    except Exception as e:
                        print
                if 'deny=' in options:
                    try:
                        deny_match = re.search(r'deny=(\d+)', options)
                        if deny_match:
                            pam_settings_dict['deny'] = deny_match.group(1)
                    except Exception as e:
                        print(f"Error parsing deny: {e}")
    
    # Parse PAM data from common-auth to extract faillock settings
    # Track all three faillock modules separately: preauth, authfail, authsucc
    common_auth_faillock_modules = {
        'preauth': {},
        'authfail': {},
        'authsucc': {}
    }
    common_auth_dict = {}  # Keep for backward compatibility with other checks
    
    for auth_line in common_auth_content:
        # Replace literal \t with actual tabs, then split by tabs and whitespace
        normalized_line = auth_line.replace('\\t', '\t')
        # Split by both tabs and multiple spaces to handle different formatting
        parts = re.split(r'[\t\s]+', normalized_line.strip())
        parts = [p for p in parts if p]  # Remove empty strings
        
        if len(parts) >= 3:
            module_type = parts[0]  # e.g., "auth"
            control = parts[1]      # e.g., "required"
            module_path = parts[2]  # e.g., "pam_faillock.so"
            
            # Extract module options (everything after the module path)
            if len(parts) > 3 and 'pam_faillock.so' in module_path:
                options = ' '.join(parts[3:])
                
                # Determine which faillock module this is
                module_phase = None
                if 'preauth' in options:
                    module_phase = 'preauth'
                elif 'authfail' in options:
                    module_phase = 'authfail'
                elif 'authsucc' in options:
                    module_phase = 'authsucc'
                
                # Parse faillock-specific options ADD FUTURE CONFIGURATIONS HERE
                if 'unlock_time=' in options:
                    try:
                        unlock_match = re.search(r'unlock_time=(\d+)', options)
                        if unlock_match:
                            unlock_value = unlock_match.group(1)
                            common_auth_dict['unlock_time'] = unlock_value
                            if module_phase:
                                common_auth_faillock_modules[module_phase]['unlock_time'] = unlock_value
                    except Exception as e:
                        print(f"Error parsing unlock_time from common-auth: {e}")
                        
                if 'fail_interval=' in options:
                    try:
                        fail_interval_match = re.search(r'fail_interval=(\d+)', options)
                        if fail_interval_match:
                            fail_interval_value = fail_interval_match.group(1)
                            common_auth_dict['fail_interval'] = fail_interval_value
                            if module_phase:
                                common_auth_faillock_modules[module_phase]['fail_interval'] = fail_interval_value
                    except Exception as e:
                        print(f"Error parsing fail_interval from common-auth: {e}")
                        
                if 'deny=' in options:
                    try:
                        deny_match = re.search(r'deny=(\d+)', options)
                        if deny_match:
                            deny_value = deny_match.group(1)
                            common_auth_dict['deny'] = deny_value
                            if module_phase:
                                common_auth_faillock_modules[module_phase]['deny'] = deny_value
                    except Exception as e:
                        print(f"Error parsing deny from common-auth: {e}")
    
    # Attempts to match the policy name and check its value, then records hits/misses
    try:
        match name:
            case "Minimum Password Age":
                # Get the expected value from configuration
                try:
                    expected_value = int(vulnerability[1].get("Value", 0))
                except (ValueError, TypeError, KeyError):
                    print(f"Warning: Missing or invalid 'Value' for {name}, using default 0")
                    expected_value = 0
                
                # Skip check if expected value is 0 (not configured)
                if expected_value == 0:
                    record_miss("Local Policy")
                    return
                
                try:
                    # Use chage to get actual effective password aging (Step 1)
                    chage_info = get_chage_info()
                    if chage_info and "min_days" in chage_info:
                        actual_value = chage_info["min_days"]
                    else:
                        # Fallback to login.defs if chage fails
                        actual_value = int(policy_settings_dict.get("PASS_MIN_DAYS", 0))
                    
                    if actual_value == expected_value:
                        record_hit(
                            f"Minimum password age is set to {actual_value} days.", 
                            vulnerability[1]["Points"]
                        )
                    else:
                        record_miss("Local Policy")
                except (ValueError, TypeError, KeyError) as e:
                    print(f"Error checking {name}: {e}")
                    record_miss("Local Policy")
                    
            case "Maximum Password Age":
                # Get the expected value from configuration
                try:
                    expected_value = int(vulnerability[1].get("Value", 0))
                except (ValueError, TypeError, KeyError):
                    print(f"Warning: Missing or invalid 'Value' for {name}, using default 0")
                    expected_value = 0
                
                # Skip check if expected value is 0 (not configured)
                if expected_value == 0:
                    record_miss("Local Policy")
                    return
                
                try:
                    # Use chage to get actual effective password aging (Step 1)
                    chage_info = get_chage_info()
                    if chage_info and "max_days" in chage_info:
                        actual_value = chage_info["max_days"]
                    else:
                        # Fallback to login.defs if chage fails
                        actual_value = int(policy_settings_dict.get("PASS_MAX_DAYS", 99999))
                    
                    if actual_value == expected_value:
                        record_hit(
                            f"Maximum password age is set to {actual_value} days.", 
                            vulnerability[1]["Points"]
                        )
                    else:
                        record_miss("Local Policy")
                except (ValueError, TypeError, KeyError) as e:
                    print(f"Error checking {name}: {e}")
                    record_miss("Local Policy")

            case "Minimum Password Length":
                # Get the expected value from configuration
                try:
                    expected_value = int(vulnerability[1].get("Value", 0))
                except (ValueError, TypeError, KeyError):
                    print(f"Warning: Missing or invalid 'Value' for {name}, using default 0")
                    expected_value = 0
                
                # Skip check if expected value is 0 (not configured)
                if expected_value == 0:
                    record_miss("Local Policy")
                    return
                
                try:
                    # Use pwscore to test if requirement is actually enforced (Step 4)
                    # Pass all configuration sources to the test function
                    test_results = test_password_requirements(
                        {'minlen': expected_value},
                        password_settings_content=password_settings_content,
                        pamd_policy_settings_content=pamd_policy_settings_content,
                        login_policy_settings_content=login_policy_settings_content
                    )
                    
                    minlen_result = test_results.get('minlen', {})
                    configured = minlen_result.get('configured', False)
                    enforced = minlen_result.get('enforced', False)
                    actual_value = minlen_result.get('actual_value', 0);
                    
                    # Check if the actual configured value matches the expected value
                    if configured and actual_value == expected_value:
                        if enforced:
                            record_hit(
                                f"Minimum password length is set to {actual_value} and enforced.",
                                vulnerability[1]["Points"],
                            )
                        else:
                            # Configuration is set but not enforced - still give credit
                            # (enforcement test might fail due to missing pwscore)
                            record_hit(
                                f"Minimum password length is set to {actual_value}.",
                                vulnerability[1]["Points"],
                            )
                    else:
                        record_miss("Local Policy")
                except (ValueError, TypeError, KeyError) as e:
                    print(f"Error checking {name}: {e}")
                    record_miss("Local Policy")

            case "Maximum Login Tries":
                # Get the expected value from configuration
                try:
                    expected_value = int(vulnerability[1].get("Value", 0))
                except (ValueError, TypeError, KeyError):
                    print(f"Warning: Missing or invalid 'Value' for {name}, using default 0")
                    expected_value = 0
                
                # Skip check if expected value is 0 (not configured)
                if expected_value == 0:
                    record_miss("Local Policy")
                    return
                
                try:
                    # First, attempt an active PAM enforcement test with pamtester
                    pamtester_result = pamtester.test_max_login_tries_with_pamtester(expected_value)
                    if pamtester_result is True:
                        record_hit(
                            f"Account lockout threshold is enforced after {expected_value} failed attempts.",
                            vulnerability[1]["Points"],
                        )
                        return
                    elif pamtester_result is False:
                        record_miss("Local Policy")
                        return

                    # Priority 1: Check pam_faillock.so deny parameter in /etc/pam.d/common-auth
                    deny_value = common_auth_dict.get("deny")
                    
                    # Priority 2: Fall back to /etc/security/faillock.conf
                    if not deny_value:
                        deny_value = faillock_settings_content.get("deny")
                    
                    if deny_value:
                        actual_value = int(deny_value)
                        if actual_value == expected_value:
                            record_hit(
                                f"Account lockout threshold is set to {actual_value} failed attempts.", 
                                vulnerability[1]["Points"]
                            )
                        else:
                            record_miss("Local Policy")
                    else:
                        # No deny configuration found in either location
                        record_miss("Local Policy")
                except (ValueError, TypeError, KeyError) as e:
                    print(f"Error checking {name}: {e}")
                    record_miss("Local Policy")
                    
            case "Lockout Duration":
                """
                Checks account lockout duration after failed login attempts.
                
                Linux Account Lockout Duration Configuration Methods (in priority order):

                1. pam_faillock.so (HIGHEST PRIORITY - Modern PAM faillock module)
                   Location: /etc/pam.d/common-auth or /etc/pam.d/system-auth
                   Parameter: unlock_time=<seconds>
                   Example: auth required pam_faillock.so preauth unlock_time=900
                   Notes: Primary mechanism on modern systems (Ubuntu 20.04+, RHEL 8+)
                          unlock_time=0 means permanent lockout (admin must unlock)
                          Works in conjunction with deny= and fail_interval=
                          Must be set consistently across all three modules (preauth, authfail, authsucc)

                2. /etc/security/faillock.conf (Fallback - Centralized faillock config)
                   Location: /etc/security/faillock.conf
                   Parameter: unlock_time = <seconds>
                   Example: unlock_time = 900
                   Notes: Centralized configuration file for pam_faillock
                          Only checked if not set in common-auth modules
                          Introduced in newer versions of pam_faillock
                
                Current Implementation Priority:
                - First checks if all 3 pam_faillock.so modules (preauth, authfail, authsucc) exist
                  in /etc/pam.d/common-auth with consistent unlock_time parameters
                - Falls back to /etc/security/faillock.conf only if parameter not in all 3 modules
                - Records miss if parameter values are inconsistent across modules
                """
                # Get the expected value from configuration
                try:
                    expected_value = int(vulnerability[1].get("Value", 0))
                except (ValueError, TypeError, KeyError):
                    print(f"Warning: Missing or invalid 'Value' for {name}, using default 0")
                    expected_value = 0
                
                # Skip check if expected value is 0 (not configured)
                if expected_value == 0:
                    record_miss("Local Policy")
                    return
                
                try:
                    # Priority 1: Check if all three faillock modules have unlock_time parameter
                    preauth_unlock = common_auth_faillock_modules['preauth'].get('unlock_time')
                    authfail_unlock = common_auth_faillock_modules['authfail'].get('unlock_time')
                    authsucc_unlock = common_auth_faillock_modules['authsucc'].get('unlock_time')
                    
                    # Check if all three modules have the parameter
                    all_modules_have_param = (preauth_unlock is not None and 
                                             authfail_unlock is not None and 
                                             authsucc_unlock is not None)
                    
                    if all_modules_have_param:
                        # All three modules have the parameter - verify they're consistent
                        if preauth_unlock == authfail_unlock == authsucc_unlock:
                            # All three match - check if it's the expected value
                            actual_value = int(preauth_unlock)
                            if actual_value == expected_value:
                                record_hit(
                                    f"Account lockout duration (unlock_time) is set to {actual_value} seconds across all faillock modules.", 
                                    vulnerability[1]["Points"]
                                )
                            else:
                                record_miss("Local Policy")
                        else:
                            # Values are inconsistent across modules
                            print(f"Warning: unlock_time values are inconsistent across faillock modules: preauth={preauth_unlock}, authfail={authfail_unlock}, authsucc={authsucc_unlock}")
                            record_miss("Local Policy")
                    else:
                        # Not all modules have the parameter - fall back to faillock.conf
                        unlock_time = faillock_settings_content.get("unlock_time")
                        if unlock_time:
                            actual_value = int(unlock_time)
                            if actual_value == expected_value:
                                record_hit(
                                    f"Account lockout duration (unlock_time) is set to {actual_value} seconds in faillock.conf.", 
                                    vulnerability[1]["Points"]
                                )
                            else:
                                record_miss("Local Policy")
                        else:
                            # No unlock_time found in any configuration
                            record_miss("Local Policy")
                except (ValueError, TypeError, KeyError) as e:
                    print(f"Error checking {name}: {e}")
                    record_miss("Local Policy")
                    
            case "Lockout Reset Duration":
                """
                Checks account lockout reset/observation window duration.
                This is the time window in which failed login attempts are counted.
                
                Linux Account Lockout Reset Duration Configuration Methods (in priority order):
                
                1. pam_faillock.so (HIGHEST PRIORITY - Modern PAM faillock module)
                   Location: /etc/pam.d/common-auth or /etc/pam.d/system-auth
                   Parameter: fail_interval=<seconds>
                   Example: auth required pam_faillock.so preauth fail_interval=900
                   Notes: Primary mechanism on modern systems (Ubuntu 20.04+, RHEL 8+)
                          Defines the time window for counting failed attempts
                          After this interval, the failure count resets to 0
                          Works with deny= to determine when lockout occurs
                          Must be set consistently across all three modules (preauth, authfail, authsucc)
                
                2. /etc/security/faillock.conf (Fallback - Centralized faillock config)
                   Location: /etc/security/faillock.conf
                   Parameter: fail_interval = <seconds>
                   Example: fail_interval = 900
                   Notes: Centralized configuration file for pam_faillock
                          Only checked if not set in common-auth modules
                          Introduced in newer versions of pam_faillock
                
                Current Implementation Priority:
                - First checks if all 3 pam_faillock.so modules (preauth, authfail, authsucc) exist
                  in /etc/pam.d/common-auth with consistent fail_interval parameters
                - Falls back to /etc/security/faillock.conf only if parameter not in all 3 modules
                - Records miss if parameter values are inconsistent across modules
                """
                # Get the expected value from configuration
                try:
                    expected_value = int(vulnerability[1].get("Value", 0))
                except (ValueError, TypeError, KeyError):
                    print(f"Warning: Missing or invalid 'Value' for {name}, using default 0")
                    expected_value = 0
                
                # Skip check if expected value is 0 (not configured)
                if expected_value == 0:
                    record_miss("Local Policy")
                    return
                
                try:
                    # Priority 1: Check if all three faillock modules have fail_interval parameter
                    preauth_interval = common_auth_faillock_modules['preauth'].get('fail_interval')
                    authfail_interval = common_auth_faillock_modules['authfail'].get('fail_interval')
                    authsucc_interval = common_auth_faillock_modules['authsucc'].get('fail_interval')
                    
                    # Check if all three modules have the parameter
                    all_modules_have_param = (preauth_interval is not None and 
                                             authfail_interval is not None and 
                                             authsucc_interval is not None)
                    
                    if all_modules_have_param:
                        # All three modules have the parameter - verify they're consistent
                        if preauth_interval == authfail_interval == authsucc_interval:
                            # All three match - check if it's the expected value
                            actual_value = int(preauth_interval)
                            if actual_value == expected_value:
                                record_hit(
                                    f"Account lockout observation window (fail_interval) is set to {actual_value} seconds across all faillock modules.", 
                                    vulnerability[1]["Points"]
                                )
                            else:
                                record_miss("Local Policy")
                        else:
                            # Values are inconsistent across modules
                            print(f"Warning: fail_interval values are inconsistent across faillock modules: preauth={preauth_interval}, authfail={authfail_interval}, authsucc={authsucc_interval}")
                            record_miss("Local Policy")
                    else:
                        # Not all modules have the parameter - fall back to faillock.conf
                        fail_interval = faillock_settings_content.get("fail_interval")
                        if fail_interval:
                            actual_value = int(fail_interval)
                            if actual_value == expected_value:
                                record_hit(
                                    f"Account lockout observation window (fail_interval) is set to {actual_value} seconds in faillock.conf.", 
                                    vulnerability[1]["Points"]
                                )
                            else:
                                record_miss("Local Policy")
                        else:
                            # No fail_interval found in any configuration
                            record_miss("Local Policy")
                except (ValueError, TypeError, KeyError) as e:
                    print(f"Error checking {name}: {e}")
                    record_miss("Local Policy")
                    
            case "Password History":
                # Get the expected value from configuration
                try:
                    expected_value = int(vulnerability[1].get("Value", 0))
                except (ValueError, TypeError, KeyError):
                    print(f"Warning: Missing or invalid 'Value' for {name}, using default 0")
                    expected_value = 0
                
                # Skip check if expected value is 0 (not configured)
                if expected_value == 0:
                    record_miss("Local Policy")
                    return
                
                try:
                    # Check PAM settings first, then fallback to password settings
                    remember_value = pam_settings_dict.get("remember") or password_settings_content.get("remember")
                    if remember_value:
                        actual_value = int(remember_value)
                        if actual_value == expected_value:
                            record_hit(
                                f"Password history size is set to {actual_value}.", 
                                vulnerability[1]["Points"]
                            )
                        else:
                            record_miss("Local Policy")
                    else:
                        record_miss("Local Policy")
                except (ValueError, TypeError, KeyError) as e:
                    print(f"Error checking {name}: {e}")
                    record_miss("Local Policy")
                    
            case "Audit":
                if audit_check():
                    record_hit("Auditing is on.", vulnerability[1]["Points"])
                else:
                    record_miss("Local Policy")
            
            case "Disable SSH Root Login":
                disable_SSH_Root_Login(vulnerability)


            case "Check Kernel":
                check_kernel(vulnerability)

            case _:
                # Handle unknown policy names
                record_miss("Local Policy")
                print(f"Warning: Unknown policy name '{name}' in local_group_policy")
                
    except (KeyError, ValueError, TypeError) as e:
        print(f"Error processing policy '{name}': {e}")
        warnings.warn(f"Error processing policy '{name}': {e}")
        record_miss("Local Policy")


# test
def group_manipulation(vulnerability, name):
    """
    Checks for group manipulation actions (add/remove) and records hits/misses.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
        name (str): The action being checked (Add Admin, Remove Admin, etc.).
    """
    groups = grp.getgrall()
    
    match name:
        case "Add Admin":
            for vuln in vulnerability:
                if vuln != 1:
                    if vulnerability[vuln]["User Name"] in grp.getgrnam("sudo")[3]:
                        record_hit(
                            vulnerability[vuln]["User Name"]
                            + " has been promoted to administrator.",
                            vulnerability[vuln]["Points"],
                        )
                    else:
                        record_miss("Account Management")
        case "Remove Admin":
            for vuln in vulnerability:
                if vuln != 1:
                    if vulnerability[vuln]["User Name"] not in grp.getgrnam("sudo")[3]:
                        record_hit(
                            vulnerability[vuln]["User Name"]
                            + " has been demoted to standard user.",
                            vulnerability[vuln]["Points"],
                        )
                    else:
                        record_miss("Account Management")
        case "Add User to Group":
            for vuln in vulnerability:
                if vuln != 1:
                    try:
                        if (
                            vulnerability[vuln]["User Name"]
                            in grp.getgrnam(vulnerability[vuln]["Group Name"])[3]
                        ):
                            record_hit(
                                vulnerability[vuln]["User Name"]
                                + " is in the "
                                + vulnerability[vuln]["Group Name"]
                                + " group.",
                                vulnerability[vuln]["Points"],
                            )
                        else:
                            record_miss("Account Management")
                    except KeyError: # If the group does not exist, can't be in group, miss.
                        record_miss("Account Management")
        case "Remove User from Group":
            for vuln in vulnerability:
                if vuln != 1:
                    try:
                        if (
                            vulnerability[vuln]["User Name"]
                            not in grp.getgrnam(vulnerability[vuln]["Group Name"])[3]
                        ):
                            record_hit(
                                vulnerability[vuln]["User Name"]
                                + " is no longer in the "
                                + vulnerability[vuln]["Group Name"]
                                + " group.",
                                vulnerability[vuln]["Points"],
                            )
                        else:
                            record_miss("Account Management")
                    except KeyError: # If the group does not exist, user can't be in group, hit.
                        record_hit(
                            vulnerability[vuln]["User Name"]
                            + " is no longer in the "
                            + vulnerability[vuln]["Group Name"]
                            + " group.",
                            vulnerability[vuln]["Points"],
                        )


def build_password_requirements_cache(categories, vulnerabilities_obj):
    """
    Builds a dictionary of password requirements from vulnerability configurations.
    Scans all categories to find password policy vulnerabilities and extracts their values.
    
    Args:
        categories (list): List of category objects from database.
        vulnerabilities_obj: The OptionTables object to query vulnerabilities.
    
    Returns:
        dict: Dictionary mapping requirement keys (e.g., 'minlen') to their configured values.
    """
    password_requirement_mapping = { # DEVNOTE: Add more if creating new password requirements in future.
        "Minimum Password Length": "minlen",
        # Add more mappings here as needed in the future:
        # "Password Complexity": "complexity",
        # "Minimum Uppercase Letters": "ucredit",
        # "Minimum Lowercase Letters": "lcredit",
        # etc.
    }
    requirements = {}
    
    for category in categories:
        # Get vulnerability templates for this category
        vuln_templates = vulnerabilities_obj.get_option_template_by_category(category.id)
        # vuln_templates is a list of VulnerabilityTemplateModel objects
        for template in vuln_templates:
            vuln_name = template.name  # This is the vulnerability name like "Minimum Password Length"
            
            # Check if this vulnerability is a password requirement we want to test
            if vuln_name in password_requirement_mapping:
                # Get the actual configured instances for this vulnerability
                try:
                    option_table = vulnerabilities_obj.get_option_table(vuln_name, config=False)
                    
                    # option_table is a dict indexed by instance ID
                    # For policy vulnerabilities, the data is always in entry 1(just a safety measure check)
                    if 1 in option_table: 
                        instance_data = option_table[1]
                        # Check if enabled and has a configured value
                        if instance_data.get("Enabled", False):
                            requirement_value = instance_data.get("Value", 0)
                            
                            # Only add if value is configured (non-zero)
                            if requirement_value and int(requirement_value) > 0:
                                requirement_key = password_requirement_mapping[vuln_name]
                                requirements[requirement_key] = int(requirement_value)
                except Exception as e:
                    # If there's an error getting the option table, skip this vulnerability
                    print(f"Warning: Could not get option table for {vuln_name}: {e}")
                    continue
    
    return requirements


def get_password_hash(username):
    """
    Get the current password hash for a user from /etc/shadow.
    Used for efficient change detection without re-validating if hash unchanged.
    
    Args:
        username (str): The username to lookup.
    
    Returns:
        str: The password hash (second field from /etc/shadow), or None if not found.
    """
    try:
        with open('/etc/shadow', 'r') as f:
            for line in f:
                if line.startswith(username + ':'):
                    parts = line.split(':')
                    if len(parts) >= 2:
                        return parts[1]  # Password hash field
    except (PermissionError, FileNotFoundError) as e:
        print(f"Warning: Could not read /etc/shadow: {e}")
    return None

# Deprecated
def get_precise_password_change_time(username):
    """
    Get the most recent precise password change time for a user from auth.log.
    Searches auth logs for password change events with precise timestamps.
    Handles both ISO 8601 format (systemd) and traditional syslog format.
    
    CRITICAL: PAM may log "password changed" even when the change was rejected by pwquality.
    This function cross-references the timestamp with the actual password hash to verify
    the password was truly changed. Uses the timestamp from auth.log but relies on the
    calling function to validate the hash actually changed to confirm validity.
    
    Args:
        username (str): The username to search for.
    
    Returns:
        datetime object with precise timestamp, or None if not found in logs.
        Note: Caller must verify the password hash actually changed to confirm validity.
    """
    log_files = ['/var/log/auth.log', '/var/log/auth.log.1']  # Check current and rotated log
    
    for log_file in log_files:
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            # Search backwards (most recent first)
            for line in reversed(lines):
                if f"password changed for {username}" in line:                    
                    # Parse timestamp - try ISO 8601 format first (systemd journal format)
                    # Format: 2026-01-07T12:54:31.696514-08:00 hostname ...
                    parts = line.split()
                    if len(parts) >= 1:
                        timestamp_str = parts[0]
                        
                        # Try ISO 8601 format with timezone and microseconds
                        try:
                            # Remove timezone offset for simpler parsing (just keep local time)
                            # Format: 2026-01-07T12:54:31.696514-08:00
                            if 'T' in timestamp_str:
                                # Split off timezone if present
                                if '+' in timestamp_str or timestamp_str.count('-') > 2:
                                    # Find the last + or - which indicates timezone
                                    for tz_sep in ['+', '-']:
                                        if tz_sep in timestamp_str[10:]:  # After date part
                                            timestamp_str = timestamp_str.rsplit(tz_sep, 1)[0]
                                            break
                                
                                # Now parse: 2026-01-07T12:54:31.696514 or 2026-01-07T12:54:31
                                if '.' in timestamp_str:
                                    # Has microseconds
                                    dt = datetime.datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%f")
                                else:
                                    # No microseconds
                                    dt = datetime.datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S")
                        
                                return dt
                        except ValueError as e:
                            print(f"DEBUG: Could not parse as ISO format: {e}")
                        
                        # Try traditional syslog format: Dec 19 14:23:45
                        try:
                            if len(parts) >= 3:
                                month = parts[0]
                                day = parts[1]
                                time_str = parts[2]
                                
                                current_year = datetime.datetime.now().year
                                timestamp_str = f"{month} {day} {current_year} {time_str}"
                                
                                dt = datetime.datetime.strptime(timestamp_str, "%b %d %Y %H:%M:%S")
                                return dt
                        except ValueError as e:
                            print(f"DEBUG: Could not parse as syslog format: {e}")
                            continue
                            
        except (FileNotFoundError, PermissionError) as e:
            print(f"Warning: Could not read {log_file}: {e}")
            continue
    
    return None


def user_change_password(vulnerability):
    """
    Checks if a user's password has been changed and meets password policy requirements.
    Uses auth.log to get precise password change time, and test_password_requirements
    to ensure system-wide password policies are enforced.
    
    Uses the global password_requirements_cache which is populated in the main loop
    by scanning all vulnerability categories for password policy requirements.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    # Ensure enforce_for_root is set in pwquality.conf to apply rules to root user
    # This ensures passwords must meet all requirements when changed, even for root
    pwquality_conf_path = "/etc/security/pwquality.conf"
    try:
        # Read the current configuration
        with open(pwquality_conf_path, "r") as f:
            lines = f.readlines()
        
        # Check if enforce_for_root line exists
        has_enforce_for_root = False
        modified = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Check for enforce_for_root (with or without leading comment)
            if stripped.startswith("enforce_for_root") or stripped.startswith("# enforce_for_root"):
                has_enforce_for_root = True
                # If it's commented out or not set correctly, fix it
                if not stripped.startswith("enforce_for_root") or "DO_NOT_REMOVE" not in line:
                    lines[i] = "enforce_for_root  # DO_NOT_REMOVE\n"
                    modified = True
                break
        
        # Add enforce_for_root if it doesn't exist
        if not has_enforce_for_root:
            lines.append("enforce_for_root  # DO_NOT_REMOVE\n")
            modified = True
        
        # Write back to the file if modified
        if modified:
            with open(pwquality_conf_path, "w") as f:
                f.writelines(lines)
            print(f"INFO: Added/updated 'enforce_for_root' in {pwquality_conf_path}")
    except (IOError, PermissionError) as e:
        print(f"Warning: Could not modify {pwquality_conf_path}: {e}")
    
    # Ensure enforce_for_root is added to pam_pwquality.so line in common-password
    # Also ensure pam_pwquality.so is the FIRST password module to prevent bypass
    common_password_path = "/etc/pam.d/common-password"
    try:
        with open(common_password_path, "r") as f:
            pam_lines = f.readlines()
        
        pam_modified = False
        pwquality_line_index = -1
        first_password_module_index = -1
        
        # First pass: find pam_pwquality.so line and first password module
        for i, line in enumerate(pam_lines):
            stripped = line.strip()
            # Skip comments and empty lines
            if not stripped or stripped.startswith("#"):
                continue
            
            # Check if this is a password module line
            if stripped.startswith("password"):
                if first_password_module_index == -1:
                    first_password_module_index = i
                
                # Check if this is the pam_pwquality.so line
                if "pam_pwquality.so" in line:
                    pwquality_line_index = i
                    # Ensure enforce_for_root is present
                    if "enforce_for_root" not in line:
                        pam_lines[i] = line.rstrip() + " enforce_for_root\n"
                        pam_modified = True
                    break
        
        # Second pass: if pam_pwquality.so exists but is not first, move it to the top
        if pwquality_line_index != -1 and first_password_module_index != -1:
            if pwquality_line_index != first_password_module_index:
                # Remove the pwquality line from its current position
                pwquality_line = pam_lines.pop(pwquality_line_index)
                # Insert it at the first password module position
                pam_lines.insert(first_password_module_index, pwquality_line)
                pam_modified = True
                print(f"INFO: Moved pam_pwquality.so to top of password module stack in {common_password_path}")
        
        if pam_modified:
            with open(common_password_path, "w") as f:
                f.writelines(pam_lines)
            if not (pwquality_line_index != -1 and pwquality_line_index != first_password_module_index):
                print(f"INFO: Added 'enforce_for_root' to pam_pwquality.so in {common_password_path}")
    except (IOError, PermissionError) as e:
        print(f"Warning: Could not modify {common_password_path}: {e}")
    
    # Use the global cache built in the main loop
    global password_requirements_cache
    requirements_to_check = password_requirements_cache.copy()
    for vuln in vulnerability:
        if vuln != 1:
            username = vulnerability[vuln]["User Name"]

            # Step 1: Detect password hash change and record timestamp
            # Get current hash and compare with stored hash to detect changes
            try:
                current_hash = get_password_hash(username)

                # Load stored timestamps and hashes
                config_timestamps = load_config_timestamps()
                stored_data = config_timestamps.get(username, {})
                stored_hash = stored_data.get('validated_hash')
                stored_timestamp = stored_data.get('password_change_timestamp')

                # Check if hash has changed since last check
                password_change_timestamp = None
                if stored_hash and current_hash and stored_hash != current_hash:
                    # Hash changed — record current time as password change time
                    password_change_timestamp = datetime.datetime.now()
                    stored_data['validated_hash'] = current_hash
                    stored_data['password_change_timestamp'] = password_change_timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    config_timestamps[username] = stored_data
                    save_config_timestamps(config_timestamps)
                elif stored_timestamp:
                    # Hash unchanged but we have a previous timestamp — use it
                    try:
                        password_change_timestamp = datetime.datetime.strptime(stored_timestamp, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        pass
                elif not stored_hash and current_hash:
                    # First time seeing this user — store hash, no timestamp yet
                    stored_data['validated_hash'] = current_hash
                    config_timestamps[username] = stored_data
                    save_config_timestamps(config_timestamps)

                # If we have a timestamp, check if it's recent and validate requirements
                if password_change_timestamp:
                    today = datetime.datetime.now()
                    time_since_change = today - password_change_timestamp

                    # Check if password was changed within last 7 days
                    if time_since_change.days <= 7:
                        if requirements_to_check:
                            test_results = test_password_requirements(
                                requirements_to_check,
                                password_settings_content=password_settings_content,
                                pamd_policy_settings_content=pamd_policy_settings_content,
                                login_policy_settings_content=login_policy_settings_content,
                                username_to_test=username,
                                password_change_date=password_change_timestamp
                            )
                            if test_results.get('password_passes', False):
                                record_hit(
                                    f"{username}'s password was changed after requirements were configured.",
                                    vulnerability[vuln]["Points"],
                                )
                            else:
                                record_miss("Account Management")
                        else:
                            # No password requirements configured — just check for a change
                            record_hit(
                                f"{username}'s password was changed.",
                                vulnerability[vuln]["Points"],
                            )
                    else:
                        record_miss("Account Management")
                else:
                    # Could not determine password change time
                    record_miss("Account Management")

            except subprocess.CalledProcessError as e:
                print(f"Warning: Could not get password info for {username}: {e}")
                record_miss("Account Management")
            except Exception as e:
                print(f"Error checking password for {username}: {e}")
                record_miss("Account Management")


# check
def check_startup(vulnerability):
    """
    Checks if specific programs are set to run at startup and records hits/misses.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    file = open("startup.txt", "r", encoding="utf-16-le")
    content = file.read().splitlines()
    file.close()
    for vuln in vulnerability:
        if vuln != 1:
            if vulnerability[vuln]["Program Name"] in content:
                record_hit(
                    "Program Removed from Startup", vulnerability[vuln]["Points"]
                )
            else:
                record_miss("Program Management")


def update_check_period(vulnerability):
    """
    Linux Mint:
    gsettings get com.linuxmint.updates refresh-schedule-enabled
    """

    # --- determine user to run gsettings as ---
    user = os.environ.get("SUDO_USER")
    if not user:
        user = os.environ.get("USER")
    if not user:
        try:
            user = os.getlogin()
        except OSError:
            user = None
    
    if not user:
        print("ERROR: Could not determine user for gsettings command")
        record_miss("Program Management")
        return

    # --- run gsettings ---
    try:
        result = subprocess.run(
            [
                "sudo",
                "-u",
                user,
                "gsettings",
                "get",
                "com.linuxmint.updates",
                "refresh-schedule-enabled",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        enabled = result.stdout.strip().lower() == "true"

    except Exception:
        enabled = False

    # --- scoring ---
    if enabled:
        record_hit("Update check period is enabled", vulnerability[1]["Points"])
    else:
        record_miss("Program Management")


def add_text_to_file(vulnerability):
    """
    Checks if specific text has been added to a file and records hits/misses.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    for vuln in vulnerability:
        if vuln != 1:
            # Support both new and old field names for backward compatibility
            file_path = vulnerability[vuln].get("File Path") or vulnerability[vuln].get("File Path (Regex)") or vulnerability[vuln].get("Object Path", "")
            # Skip empty or invalid file paths
            if not file_path or not file_path.strip():
                continue
            try:
                file = open(file_path, "r")
                content = file.read()
                file.close()
                if re.search(vulnerability[vuln]["Text to Add"], content):
                    record_hit(
                        vulnerability[vuln]["Text to Add"]
                        + " has been added to "
                        + file_path,
                        vulnerability[vuln]["Points"],
                    )
                else:
                    record_miss("File Management")
            except re.error:
                # Skip if regex pattern is invalid
                continue
            except (FileNotFoundError, PermissionError, OSError):
                # Skip if file doesn't exist or can't be read
                record_miss("File Management")
                continue


def remove_text_from_file(vulnerability):
    """
    Checks if specific text has been removed from a file and records hits/misses.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    for vuln in vulnerability:
        if vuln != 1:
            # Support both new and old field names for backward compatibility
            file_path = vulnerability[vuln].get("File Path") or vulnerability[vuln].get("File Path (Regex)") or vulnerability[vuln].get("Object Path", "")
            # Skip empty or invalid file paths
            if not file_path or not file_path.strip():
                continue
            try:
                file = open(file_path, "r")
                content = file.read()
                file.close()
                if not re.search(vulnerability[vuln]["Text to Remove"], content):
                    record_hit(
                        vulnerability[vuln]["Text to Remove"]
                        + " has been removed from "
                        + file_path,
                        vulnerability[vuln]["Points"],
                    )
                else:
                    record_miss("File Management")
            except re.error:
                # Skip if regex pattern is invalid
                continue
            except (FileNotFoundError, PermissionError, OSError):
                # Skip if file doesn't exist or can't be read
                record_miss("File Management")
                continue


def _is_valid_autostart_file(path):
    """
    Validate a .desktop file for autostart purposes.

    A file is considered valid if it has:
    - A [Desktop Entry] section
    - Name, Exec, and Type keys (case-sensitive key names)
    - Type=Application (whitespace-insensitive, case-insensitive)
    - A resolvable Exec binary (first token after stripping field codes like %f/%u)

    Args:
        path (Path or str): Path to the .desktop file.

    Returns:
        tuple: (is_valid: bool, is_hidden: bool)
            is_valid  - True if the file meets all validity criteria.
            is_hidden - True if Hidden=true (whitespace-insensitive, lowercase 'true').
    """
    try:
        parser = configparser.RawConfigParser()
        parser.optionxform = str  # Preserve key case (e.g. "Exec" not "exec")
        parser.read(str(path))

        if not parser.has_section('Desktop Entry'):
            return False, False

        section = parser['Desktop Entry']

        # Check required keys exist (case-sensitive)
        for key in ('Name', 'Exec', 'Type'):
            if key not in section:
                return False, False

        # Type must be "Application" (whitespace-insensitive, case-insensitive)
        if section['Type'].strip().lower() != 'application':
            return False, False

        # Exec: extract first token, strip XDG field codes (%f, %F, %u, %U, etc.)
        exec_value = section['Exec'].strip()
        exec_cmd = re.split(r'\s+', exec_value)[0]
        exec_cmd = re.sub(r'%[a-zA-Z]', '', exec_cmd).strip()
        if not exec_cmd:
            return False, False
        # Must be an existing absolute path or findable in PATH
        if not (os.path.isfile(exec_cmd) or shutil.which(exec_cmd) is not None):
            return False, False

        # Hidden=true check (whitespace-insensitive, must be lowercase 'true')
        is_hidden = False
        if 'Hidden' in section:
            is_hidden = section['Hidden'].strip() == 'true'

        return True, is_hidden

    except (configparser.Error, IOError, PermissionError, OSError):
        return False, False


def start_up_apps(vulnerability):
    """
    Checks if specific applications are disabled from running at startup.

    Determines user home directory properly when running under sudo by checking
    the SUDO_USER environment variable to get the actual user (not root).
    Falls back to Path.home() if not running under sudo.

    Uses XDG base directories (via pyxdg) to find system-wide autostart folders.

    Validation criteria for a .desktop file:
    - Has a [Desktop Entry] section
    - Has Name, Exec, and Type keys
    - Type=Application (whitespace/case-insensitive)
    - Exec binary is resolvable (exists on filesystem or in PATH)

    Scoring logic (checked in order):
    1. User autostart file (~/.config/autostart/<program>.desktop):
       - If valid: hit if Hidden=true (whitespace-insensitive), miss otherwise
    2. Global autostart file(s) (from XDG config dirs, e.g. /etc/xdg/autostart):
       - If valid: hit if Hidden=true (whitespace-insensitive), miss otherwise
    3. Neither file is valid (doesn't exist or fails validation):
       - Record a hit (program is not configured to autostart anywhere)

    Note: Hidden value matching is whitespace-insensitive and case-sensitive
          (must be lowercase 'true'). Hidden=TRUE will NOT score a hit.

    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    # Get system-wide autostart directories via XDG (excludes user config home)
    global_autostart_dirs = [
        Path(d) / "autostart"
        for d in xdg_base.xdg_config_dirs
        if d != xdg_base.xdg_config_home
    ]

    # Get the actual user's home directory (not root's when running with sudo)
    sudo_user = os.environ.get('SUDO_USER')
    if sudo_user:
        user_home = Path(f"/home/{sudo_user}")
    else:
        user_home = Path.home()

    user_autostart_dir = user_home / ".config/autostart"

    for vuln in vulnerability:
        if vuln != 1:
            program_to_check = vulnerability[vuln].get("Program Name", "")
            if not program_to_check:
                continue

            # Ensure .desktop extension
            desktop_filename = (
                program_to_check
                if program_to_check.endswith(".desktop")
                else f"{program_to_check}.desktop"
            )

            user_desktop_path = user_autostart_dir / desktop_filename

            # Step 1: Check user autostart file — if valid, score on Hidden
            if user_desktop_path.exists():
                is_valid, is_hidden = _is_valid_autostart_file(user_desktop_path)
                if is_valid:
                    if is_hidden:
                        record_hit(
                            f"{program_to_check} has been disabled from startup",
                            vulnerability[vuln]["Points"],
                        )
                    else:
                        record_miss("File Management")
                    continue

            # Step 2: Check global autostart file(s) — if valid, score on Hidden
            global_valid = False
            global_hidden = False
            for global_autostart_dir in global_autostart_dirs:
                global_desktop_path = global_autostart_dir / desktop_filename
                if global_desktop_path.exists():
                    gv, gh = _is_valid_autostart_file(global_desktop_path)
                    if gv:
                        global_valid, global_hidden = True, gh
                        break

            if global_valid:
                if global_hidden:
                    record_hit(
                        f"{program_to_check} has been disabled from startup",
                        vulnerability[vuln]["Points"],
                    )
                else:
                    record_miss("File Management")
                continue

            # Step 3: No valid autostart entry found — program is not configured to autostart
            record_hit(
                f"{program_to_check} is not configured to autostart",
                vulnerability[vuln]["Points"],
            )


def check_hosts(vulnerability):
    """
    Checks the /etc/hosts file and records hits/misses based on its content.
    Ignores standard default entries that are part of a normal hosts file.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    hosts_file_path = "/etc/hosts"
    
    # Define standard default patterns that should be ignored
    # These are the default entries in a typical Linux mint hosts file
    # TODO: Might need updating for other distributions
    default_patterns = [
        r'^\s*127\.0\.0\.1\s+\S+(\s+\S+)*\s*$',
        r'^\s*127\.0\.1\.1\s+\S+(\s+\S+)*\s*$',
        r'^\s*::1\s+\S+(\s+\S+)*\s*$',
        r'^\s*fe00::0\s+\S+(\s+\S+)*\s*$',
        r'^\s*ff00::0\s+\S+(\s+\S+)*\s*$',
        r'^\s*ff02::1\s+\S+(\s+\S+)*\s*$',
        r'^\s*ff02::2\s+\S+(\s+\S+)*\s*$',
    ]
    try:
        with open(hosts_file_path, "r") as file:
            lines = file.readlines()
        
        # Filter out empty lines, comments, and default entries
        non_default_lines = []
        for line in lines:
            stripped_line = line.strip()
            
            # Skip empty lines and comment-only lines
            if not stripped_line or stripped_line.startswith('#'):
                continue
            
            # Check if this line matches any default pattern
            is_default = False
            for pattern in default_patterns:
                if re.match(pattern, stripped_line, re.IGNORECASE):
                    is_default = True
                    break
            
            # If it doesn't match any default pattern, it's a non-default entry
            if not is_default:
                non_default_lines.append(stripped_line)
        
        # Score based on whether there are any non-default entries
        if not non_default_lines:
            record_hit("Hosts file has been cleared", vulnerability[1]["Points"])
        else:
            record_miss("File Management")
    
    except (IOError, PermissionError) as e:
        print(f"ERROR: Could not read {hosts_file_path}: {e}")
        record_miss("File Management")
        
    except Exception as e:
        print(f"ERROR: An unexpected error occurred while checking hosts file: {e}")
        record_miss("File Management")


# fix
def critical_services(vulnerability):
    """
    Checks for critical services and records penalties if their state has changed.
    Awards penalty if service state OR start mode differs from configured values.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    for vuln in vulnerability:
        if vuln != 1:
            service_name = vulnerability[vuln]["Service Name"]
            expected_state = vulnerability[vuln]["Service State"]
            expected_start_mode = vulnerability[vuln]["Service Start Mode"]
            # Ensure service name has .service extension
            if not service_name.endswith(".service"):
                service_name_full = service_name + ".service"
            else:
                service_name_full = service_name
            
            # Find the service in services_content list
            for service in services_content:     
                # Check for exact match of base names
                if service_name_full == service["unit"]:
                    actual_state = service["active"]
                    # Get the service start mode
                    try:
                        result = subprocess.run(
                            ["systemctl", "is-enabled", service["unit"]],
                            capture_output=True,
                            text=True,
                            check=False
                        )
                        actual_start_mode = result.stdout.strip()
                    except Exception as e:
                        print(f"Warning: Could not check start mode for {service['unit']}: {e}")
                        actual_start_mode = "unknown"
                    
                    # Penalize if either state or start mode changed
                    if actual_state != expected_state or actual_start_mode != expected_start_mode:
                        record_penalty(
                            f"{service_name} was changed from {expected_state}/{expected_start_mode}",
                            vulnerability[vuln]["Points"]
                        )
                    break


# fix
def manage_services(vulnerability):
    """
    Checks the state of services and records hits/misses based on their status.
    Checks both service state (active/inactive) and start mode (enabled/disabled/masked).
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    for vuln in vulnerability:
        if vuln != 1:
            service_name = vulnerability[vuln]["Service Name"]
            expected_state = vulnerability[vuln]["Service State"]  # "active" or "inactive"
            expected_start_mode = vulnerability[vuln]["Service Start Mode"]  # "enabled", "disabled", "masked"
            
            # Ensure service name has .service extension
            if not service_name.endswith(".service"):
                service_name_full = service_name + ".service"
            else:
                service_name_full = service_name
            
            # Use systemctl status to check if service exists and get its state
            try:
                status_result = subprocess.run(
                    ["systemctl", "status", service_name_full],
                    capture_output=True,
                    text=True,
                    check=False  # Don't raise on non-zero exit (service might be inactive)
                )
                
                # Parse the status output to determine actual state
                status_output = status_result.stdout.lower()
                
                # Check if service exists (systemctl status returns specific error if not found)
                if "could not be found" in status_output or "not loaded" in status_output:
                    print(f"DEBUG: Service {service_name} not found")
                    record_miss("Program Management")
                    continue
                
                # Determine actual state from status output
                if "active (running)" in status_output or "active (exited)" in status_output:
                    actual_state = "active"
                elif "inactive (dead)" in status_output:
                    actual_state = "inactive"
                elif "failed" in status_output:
                    actual_state = "failed"
                else:
                    actual_state = "unknown"
                
                # Get the service start mode using systemctl is-enabled
                try:
                    enabled_result = subprocess.run(
                        ["systemctl", "is-enabled", service_name_full],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    actual_start_mode = enabled_result.stdout.strip()  # "enabled", "disabled", "masked", etc.
                except Exception as e:
                    print(f"Warning: Could not check start mode for {service_name_full}: {e}")
                    actual_start_mode = "unknown"
                
                # Check if both state and start mode match
                state_matches = (actual_state == expected_state)
                start_mode_matches = (actual_start_mode == expected_start_mode)
                
                if state_matches and start_mode_matches:
                    record_hit(
                        f"{service_name} is {expected_state} and set to {expected_start_mode}",
                        vulnerability[vuln]["Points"],
                    )
                else:
                    if not state_matches:
                        print(f"DEBUG: {service_name} state mismatch - expected: {expected_state}, actual: {actual_state}")
                    if not start_mode_matches:
                        print(f"DEBUG: {service_name} start mode mismatch - expected: {expected_start_mode}, actual: {actual_start_mode}")
                    record_miss("Program Management")
                    
            except Exception as e:
                print(f"ERROR: Could not check service {service_name}: {e}")
                record_miss("Program Management")

def check_ssh_permit_root_login():
    """
    Helper function to check SSH PermitRootLogin configuration.
    Uses global ssh_config_cache to avoid re-parsing when file hasn't changed.
    
    Returns:
        dict: {
            'permit_root_login_found': bool,
            'permit_root_login_value': str or None,
            'ssh_config_exists': bool
        }
    """
    global ssh_config_cache, _ssh_config_cache_valid
    
    # If cache is valid, return cached result
    if _ssh_config_cache_valid and ssh_config_cache['populated']:
        return {
            'permit_root_login_found': ssh_config_cache['permit_root_login'] == 'found',
            'permit_root_login_value': ssh_config_cache['permit_root_login_value'],
            'ssh_config_exists': ssh_config_cache['permit_root_login'] is not None
        }
    
    # Cache miss or invalidated - re-read the file
    result = {
        'permit_root_login_found': False,
        'permit_root_login_value': None,
        'ssh_config_exists': True
    }
    
    try:
        with open("/etc/ssh/sshd_config", "r") as ssh_config_file:
            for line in ssh_config_file:
                stripped_line = line.strip()
                # Skip empty lines and comments
                if not stripped_line or stripped_line.startswith("#"):
                    continue
                
                # Check for PermitRootLogin directive (case-insensitive)
                if stripped_line.lower().startswith("permitrootlogin"):
                    result['permit_root_login_found'] = True
                    parts = stripped_line.split()
                    if len(parts) >= 2:
                        result['permit_root_login_value'] = parts[1].lower()
                    break  # Found the active directive, stop searching
        
        # Update cache
        ssh_config_cache['permit_root_login'] = 'found' if result['permit_root_login_found'] else 'not_found'
        ssh_config_cache['permit_root_login_value'] = result['permit_root_login_value']
        ssh_config_cache['populated'] = True
        
    except FileNotFoundError:
        result['ssh_config_exists'] = False
        # Update cache
        ssh_config_cache['permit_root_login'] = None
        ssh_config_cache['permit_root_login_value'] = None
        ssh_config_cache['populated'] = True
    
    return result


def disable_SSH_Root_Login(vulnerability):
    """
    Checks if SSH root login is disabled and records hits/misses.
    Uses check_ssh_permit_root_login() helper which caches results via inotify.
    
    By default, SSH has PermitRootLogin disabled (or set to "prohibit-password").
    Award points if:
    - PermitRootLogin is explicitly set to "no" or "without-password" or "prohibit-password"
    - PermitRootLogin is commented out (default behavior = disabled)
    - PermitRootLogin line doesn't exist (default behavior = disabled)
    - SSH config file doesn't exist (SSH not installed)
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    ssh_config = check_ssh_permit_root_login()
    
    if not ssh_config['ssh_config_exists']:
        # SSH config doesn't exist - SSH likely not installed
        record_hit("SSH Root Login Disabled (SSH not configured).", vulnerability[1]["Points"])
        return
    
    if not ssh_config['permit_root_login_found']:
        # Not found = commented out or doesn't exist which is default
        record_hit(
            "SSH Root Login Disabled (default or commented out).", 
            vulnerability[1]["Points"]
        )
    elif ssh_config['permit_root_login_value'] in ("no", "without-password", "prohibit-password"):
        record_hit(
            f"SSH Root Login Disabled (PermitRootLogin {ssh_config['permit_root_login_value']}).", 
            vulnerability[1]["Points"]
        )
    else:
        # PermitRootLogin is explicitly set to something insecure (e.g., "yes")
        record_miss("Local Policy")


def is_kernel_running(expected_version, running_kernel):
    """
    Helper function to check if the expected kernel version is currently running.
    
    Args:
        expected_version (str): Expected kernel version (e.g., "5.15.0-92")
        running_kernel (str): Currently running kernel from uname (e.g., "5.15.0-92-generic")
    
    Returns:
        bool: True if running kernel matches expected version, False otherwise
    """
    import re
    
    # Extract version numbers from both strings for comparison
    # Expected: "5.15.0-92" -> [5, 15, 0, 92]
    # Running: "5.15.0-92-generic" -> [5, 15, 0, 92]
    expected_nums = [int(n) for n in re.findall(r'\d+', expected_version)]
    running_nums = [int(n) for n in re.findall(r'\d+', running_kernel)]
    
    # Compare the first 4 version numbers (major.minor.patch-build)
    # Ignore any trailing numbers (like architecture variants)
    if len(expected_nums) >= 4 and len(running_nums) >= 4:
        return expected_nums[:4] == running_nums[:4]
    
    # Fallback: simple substring match
    return expected_version in running_kernel


def check_kernel(vulnerability):
    """
    Checks if the system kernel has been updated to the latest available version
    and is currently running. Handles both standard and HWE kernel tracks.
    Requires internet access to query repositories.
    """
    import subprocess
    import re
    
    try:
        # Step 1: Get the currently running kernel
        running_kernel = platform.uname().release
        # print(f"Running kernel: {running_kernel}")
        
        # Step 1.5: Detect Ubuntu base version (important for derivatives like Mint)
        ubuntu_version = None
        try:
            # Get both VERSION_ID and UBUNTU_CODENAME from /etc/os-release
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if line.startswith('UBUNTU_CODENAME='):
                        # For Ubuntu-based distros like Mint, use UBUNTU_CODENAME
                        ubuntu_codename = line.split('=')[1].strip().strip('"')
                    elif line.startswith('VERSION_ID=') and not ubuntu_version:
                        # Fallback to VERSION_ID if no UBUNTU_CODENAME
                        version_id = line.split('=')[1].strip().strip('"')
                        # Only use if it looks like Ubuntu version (X.XX format)
                        if '.' in version_id and len(version_id) <= 5:
                            ubuntu_version = version_id
            
            # Map Ubuntu codenames to version numbers (for HWE package naming)
            ## DEVNOTE: This mapping may need to be updated for future releases, and is needed because linux mint is weird.
            codename_to_version = {
                'noble': '24.04',
                'mantic': '23.10',
                'lunar': '23.04',
                'jammy': '22.04',
                'focal': '20.04',
                'bionic': '18.04',
                'xenial': '16.04',
            }
            
            # Prefer UBUNTU_CODENAME mapping, fallback to VERSION_ID
            # if ubuntu_codename and ubuntu_codename in codename_to_version:
            #     ubuntu_version = codename_to_version[ubuntu_codename]
            #     print(f"Detected Ubuntu base: {ubuntu_version} (codename: {ubuntu_codename})")
            # elif ubuntu_version:
            #     print(f"Detected Ubuntu version: {ubuntu_version}")
            # else:
            #     print("Warning: Could not determine Ubuntu version")
                
        except FileNotFoundError:
            print("Warning: Could not detect Ubuntu version from /etc/os-release")
        
        # Step 2: Detect if system uses HWE kernel or standard kernel
        # Check which meta-package is installed
        hwe_package_name = None
        uses_hwe = False
        
        if ubuntu_version:
            # Try version-specific HWE package first
            hwe_package_name = f"linux-image-generic-hwe-{ubuntu_version}"
            hwe_check = subprocess.run(
                ["dpkg", "-l", hwe_package_name],
                capture_output=True,
                text=True
            )
            
            if hwe_check.returncode == 0:
                for line in hwe_check.stdout.splitlines():
                    if line.startswith("ii"):
                        uses_hwe = True
                        break
        # If version-specific HWE not found, try generic HWE package
        if not uses_hwe:
            hwe_package_name = "linux-image-generic-hwe"
            hwe_check = subprocess.run(
                ["dpkg", "-l", hwe_package_name],
                capture_output=True,
                text=True
            )
            
            if hwe_check.returncode == 0:
                for line in hwe_check.stdout.splitlines():
                    if line.startswith("ii"):
                        uses_hwe = True
                        break
        
        # Determine which meta-package to query
        if uses_hwe:
            meta_package = hwe_package_name
            # print(f"System uses HWE kernel track: {meta_package}")
        else:
            meta_package = "linux-image-generic"
            # print("System uses standard kernel track")
        
        # Step 3: Query apt cache for latest available kernel version
        # print(f"Querying repositories for latest {meta_package} version...")
        apt_result = subprocess.run(
            ["apt-cache", "policy", meta_package],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the "Candidate" line which shows the latest available version
        latest_available_version = None
        for line in apt_result.stdout.splitlines():
            if "Candidate:" in line:
                latest_available_version = line.split("Candidate:")[1].strip()
                break
        
        if not latest_available_version or latest_available_version == "(none)":
            # print("ERROR: Could not determine latest available kernel version")
            # print("Ensure internet connection is available and 'sudo apt update' has been run")
            record_miss("Local Policy")
            return
        
        # print(f"Latest available kernel meta-package version: {latest_available_version}")
        
        # Step 4: Determine the actual kernel image package version from the meta-package
        depends_result = subprocess.run(
            ["apt-cache", "depends", meta_package],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Find the "Depends: linux-image-X.X.X-XX-generic" line
        latest_kernel_image = None
        for line in depends_result.stdout.splitlines():
            if "Depends:" in line and "linux-image-" in line:
                match = re.search(r'linux-image-[\d\.]+-\d+-\w+', line)
                if match:
                    latest_kernel_image = match.group(0)
                    break
        
        if not latest_kernel_image:
            print("ERROR: Could not determine latest kernel image package")
            record_miss("Local Policy")
            return
        
        # Extract version from package name
        latest_kernel_version = latest_kernel_image.replace("linux-image-", "").replace("-generic", "")
        # print(f"Latest available kernel version: {latest_kernel_version}")
        
        # Step 5: Check if the latest kernel package is installed
        installed_check = subprocess.run(
            ["dpkg", "-l", latest_kernel_image],
            capture_output=True,
            text=True
        )
        
        is_installed = False
        if installed_check.returncode == 0:
            for line in installed_check.stdout.splitlines():
                if line.startswith("ii") and latest_kernel_image in line:
                    is_installed = True
                    break
        
        if not is_installed:
            # print(f"Latest kernel {latest_kernel_image} is NOT installed")
            # print(f"Run 'sudo apt update && sudo apt upgrade' to install")
            record_miss("Local Policy")
            return
        
        print(f"Latest kernel {latest_kernel_image} is installed ✓")
        
        # Step 6: Check if the installed latest kernel is actually running
        if not is_kernel_running(latest_kernel_version, running_kernel):
            # print(f"Latest kernel {latest_kernel_version} is installed but NOT running")
            # print(f"Currently running: {running_kernel}")
            # print("Reboot required to load the new kernel")
            record_miss("Local Policy")
            return
        
        # Step 7: Success - latest kernel is both installed and running
        # print(f"✓ Kernel updated to latest version and running: {running_kernel}")
        record_hit(
            f"Kernel updated to latest version ({running_kernel})",
            vulnerability[1]["Points"]
        )
        
    except subprocess.CalledProcessError as e:
        print(f"Error checking kernel (ensure internet connection and apt cache is updated): {e}")
        record_miss("Local Policy")
    except Exception as e:
        print(f"Unexpected error in check_kernel: {e}")
        import traceback
        traceback.print_exc()
        record_miss("Local Policy")


def programs(vulnerability, name):
    """
    Checks for the presence or absence of specific programs and records hits/misses.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
        name (str): The type of program check (Good Program, Bad Program, etc.).
    """
    match name:
        case "Good Program":
            for vuln in vulnerability:
                if vuln != 1:
                    if vulnerability[vuln]["Program Name"] in program_content:
                        record_hit(
                            vulnerability[vuln]["Program Name"] + " is installed",
                            vulnerability[vuln]["Points"],
                        )
                    else:
                        record_miss("Program Management")
        case "Bad Program":
            for vuln in vulnerability:
                if vuln != 1:
                    if vulnerability[vuln]["Program Name"] not in program_content:
                        record_hit(
                            vulnerability[vuln]["Program Name"] + " is not installed",
                            vulnerability[vuln]["Points"],
                        )
                    else:
                        record_miss("Program Management")
        case "Update Program":
            for vuln in vulnerability:
                if vuln != 1:
                    program_name = vulnerability[vuln]["Program Name"]
                    expected_version = vulnerability[vuln]["Version"]
                    
                    # Find the package in program_versions list
                    package_found = False
                    version_matches = False
                    
                    for package in program_versions:
                        if package["name"] == program_name:
                            package_found = True
                            if package["version"] == expected_version:
                                version_matches = True
                            break
                    
                    if package_found and version_matches:
                        record_hit(
                            program_name + " updated to version " + expected_version,
                            vulnerability[vuln]["Points"],
                        )
                    else:
                        record_miss("Program Management")


def critical_programs(vulnerability):
    """
    Checks for critical programs and records penalties if they are removed.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    for vuln in vulnerability:
        if vuln != 1:
            program_name = vulnerability[vuln]["Program Name"]
            # Penalize if critical program has been removed
            if program_name not in program_content:
                record_penalty(
                    f"Critical program {program_name} was removed",
                    vulnerability[vuln]["Points"],
                )


# wip
def anti_virus(vulnerability):
    """
    Checks if antivirus protection is enabled and records hits/misses.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    z = open("security.txt", "r", encoding="utf-16-le")
    content = z.read()
    z.close()
    if "Real-time Protection Status : Enabled" in content:
        record_hit("Virus & threat protection enabled.", vulnerability[1]["Points"])
    else:
        record_miss("Security")


# test
def bad_file(vulnerability):
    """
    Checks for the existence of specific files or directories and records hits/misses based on their presence.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    for vuln in vulnerability:
        if vuln != 1:
            # Support both Object Path (new) and File Path (old) for backward compatibility
            file_path = vulnerability[vuln].get("Object Path") or vulnerability[vuln].get("File Path", "")
            if not file_path:
                continue
            if not os.path.exists(file_path):
                record_hit(
                    "The item "
                    + file_path
                    + " has been removed.",
                    vulnerability[vuln]["Points"],
                )
            else:
                record_miss("File Management")


def get_user_permission_on_file(username, file_path):
    """
    Determine what permission level a specific user has on a file or directory.
    
    Args:
        username (str): The username to check permissions for.
        file_path (str): The path to the file or directory.
    
    Returns:
        int: The permission octal digit (0-7) that applies to this user.
             Returns owner permissions if user owns the file,
             group permissions if user is in the file's group,
             other permissions otherwise.
             Returns None if the file doesn't exist or user doesn't exist.
    """
    try:
        # Get file stats
        stat_info = os.stat(file_path)
        file_mode = stat_info.st_mode
        file_uid = stat_info.st_uid
        file_gid = stat_info.st_gid
        
        # Get user info
        user_info = getpwnam(username)
        user_uid = user_info.pw_uid
        
        # Get all groups the user belongs to
        user_groups = [g.gr_gid for g in grp.getgrall() if username in g.gr_mem]
        # Also add the user's primary group
        user_groups.append(user_info.pw_gid)
        
        # Determine which permission bits apply
        if user_uid == file_uid:
            # User is the owner - return owner permissions (first octal digit)
            return (file_mode >> 6) & 0o7
        elif file_gid in user_groups:
            # User is in the file's group - return group permissions (second octal digit)
            return (file_mode >> 3) & 0o7
        else:
            # User is neither owner nor in group - return other permissions (third octal digit)
            return file_mode & 0o7
            
    except (FileNotFoundError, PermissionError, KeyError, OSError) as e:
        print(f"Error checking permissions for user {username} on {file_path}: {e}")
        return None


def permission_checks(vulnerability):
    """
    Checks file permissions for specific users against expected values and records hits/misses.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    for vuln in vulnerability:
        if vuln != 1:
            # Get the file path
            file_path = vulnerability[vuln].get("Object Path")
            if not file_path:
                continue
            
            # Get the username and expected permission
            username = vulnerability[vuln].get("Users to Modify")
            expected_perm_str = vulnerability[vuln].get("Permissions(R/W/X)", "")
            
            # Validate inputs - only username is required
            if not username:
                print(f"Warning: Missing username for {file_path}")
                record_miss("File Management")
                continue
            
            try:
                # Get expected permission as integer (0-7), treat empty string as 0
                expected_perm = int(expected_perm_str or "0")
                
                # Get the actual permission this user has on the file
                actual_perm = get_user_permission_on_file(username, file_path)
                if actual_perm is None:
                    # Error getting permissions (file doesn't exist, user doesn't exist, etc.)
                    print(f"Warning: Could not check permissions for user '{username}' on '{file_path}'")
                    record_miss("File Management")
                    continue
                
                # Compare actual vs expected
                if actual_perm == expected_perm:
                    record_hit(
                        f"User '{username}' has correct permissions ({actual_perm}) on {file_path}.",
                        vulnerability[vuln]["Points"],
                    )
                else:
                    record_miss("File Management")
                    
            except (ValueError, KeyError, FileNotFoundError, OSError) as e:
                print(f"Error checking permissions for {file_path}: {e}")
                record_miss("File Management")


def no_scoring_available(name):
    """
    Displays an error message if no scoring definition is available for a given name.
    
    Args:
        name (str): The name of the item with no scoring definition.
    """
    print(f"ERROR: No scoring definition for '{name}'. Please remove this option if you are the image creator, if you are a competitor ignore this message.")


def load_policy_settings():
    """
    Loads policy and password settings from multiple configuration files.
    
    Returns:
        tuple: A tuple containing:
            - login_defs_list (list): Key-value pairs from /etc/login.defs
            - pamd_defs_list (list): Password lines from /etc/pam.d/common-password
            - password_settings (dict): Password settings from /etc/security/pwquality.conf
            - common_auth_list (list): Auth lines from /etc/pam.d/common-auth
            - faillock_settings (dict): Faillock settings from /etc/security/faillock.conf
    """
    # Load /etc/login.defs settings
    with open("/etc/login.defs", "r") as file:
        lines = file.readlines()
    login_defs_list = []

    # Scans through each line in the file and extracts key-value pairs
    for line in lines:
        line = line.strip()
        if not line.startswith("#") and line: # Ignore comments and empty lines
            key, value = line.split()
            login_defs_list.append((key, value))



    # Load /etc/pam.d/common-password settings
    pamd_defs_list = []
    with open("/etc/pam.d/common-password", "r") as common_password_file:
        for line in common_password_file:
            line = line.strip()
            if line.startswith("password"):
                pamd_defs_list.append(line)

    # Load /etc/pam.d/common-auth settings
    common_auth_list = []
    try:
        with open("/etc/pam.d/common-auth", "r") as common_auth_file:
            for line in common_auth_file:
                line = line.strip()
                if line.startswith("auth"):
                    common_auth_list.append(line)
    except FileNotFoundError:
        pass  # File may not exist on all systems

    # Load /etc/security/pwquality.conf settings
    password_settings = {}
    with open("/etc/security/pwquality.conf", "r") as file:
        lines = file.readlines()
    for line in lines:
        line = line.strip()
        if line and "=" in line:
            key, value = line.split("=")
            key = key.strip().lstrip("# ")
            password_settings[key.strip()] = value.strip()

    # Load /etc/security/faillock.conf settings
    faillock_settings = {}
    try:
        with open("/etc/security/faillock.conf", "r") as file:
            lines = file.readlines()
        for line in lines:
            line = line.strip()
            # Skip comments and empty lines
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)  # Split on first = only
                key = key.strip()
                value = value.strip()
                faillock_settings[key] = value
    except FileNotFoundError:
        pass  # File may not exist on all systems

    return login_defs_list, pamd_defs_list, password_settings, common_auth_list, faillock_settings


def get_chage_info():
    """
    Gets password aging information for a user using chage command.
    Creates a temporary test user to verify the actual effective password aging settings
    from system configuration, then cleans up the test user.
    Uses pwmake to generate a password that meets all system requirements.
    
    Returns:
        dict: Dictionary containing password aging information, or empty dict on error.
    """
    test_username = "csel_pwtest_user"
    
    try:
        # Generate a password that meets system requirements using pwmake
        # pwmake generates passwords with entropy of specified bits (default 128)
        try:
            pwmake_result = subprocess.run(
                ["pwmake", "128"],
                capture_output=True,
                text=True,
                check=True
            )
            test_password = pwmake_result.stdout.strip()
            
            if not test_password:
                # Fallback to a strong password if pwmake fails
                print("Warning: pwmake returned empty password, using fallback")
                test_password = "TempP@ss123!Secure"
        except (subprocess.CalledProcessError, FileNotFoundError):
            # pwmake not available, use a strong fallback password
            print("Warning: pwmake not available, using fallback password")
            test_password = "TempP@ss123!Secure"
        
        # Create a temporary test user to check actual system password policies
        # This user will inherit the system's default password aging settings
        create_result = subprocess.run(
            ["useradd", "-m", "-s", "/bin/bash", test_username],
            capture_output=True,
            text=True,
            check=False
        )
        
        if create_result.returncode != 0:
            # User might already exist, try to use it anyway
            print(f"Note: Test user {test_username} may already exist, continuing...")
        
        # Set the generated password for the test user
        # Use chpasswd with the generated password
        passwd_result = subprocess.run(
            ["chpasswd"],
            input=f"{test_username}:{test_password}",
            capture_output=True,
            text=True,
            check=False
        )
        
        if passwd_result.returncode != 0:
            print(f"Warning: Could not set password for test user {test_username}")
            print(f"Error: {passwd_result.stderr}")
        
        # Now get the chage info for this test user
        # This will show the actual system defaults that are enforced
        result = subprocess.run(
            ["chage", "-l", test_username],
            capture_output=True,
            text=True,
            check=True
        )
        
        chage_info = {}
        for line in result.stdout.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                
                # Parse specific fields we care about
                if "Minimum number of days between password change" in key:
                    try:
                        chage_info["min_days"] = int(value)
                    except (ValueError, TypeError):
                        chage_info["min_days"] = 0
                elif "Maximum number of days between password change" in key:
                    try:
                        chage_info["max_days"] = int(value)
                    except (ValueError, TypeError):
                        chage_info["max_days"] = 99999
        
        # Clean up: delete the test user and their home directory
        cleanup_result = subprocess.run(
            ["userdel", "-r", test_username],
            capture_output=True,
            text=True,
            check=False
        )
        
        if cleanup_result.returncode != 0:
            print(f"Warning: Could not fully clean up test user {test_username}")
                        
        return chage_info
        
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        # Attempt cleanup even on error
        try:
            subprocess.run(
                ["userdel", "-r", test_username],
                capture_output=True,
                text=True,
                check=False
            )
        except:
            pass
        
        print(f"Warning: Could not get chage info using test user: {e}")
        return {}


def test_password_requirements(requirements, password_settings_content=None, pamd_policy_settings_content=None, login_policy_settings_content=None, username_to_test=None, password_change_date=None):
    """
    Tests password requirements using pwscore/pwmake to verify they're actually enforced.
    Tracks when requirements are first fully configured and compares with password change date.
    
    Args:
        requirements (dict): Dictionary of password requirements to test.
                           Supported keys: 'minlen', 'dcredit', 'ucredit', 'lcredit', 'ocredit'
        password_settings_content (dict): Password settings from /etc/security/pwquality.conf
        pamd_policy_settings_content (list): PAM password lines from /etc/pam.d/common-password
        login_policy_settings_content (list): Key-value pairs from /etc/login.defs
        username_to_test (str): Username to track configuration timestamps for.
        password_change_date (datetime): Date when the user's password was changed.
    
    Returns:
        dict: Results dictionary with keys for each requirement tested.
              Format: {
                  'minlen': {'configured': True/False, 'enforced': True/False, 'actual_value': int},
                  'dcredit': {...},
                  ...,
                  'password_passes': True/False  # Only present if username_to_test is provided
              }
              Keys:
                configured: Indicates if the requirement is configured as expected in the configurator.
                enforced: Indicates if the requirement is actually enforced by the system(not just configured, useful for changing standards).
                actual_value: The actual value found in system configuration.
                password_passes: If username_to_test is provided, indicates if password was changed after all requirements were configured.
    """
    results = {}
    
    # Check if pwscore/pwmake are available
    try:
        subprocess.run(["which", "pwscore"], capture_output=True, check=True)
        has_pwscore = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        has_pwscore = False
        print("Warning: pwscore not available. Install libpwquality-tools for password quality testing.")
        return results
    
    # Test minimum password length
    if 'minlen' in requirements and requirements['minlen']:
        try:
            expected_value = int(requirements['minlen'])
            
            # Check configuration sources in priority order:
            # 1. Check if pam_pwquality.so exists in /etc/pam.d/common-password
            #    a. If it exists AND has minlen argument, use that value
            #    b. If it exists but NO minlen argument, check /etc/security/pwquality.conf
            # 2. If pam_pwquality.so doesn't exist at all, fallback to /etc/login.defs
            actual_value = None
            pam_pwquality_exists = False
            
            # Parse PAM data to check for pam_pwquality.so and extract module settings
            if pamd_policy_settings_content:
                pam_settings_dict = {}
                for pam_line in pamd_policy_settings_content:
                    normalized_line = pam_line.replace('\\t', '\t')
                    parts = re.split(r'[\t\s]+', normalized_line.strip())
                    parts = [p for p in parts if p]
                    
                    if len(parts) >= 3:
                        module_path = parts[2]
                        
                        # Check if pam_pwquality.so is present
                        if 'pam_pwquality.so' in module_path:
                            pam_pwquality_exists = True
                            # Extract module options
                            if len(parts) > 3:
                                for option in parts[3:]:
                                    if '=' in option:
                                        key, value = option.split('=', 1)
                                        pam_settings_dict[key.strip()] = value.strip()
                
                # If pam_pwquality.so exists, check for minlen argument
                if pam_pwquality_exists:
                    if 'minlen' in pam_settings_dict:
                        # Priority 1a: minlen argument in pam_pwquality.so line
                        try:
                            actual_value = int(pam_settings_dict['minlen'])
                        except (ValueError, TypeError):
                            pass
                    
                    # If no minlen argument, check pwquality.conf
                    if actual_value is None and password_settings_content and 'minlen' in password_settings_content:
                        # Priority 1b: /etc/security/pwquality.conf (when pam_pwquality.so exists but has no minlen arg)
                        try:
                            actual_value = int(password_settings_content['minlen'])
                        except (ValueError, TypeError):
                            pass
            
            # Priority 2: Fallback to /etc/login.defs (if pam_pwquality.so doesn't exist or PAM settings unavailable)
            if actual_value is None and login_policy_settings_content:
                policy_settings_dict = dict(login_policy_settings_content)
                if 'PASS_MIN_LEN' in policy_settings_dict:
                    try:
                        actual_value = int(policy_settings_dict['PASS_MIN_LEN'])
                    except (ValueError, TypeError):
                        pass
            
            # Determine if configured based on EXACT match with expected value
            if actual_value is None:
                actual_value = 0
                configured = False
            elif actual_value == expected_value:
                configured = True
            else:
                configured = False
            
            results['minlen'] = {
                'configured': configured,
                'enforced': False,
                'actual_value': actual_value
            }
            
            # Only test enforcement if configured (actual matches expected) and value > 0
            if configured and expected_value > 0:
                # Generate a password that meets the length requirement using pwmake
                # Passing password should be EXACTLY expected_value length
                try:
                    pwmake_result = subprocess.run(
                        ["pwmake", "128"],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    passing_password = pwmake_result.stdout.strip()
                    
                    if not passing_password or len(passing_password) < expected_value:
                        # Fallback if pwmake returns empty or too short
                        print("Warning: pwmake returned insufficient password for passing test, using fallback")
                        passing_password = 'A' * (expected_value // 4) + 'a' * (expected_value // 4) + \
                                         '1' * (expected_value // 4) + '!' * (expected_value // 4) + \
                                         'Aa1!' * ((expected_value % 4))
                        passing_password = passing_password[:expected_value]
                    else:
                        # Truncate to be EXACTLY expected_value length
                        passing_password = passing_password[:expected_value]
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # pwmake not available, use fallback
                    print("Warning: pwmake not available for passing test, using fallback password")
                    passing_password = 'A' * (expected_value // 4) + 'a' * (expected_value // 4) + \
                                     '1' * (expected_value // 4) + '!' * (expected_value // 4) + \
                                     'Aa1!' * ((expected_value % 4))
                    passing_password = passing_password[:expected_value]
                
                # Generate a password that FAILS the length requirement (too short)
                # Use pwmake then truncate to be EXACTLY 1 character shorter than expected_value
                try:
                    pwmake_result = subprocess.run(
                        ["pwmake", "128"],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    failing_password = pwmake_result.stdout.strip()
                    
                    if not failing_password or len(failing_password) < expected_value:
                        # Fallback if pwmake returns empty or too short
                        print("Warning: pwmake returned insufficient password for failing test, using fallback")
                        failing_password = 'Aa1!' * max(1, (expected_value - 1) // 4)
                        failing_password = failing_password[:max(1, expected_value - 1)]
                    else:
                        # Truncate to be exactly 1 character shorter than expected_value
                        failing_password = failing_password[:max(1, expected_value - 1)]
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # pwmake not available, use fallback
                    print("Warning: pwmake not available for failing test, using fallback password")
                    failing_password = 'Aa1!' * max(1, (expected_value - 1) // 4)
                    failing_password = failing_password[:max(1, expected_value - 1)]
                
                # Test the passing password
                result_pass = subprocess.run(
                    ["pwscore"],
                    input=passing_password,
                    capture_output=True,
                    text=True
                )
                
                # Test the failing password
                result_fail = subprocess.run(
                    ["pwscore"],
                    input=failing_password,
                    capture_output=True,
                    text=True
                )
                
                # If passing password gets a good score and failing password gets rejected,
                # the requirement is enforced
                pass_score = 0
                fail_score = 0
                
                try:
                    pass_score = int(result_pass.stdout.strip())
                except (ValueError, AttributeError):
                    pass
                    
                # Check if failing password was rejected
                if result_fail.returncode != 0 or "too short" in result_fail.stderr.lower():
                    results['minlen']['enforced'] = True
                elif pass_score > 0 and fail_score == 0:
                    results['minlen']['enforced'] = True
                
        except (ValueError, TypeError, subprocess.SubprocessError) as e:
            print(f"Error testing minlen requirement: {e}")
            results['minlen'] = {
                'configured': False,
                'enforced': False,
                'actual_value': 0,
                'error': str(e)
            }
    
    # Placeholder for future requirement tests (uppercase, lowercase, digits, special chars)
    # These can be expanded as needed
    for req_type in ['dcredit', 'ucredit', 'lcredit', 'ocredit']:
        if req_type in requirements and requirements[req_type]:
            results[req_type] = {
                'configured': True,
                'enforced': False,  # Will implement testing in future
                'actual_value': requirements[req_type],
                'note': 'Testing not yet implemented'
            }
    
    ### USER CHANGE PASSWORD TESTING ###
    # If username is provided, track configuration timestamps and validate password change
    if username_to_test and password_change_date:
        # Check if all requirements are currently configured
        all_configured = all(result.get('configured', False) for result in results.values() if isinstance(result, dict))
        
        # Load existing timestamps
        timestamps = load_config_timestamps()
        
        if all_configured:
            # All requirements are configured
            if username_to_test not in timestamps:
                # First time all requirements are configured - save timestamp
                current_time = datetime.datetime.now()
                timestamps[username_to_test] = {
                    'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'requirements': requirements.copy(),
                    'validated_hash': None  # Will be set when password passes
                }
                save_config_timestamps(timestamps)
                print(f"INFO: Saved configuration timestamp for {username_to_test}: {current_time}")
            
            # OPTIMIZATION: Check if password hash changed since last validation
            current_hash = get_password_hash(username_to_test)
            stored_hash = timestamps[username_to_test].get('validated_hash')
            
            # If hash unchanged and we've already validated it, skip expensive re-validation
            if current_hash and stored_hash and current_hash == stored_hash:
                # Password hasn't changed since last successful validation
                results['password_passes'] = True
            else:
                # Hash changed or first check - perform full validation
                if username_to_test in timestamps:
                    config_timestamp_str = timestamps[username_to_test]['timestamp']
                    config_timestamp = datetime.datetime.strptime(config_timestamp_str, '%Y-%m-%d %H:%M:%S')
                    
                    # Password passes if it was changed AFTER all requirements were configured
                    password_passes = password_change_date >= config_timestamp
                    results['password_passes'] = password_passes
                    
                    # If password passes, save the hash to skip re-validation next time
                    if password_passes and current_hash:
                        timestamps[username_to_test]['validated_hash'] = current_hash
                        save_config_timestamps(timestamps)

                else:
                    # Should not happen, but handle gracefully
                    results['password_passes'] = False
        else:
            # Not all requirements are configured - clear timestamp and fail
            if username_to_test in timestamps:
                del timestamps[username_to_test]
                save_config_timestamps(timestamps)
                print(f"INFO: Cleared configuration data for {username_to_test} - requirements no longer fully configured")
            
            results['password_passes'] = False
    
    return results


def get_file_names_in_directory(directory):
    """
    Retrieves all file names in a specified directory and its subdirectories.
    
    Args:
        directory (str): The directory to search.
    
    Returns:
        list: A list of file names found in the directory.
    """
    file_names = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            file_names.append(filename)
    return file_names


def load_programs():
    """
    Loads the names of installed programs from /usr/bin and /snap/bin directories.
    
    Returns:
        set: A set of all installed program names.
    """
    usr_bin_file_names = get_file_names_in_directory("/usr/bin")
    usr_sbin_file_names = get_file_names_in_directory("/usr/sbin")
    snap_bin_file_names = get_file_names_in_directory("/snap/bin")
    games_bin_file_names = get_file_names_in_directory("/usr/games")

    all_file_names = usr_bin_file_names + usr_sbin_file_names + snap_bin_file_names + games_bin_file_names
    return set(all_file_names)


def load_versions():
    """
    Loads the installed package versions using dpkg and returns them as a list.
    
    Returns:
        list: A list of dictionaries containing package names and their versions.
    """
    command = "dpkg -l"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        installed_packages = result.stdout.splitlines()[5:]  # Skip the header lines
    else:
        installed_packages = []

    package_list = []
    for line in installed_packages:
        parts = line.split()
        package_name = parts[1]
        package_version = parts[2]
        package_list.append({"name": package_name, "version": package_version})
    return package_list


def setup_program_inotify():
    """
    Sets up inotify watchers for program directories.
    
    Returns:
        INotify: An inotify instance watching program directories.
    """
    inotify = INotify()
    watch_flags = flags.CREATE | flags.DELETE | flags.MOVED_TO | flags.MOVED_FROM
    
    # Watch program directories
    directories = ["/usr/bin", "/usr/sbin", "/snap/bin", "/usr/games"]
    for directory in directories:
        if os.path.exists(directory):
            try:
                inotify.add_watch(directory, watch_flags)
            except Exception as e:
                print(f"WARNING: Could not watch {directory}: {e}")
    
    return inotify


def setup_versions_inotify():
    """
    Sets up inotify watcher for dpkg status file.
    
    Returns:
        INotify: An inotify instance watching dpkg status file.
    """
    inotify = INotify()
    watch_flags = flags.MODIFY | flags.CLOSE_WRITE
    
    dpkg_status = "/var/lib/dpkg/status"
    if os.path.exists(dpkg_status):
        try:
            inotify.add_watch(dpkg_status, watch_flags)
        except Exception as e:
            print(f"WARNING: Could not watch {dpkg_status}: {e}")
    
    return inotify


def check_program_changes(inotify_watcher):
    """
    Non-blocking check for program directory changes.
    
    Args:
        inotify_watcher (INotify): The inotify instance watching program directories.
    
    Returns:
        bool: True if changes detected, False otherwise.
    """
    try:
        # Non-blocking read with 0 timeout
        events = inotify_watcher.read(timeout=0, read_delay=0)
        if events:
            print(f"INFO: Detected {len(events)} program directory change(s)")
            return True
    except Exception:
        pass  # No events available
    return False


def check_version_changes(inotify_watcher):
    """
    Non-blocking check for dpkg status file changes.
    
    Args:
        inotify_watcher (INotify): The inotify instance watching dpkg status.
    
    Returns:
        bool: True if changes detected, False otherwise.
    """
    try:
        # Non-blocking read with 0 timeout
        events = inotify_watcher.read(timeout=0, read_delay=0)
        if events:
            print(f"INFO: Detected dpkg database change")
            return True
    except Exception:
        pass  # No events available
    return False


def setup_policy_inotify():
    """
    Sets up inotify watchers for PAM and security policy configuration paths.

    Watches:
      - /etc/pam.d/       — covers common-password, common-auth, etc.
      - /etc/security/    — covers faillock.conf, pwquality.conf, etc.
      - /etc/login.defs   — password-aging settings (min/max days)

    Returns:
        INotify: An inotify instance watching all policy-related paths.
    """
    inotify = INotify()
    dir_flags  = flags.MODIFY | flags.CLOSE_WRITE | flags.CREATE | flags.DELETE | flags.MOVED_TO | flags.MOVED_FROM
    file_flags = flags.MODIFY | flags.CLOSE_WRITE

    for path in ("/etc/pam.d", "/etc/security"):
        if os.path.exists(path):
            try:
                inotify.add_watch(path, dir_flags)
            except Exception as e:
                print(f"WARNING: Could not watch {path}: {e}")

    if os.path.exists("/etc/login.defs"):
        try:
            inotify.add_watch("/etc/login.defs", file_flags)
        except Exception as e:
            print(f"WARNING: Could not watch /etc/login.defs: {e}")

    return inotify


def check_policy_changes(inotify_watcher):
    """
    Non-blocking check for PAM / security policy file changes.

    Args:
        inotify_watcher (INotify): The inotify instance watching policy paths.

    Returns:
        bool: True if any changes were detected, False otherwise.
    """
    try:
        events = inotify_watcher.read(timeout=0, read_delay=0)
        if events:
            changed = {e.name for e in events if e.name}
            label = ", ".join(sorted(changed)) if changed else "unknown file"
            print(f"INFO: Policy file change detected ({label}) — re-running local policy checks")
            return True
    except Exception:
        pass
    return False


def setup_ssh_config_inotify():
    """
    Sets up inotify watcher for SSH configuration file.

    Watches:
      - /etc/ssh/sshd_config — SSH server configuration

    Returns:
        INotify: An inotify instance watching SSH config file.
    """
    inotify = INotify()
    file_flags = flags.MODIFY | flags.CLOSE_WRITE
    
    if os.path.exists("/etc/ssh/sshd_config"):
        try:
            inotify.add_watch("/etc/ssh/sshd_config", file_flags)
        except Exception as e:
            print(f"WARNING: Could not watch /etc/ssh/sshd_config: {e}")
    
    return inotify


def check_ssh_config_changes(inotify_watcher):
    """
    Non-blocking check for SSH config file changes.

    Args:
        inotify_watcher (INotify): The inotify instance watching sshd_config.

    Returns:
        bool: True if any changes were detected, False otherwise.
    """
    try:
        events = inotify_watcher.read(timeout=0, read_delay=0)
        if events:
            print(f"INFO: SSH config file change detected — re-checking SSH settings")
            return True
    except Exception:
        pass
    return False


def load_services():

    # Run the systemctl command to list all services
    command = [
        "systemctl",
        "list-units",
        "--type=service",
        "--all",
        "--no-pager",
        "--plain",
    ]
    result = subprocess.run(command, capture_output=True, text=True)

    # Check if the command was successful
    if result.returncode == 0:
        services_output = result.stdout

        # Split the output into lines
        services_lines = services_output.splitlines()

        service_data = []
        # Process each line and create a dictionary
        for line in services_lines:
            words = line.split()
            if words == []:
                break
            else:
                # Define dictionary keys and extract values from words
                service = {
                    "unit": words[0],
                    "load": words[1],
                    "active": words[2],
                    "sub": words[3],
                    "description": " ".join(words[4:]),
                }
                service_data.append(service)
        # Print the dictionary for the current line
        return service_data
    else:
        return result.stderr


# check1
def process_vulnerability(vuln, vulnerability_def):
    """
    Helper function to process a single vulnerability check.
    Determines if the function needs 1 or 2 arguments and calls it appropriately.
    
    Args:
        vuln: Vulnerability template object with .name property
        vulnerability_def (dict): Dictionary mapping vulnerability names to their check functions
    """
    vulnerability = Vulnerabilities.get_option_table(vuln.name, False)
    if vulnerability[1]["Enabled"]:
        func = vulnerability_def[vuln.name]
        # Check if function takes 1 or 2 arguments
        if len(getfullargspec(func).args) == 1:
            func(vulnerability)
        else:
            func(vulnerability, vuln.name)


def account_management(vulnerabilities):
    """
    Manages user accounts based on the provided vulnerabilities and records hits/misses.
    
    Args:
        vulnerabilities (list): A list of vulnerabilities to check.
    """
    write_to_html("<H3>USER MANAGEMENT</H3>")
    vulnerability_def = {
        "Add Admin": group_manipulation,
        "Remove Admin": group_manipulation,
        "Add User to Group": group_manipulation,
        "Remove User from Group": group_manipulation,
        "Add User": users_manipulation,
        "Remove User": users_manipulation,
        "User Change Password": user_change_password,
        "Critical Users": critical_users,
    }
    for vuln in vulnerabilities:
        if "Critical" in vuln.name:
            critical_items.append(vuln)
        else:
            process_vulnerability(vuln, vulnerability_def)

def local_policies(vulnerabilities):
    """
    Manages local security policies based on the provided vulnerabilities and records hits/misses.

    Uses caching for password-policy checks (which depend on PAM/security files tracked by inotify).
    Other checks (like kernel version, SSH config) are always executed.

    Args:
        vulnerabilities (list): A list of vulnerabilities to check.
    """
    global _capturing_policy_events

    write_to_html("<H3>SECURITY POLICIES</H3>")

    # Define which vulnerability types use the cache (only those depending on tracked policy files)
    CACHED_POLICY_TYPES = {
        "Minimum Password Age",
        "Maximum Password Age", 
        "Minimum Password Length",
        "Maximum Login Tries",
        "Lockout Duration",
        "Lockout Reset Duration",
        "Password History",
    }

    # Separate vulnerabilities into cached and non-cached
    cached_vulns = []
    non_cached_vulns = []
    
    for vuln in vulnerabilities:
        if vuln.name in CACHED_POLICY_TYPES:
            cached_vulns.append(vuln)
        else:
            non_cached_vulns.append(vuln)

    # ── Process cached vulnerabilities (PAM/security policy checks) ────────────
    if _local_policy_cache_valid and local_policy_cache['populated'] and cached_vulns:
        # Replay cached results for policy checks
        for event in local_policy_cache['events']:
            if event[0] == 'hit':
                record_hit(event[1], event[2])
            elif event[0] == 'miss':
                record_miss(event[1])
            elif event[0] == 'penalty':
                record_penalty(event[1], event[2])
    else:
        # Re-run cached policy checks and capture results
        local_policy_cache['events'] = []
        _capturing_policy_events = True
        try:
            vulnerability_def = {
                "Minimum Password Age": local_group_policy,
                "Maximum Password Age": local_group_policy,
                "Minimum Password Length": local_group_policy,
                "Maximum Login Tries": local_group_policy,
                "Lockout Duration": local_group_policy,
                "Lockout Reset Duration": local_group_policy,
                "Password History": local_group_policy,
            }
            for vuln in cached_vulns:
                process_vulnerability(vuln, vulnerability_def)
        finally:
            _capturing_policy_events = False
            local_policy_cache['populated'] = True

    # ── Always process non-cached vulnerabilities ─────────────────────────────
    vulnerability_def = {
        "Check Kernel": check_kernel,
        "Disable SSH Root Login": local_group_policy,
        "Audit": local_group_policy
    }
    for vuln in non_cached_vulns:
        process_vulnerability(vuln, vulnerability_def)



def program_management(vulnerabilities):
    """
    Manages installed programs based on the provided vulnerabilities and records hits/misses.
    
    Args:
        vulnerabilities (list): A list of vulnerabilities to check.
    """
    write_to_html("<H3>PROGRAMS</H3>")
    vulnerability_def = {
        "Good Program": programs,
        "Bad Program": programs,
        "Update Program": programs,
        "Services": manage_services,
        "Update Check Period": update_check_period,
    }
    # vulnerability_def = {"Good Program": programs, "Bad Program": programs, "Update Program": no_scoring_available, "Add Feature": no_scoring_available, "Remove Feature": no_scoring_available, "Services": manage_services}
    for vuln in vulnerabilities:
        if "Critical" in vuln.name:
            critical_items.append(vuln)
        else:
            process_vulnerability(vuln, vulnerability_def)


def file_management(vulnerabilities):
    """
    Manages file-related checks based on the provided vulnerabilities and records hits/misses.
    
    Args:
        vulnerabilities (list): A list of vulnerabilities to check.
    """
    write_to_html("<H3>FILE MANAGEMENT</H3>")
    vulnerability_def = {
        "Forensic": forensic_question,
        "Check Hosts": check_hosts,
        "Bad File/Directory": bad_file,
        "Bad File": bad_file,
        "Add Text to File": add_text_to_file,
        "Remove Text From File": remove_text_from_file,
        "File Permissions": permission_checks,
        "Check Startup": start_up_apps,
    }
    for vuln in vulnerabilities:
        process_vulnerability(vuln, vulnerability_def)


def firewall_management(vulnerabilities):
    """
    Manages firewall-related checks based on the provided vulnerabilities and records hits/misses.
    
    Args:
        vulnerabilities (list): A list of vulnerabilities to check.
    """
    write_to_html("<H3>FIREWALL MANAGEMENT</H3>")
    vulnerabilities
    vulnerability_def = {
        "Turn On Firewall": firewallVulns,
        "Check Port Open": portVulns,
        "Check Port Closed": portVulns,
    }
    for vuln in vulnerabilities:
        process_vulnerability(vuln, vulnerability_def)


def critical_functions(vulnerabilities):
    """
    Manages critical functions based on the provided vulnerabilities and records hits/misses.
    
    Args:
        vulnerabilities (list): A list of vulnerabilities to check.
    """
    write_to_html("<H4>Critical Functions:</H4>")
    vulnerability_def = {
        "Critical Users": critical_users,
        "Critical Programs": critical_programs,
        "Critical Services": critical_services,
    }
    for vuln in vulnerabilities:
        vulnerability = Vulnerabilities.get_option_table(vuln.name, False)
        if vulnerability[1]["Enabled"]:
            vulnerability_def[vuln.name](vulnerability)


"""
def policyCreation():
    with open('/etc/login.defs', 'r') as source, open(destination_file, 'w') as destination:
        for line in source:
            if not line.strip().startswith("#"):
                destination.write(line)
"""



try:
    Settings = db_handler.Settings()
    menuSettings = Settings.get_settings(False)
    Categories = db_handler.Categories()
    categories = Categories.get_categories()
    Vulnerabilities = db_handler.OptionTables()
    Vulnerabilities.initialize_option_table()
except KeyboardInterrupt:
    print("INFO: Scoring engine stopped by user.")
    sys.exit(0)
except Exception:
    f = open("scoring_engine.log", "a")
    e = traceback.format_exc()
    f.write(str(e))
    f.close()
    print("ERROR: The scoring engine has stopped working, a log has been saved to " + os.path.abspath("scoring_engine.log"))
    sys.exit()

prePoints = 0
password_requirements_cache = {}  # Cache for password requirements extracted from vulnerabilities
category_def = {
    "Account Management": account_management,
    "Local Policy": local_policies,
    "Program Management": program_management,
    "File Management": file_management,
    "Firewall Management": firewall_management,
}
Desktop = menuSettings["Desktop"]
# fix
index = "/var/www/CYBERPATRIOT"
scoreIndex = index + "/ScoreReport.html"

menuSettings = Settings.get_settings(False)
total_points = 0
total_vulnerabilities = 0
critical_items = []

# Build password requirements cache from all categories
password_requirements_cache = build_password_requirements_cache(categories, Vulnerabilities)

# --------- Main Loop --------- #
check_runas()
iterations = 0

# Initialize inotify watchers and load initial data
program_inotify = setup_program_inotify()
version_inotify = setup_versions_inotify()
policy_inotify  = setup_policy_inotify()    # watches /etc/pam.d, /etc/security, /etc/login.defs
ssh_config_inotify = setup_ssh_config_inotify()  # watches /etc/ssh/sshd_config

# Load initial state
program_content = load_programs()
program_versions = load_versions()
# Policy settings are loaded on first loop iteration (cache not yet populated)

while True:
    try:
        # Reset scoring totals each loop to avoid cumulative double counting
        total_points = 0
        total_vulnerabilities = 0
        critical_items = []

        # DEVELOPING: Reload settings from database each iteration to catch configuration updates
        if developerMode:
            menuSettings = Settings.get_settings(False)
            # Build password requirements cache from all categories
            password_requirements_cache = build_password_requirements_cache(categories, Vulnerabilities)
        
        # Always reload services (fast and state-based)
        services_content = load_services()
        
        # Only reload programs if inotify detected changes
        if check_program_changes(program_inotify):
            program_content = load_programs()
            print("INFO: Program list reloaded due to file system changes")
        
        # Only reload versions if dpkg database changed
        if check_version_changes(version_inotify):
            program_versions = load_versions()
            print("INFO: Package versions reloaded due to dpkg changes")

        # Only reload policy settings and invalidate the local-policy cache when
        # inotify detects a write/create/delete inside /etc/pam.d or /etc/security,
        # or a write to /etc/login.defs — or on the very first iteration.
        if check_policy_changes(policy_inotify) or not local_policy_cache['populated']:
            _local_policy_cache_valid = False
            login_policy_settings_content, pamd_policy_settings_content, password_settings_content, common_auth_content, faillock_settings_content = load_policy_settings()
        else:
            # No changes detected — local_policies() will replay from cache
            _local_policy_cache_valid = True
        
        # Only invalidate SSH config cache when sshd_config changes or first iteration
        if check_ssh_config_changes(ssh_config_inotify) or not ssh_config_cache['populated']:
            _ssh_config_cache_valid = False
        else:
            # No changes detected — check_ssh_permit_root_login() will use cache
            _ssh_config_cache_valid = True

        print("Scoring Engine loop 1st:" + str(iterations))
        time.sleep(10)
        draw_head()

        # Grabs VulnerabilityTemplateModel object 
        for category in categories:
            category_def[category.name](
                Vulnerabilities.get_option_template_by_category(category.id)
            )
        critical_functions(critical_items)
        draw_tail()
        check_score()
        print("Scoring Engine loop 2nd:" + str(iterations))
        time.sleep(10)
    except KeyboardInterrupt:
        print("INFO: Scoring engine stopped by user.")
        sys.exit(0)
    except Exception:
        # ── Log the error ────────────────────────────────────────────────────
        log_path = os.path.abspath("scoring_engine.log")
        with open(log_path, "a") as f:                      # "a" = append, not overwrite
            f.write(f"\n{'='*60}\n")
            f.write(f"ERROR at {datetime.datetime.now()}\n")
            f.write(traceback.format_exc())
            f.write(f"{'='*60}\n")
        
        print(f"ERROR: Scoring engine loop failed — see {log_path}")

        # ── Write the error visibly into the score report ────────────────────
        # draw_head() already wrote the .tmp file — append the error before
        # draw_tail() would have closed it. If draw_head() itself failed,
        # we write a fresh error page directly.
        try:
            error_msg = traceback.format_exc().replace('\n', '<br>').replace(' ', '&nbsp;')
            write_to_html(
                f'<hr><p style="color:red;font-weight:bold;">&#9888; Scoring engine error — '
                f'check {log_path}</p>'
                f'<pre style="color:red;font-size:12px;">{error_msg}</pre>'
            )
            draw_tail()
        except Exception:
            # draw_head() likely never ran — write a standalone error page
            try:
                with open(scoreIndex, "w") as ef:
                    ef.write(
                        f'<!doctype html><html><head><title>CSEL Error</title>'
                        f'<meta http-equiv="refresh" content="30"></head>'
                        f'<body style="background-color:powderblue;">'
                        f'<h2 style="color:red;">&#9888; Scoring Engine Error</h2>'
                        f'<p>Check <code>{log_path}</code> for details.</p>'
                        f'</body></html>'
                    )
                os.chmod(scoreIndex, 0o777)
            except Exception:
                pass    # Absolute last resort — nothing more we can do

        # ── Keep the engine alive — sleep then retry next loop ───────────────
        print("INFO: Retrying in 30 seconds...")
        time.sleep(30)
