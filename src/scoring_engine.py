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

# Add parent directory to path for relative imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import admin_test
from src import db_handler


# check
# Scoring Report creation
def draw_head():
    """
    Creates the header of the scoring report HTML file.
    Initializes the HTML structure and includes title and refresh meta tag.
    Writes the initial content to the score index file.
    """
    file = open(scoreIndex, "w+")
    file.write(
        '<!doctype html><html><head><title>CSEL Score Report</title><meta http-equiv="refresh" content="60"></head><body style="background-color:powderblue;">'
        "\n"
    )
    file.write(
        '<table align="center" cellpadding="10"><tr><td><img src="file:///var/www/CYBERPATRIOT/CCC_logo.png"></td><td><div align="center"><H2>Cyberpatriot Scoring Engine:Linux v1.1</H2></div></td><td><img src="file:///var/www/CYBERPATRIOT/SoCalCCCC.png"></td></tr></table>If you see this wait a few seconds then refresh<br><H2>Your Score: #TotalScore#/'
        + str(menuSettings["Tally Points"])
        + "</H2><H2>Vulnerabilities: #TotalVuln#/"
        + str(menuSettings["Tally Vulnerabilities"])
        + "</H2><hr>"
    )
    file.close()


def record_hit(name, points):
    """
    Records a successful scoring event.
    
    Args:
        name (str): The name of the scoring event.
        points (int): The points awarded for the event.
    """
    global total_points, total_vulnerabilities
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
    write_to_html(
        ('<p style="color:red">' + name + " (" + str(points) + " points)</p>")
    )
    total_points -= int(points)


def display_html_sh(path):  
    """
    Creates a .desktop file for the scoring report on the user's desktop.
    
    Args:
        path (str): The path to the user's desktop directory.
    """
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


def draw_tail():
    """
    Completes the scoring report HTML file by adding the footer content.
    Updates the score and vulnerabilities in the HTML file.
    Sets permissions and ownership for the score index file.
    """
    write_to_html('<hr><div align="center"><b>Coastline College</b>')
    replace_section(scoreIndex, "#TotalScore#", str(total_points))
    replace_section(scoreIndex, "#TotalVuln#", str(total_vulnerabilities))
    replace_section(scoreIndex, "If you see this wait a few seconds then refresh", "")
    os.chmod(scoreIndex, 0o777)
    os.chown(scoreIndex, int(os.environ["SUDO_UID"]), int(os.environ["SUDO_UID"]))
    # shutil.copy('/var/www/CYBERPATRIOT/ScoreReport.html', '/home/'+ os.environ['SUDO_USER'] + '/Desktop/')
    # os.chown ( '/home/'+ os.environ['SUDO_USER'] + '/Desktop/ScoreReport.html', int(os.environ['SUDO_UID']), int(os.environ['SUDO_UID']))
    display_html_sh("/home/" + os.environ["SUDO_USER"] + "/Desktop/")
    os.chown(
        "/home/" + os.environ["SUDO_USER"] + "/Desktop/ScoringReport.desktop",
        int(os.environ["SUDO_UID"]),
        int(os.environ["SUDO_UID"]),
    )
    os.chmod(
        "/home/" + os.environ["SUDO_USER"] + "/Desktop/ScoringReport.desktop", 0o770
    )


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
    
    # Create the HTML file with updated totals
    with open(score_index_path, "w+") as file:
        file.write(
            '<!doctype html><html><head><title>CSEL Score Report</title><meta http-equiv="refresh" content="60"></head><body style="background-color:powderblue;">'
            "\n"
        )
        file.write(
            '<table align="center" cellpadding="10"><tr><td><img src="file:///var/www/CYBERPATRIOT/CCC_logo.png"></td><td><div align="center"><H2>Cyberpatriot Scoring Engine:Linux v1.1</H2></div></td><td><img src="file:///var/www/CYBERPATRIOT/SoCalCCCC.png"></td></tr></table><br><H2>Your Score: 0/'
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
    os.chmod(score_index_path, 0o777)
    os.chown(score_index_path, int(os.environ["SUDO_UID"]), int(os.environ["SUDO_UID"]))
    
    # Ensure desktop icon exists
    display_html_sh("/home/" + os.environ["SUDO_USER"] + "/Desktop/")
    os.chown(
        "/home/" + os.environ["SUDO_USER"] + "/Desktop/ScoringReport.desktop",
        int(os.environ["SUDO_UID"]),
        int(os.environ["SUDO_UID"]),
    )
    os.chmod(
        "/home/" + os.environ["SUDO_USER"] + "/Desktop/ScoringReport.desktop", 0o770
    )


# Extra Functions
def check_runas():
    """
    Checks if the script is running with administrator privileges.
    If not, prompts the user to run as admin and exits.
    """
    if not admin_test.isUserAdmin():
        messagebox.showerror(
            "Administrator Access Needed",
            "Please make sure the scoring engine is running as admin.",
        )
        exit(admin_test.runAsAdmin())


def check_score():
    """
    Checks the current score against the menu settings.
    Sends notifications if points are gained or lost.
    Logs any exceptions that occur during the check.
    """
    global total_points, total_vulnerabilities
    try:
        current_user = os.getlogin()
        getpwnam(current_user).pw_uid
        menuSettings["Current Vulnerabilities"] = total_vulnerabilities
        if total_points > menuSettings["Current Points"]:
            menuSettings["Current Points"] = total_points
            Settings.update_score(menuSettings)
            subprocess.run(
                [
                    "sudo",
                    "-u",
                    os.environ["SUDO_USER"],
                    "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{}/bus".format(
                        getpwnam(current_user).pw_uid
                    ),
                    "notify-send",
                    "-i",
                    "utilities-terminal",
                    "CyberPatriot",
                    "You've gained points!",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
        elif total_points < menuSettings["Current Points"]:
            menuSettings["Current Points"] = total_points
            Settings.update_score(menuSettings)
            subprocess.run(
                [
                    "sudo",
                    "-u",
                    os.environ["SUDO_USER"],
                    "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{}/bus".format(
                        getpwnam(current_user).pw_uid
                    ),
                    "notify-send",
                    "-i",
                    "utilities-terminal",
                    "CyberPatriot",
                    "You've lost points!",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            if (
                total_points == menuSettings["Tally Points"]
                and total_vulnerabilities == menuSettings["Tally Vulnerabilities"]
            ):
                subprocess.run(
                    [
                        "sudo",
                        "-u",
                        os.environ["SUDO_USER"],
                        "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{}/bus".format(
                            getpwnam(current_user).pw_uid
                        ),
                        "notify-send",
                        "-i",
                        "utilities-terminal",
                        "CyberPatriot",
                        "You've completed the image!",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                )
    except:
        f = open("scoring_engine.log", "w")
        e = traceback.format_exc()
        f.write(str(e))
        f.close()
        messagebox.showerror(
            "Crash Report",
            "The scoring engine has stopped working, a log has been saved to "
            + os.path.abspath("scoring_engine.log"),
        )
        sys.exit()


def write_to_html(message):
    """
    Appends a message to the scoring report HTML file.
    
    Args:
        message (str): The message to write to the HTML file.
    """
    file = open(scoreIndex, "a")
    file.write(message)
    file.close()


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
            file = open(vulnerability[vuln]["Location"], "r")
            content = file.read().splitlines()
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
                        record_miss("Forensic Question")


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
    Checks if a UDP port is open on a given host.
    
    Args:
        host (str): The hostname or IP address to check.
        port (int): The UDP port number to check.
    
    Returns:
        bool: True if the port is open, False otherwise.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1)  # Set a timeout for the socket operations
    try:
        sock.sendto(b"", (host, port))
        data, addr = sock.recvfrom(1024)
        sock.close()
        return True
    except socket.timeout:
        sock.close()
        return False


def portVulns(vulnerability):
    """
    Checks for open ports based on the provided vulnerabilities.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    for vuln in vulnerability:
        if vuln != 1:
            if str.upper(vulnerability[vuln]["Protocol"]) == "TCP":
                if (check_tcp(vulnerability[vuln]["IP"]), vulnerability[vuln]["Port"]):
                    record_hit(
                        "Port " + Vulnerabilities[vuln]["Port"] + " is opened.",
                        vulnerability[vuln]["Points"],
                    )
                else:
                    record_miss("Firewall Management")
            else:
                if (check_udp(vulnerability[vuln]["IP"]), vulnerability[vuln]["Port"]):
                    record_hit(
                        "Port " + Vulnerabilities[vuln]["Port"] + " is opened.",
                        vulnerability[vuln]["Points"],
                    )
                else:
                    record_miss("Firewall Management")


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
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
        name (str): The name of the policy being checked.
    """
    # ===== VALIDATION PHASE: Check if PAM configuration files are valid =====
    # If PAM configurations are invalid, no points should be awarded as the system
    # may not be enforcing the configured policies correctly.
    # Checks /var/log/auth.log for actual PAM errors logged by the system.
    
    try:
        # Check /var/log/auth.log for PAM configuration errors
        # These errors indicate that PAM encountered issues with the configuration
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
            with open(auth_log_path, 'r') as log_file:
                # Read the last 1000 lines to check recent PAM errors
                # (auth.log can be very large, so we don't read the entire file)
                lines = log_file.readlines()
                recent_lines = lines[-1000:] if len(lines) > 1000 else lines
                
                for line in recent_lines:
                    line_lower = line.lower()
                    # Check if line contains PAM error indicators
                    for error_indicator in pam_error_indicators:
                        if error_indicator.lower() in line_lower:
                            print(f"WARNING: PAM configuration error detected in {auth_log_path}:")
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
                        print(f"Error parsing unlock_time: {e}")
                        
                if 'deny=' in options:
                    try:
                        deny_match = re.search(r'deny=(\d+)', options)
                        if deny_match:
                            pam_settings_dict['deny'] = deny_match.group(1)
                    except Exception as e:
                        print(f"Error parsing deny: {e}")
    
    # Parse PAM data from common-auth to extract faillock settings
    common_auth_dict = {}
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
                
                # Parse faillock-specific options ADD FUTURE CONFIGURATIONS HERE
                if 'unlock_time=' in options:
                    try:
                        unlock_match = re.search(r'unlock_time=(\d+)', options)
                        if unlock_match:
                            common_auth_dict['unlock_time'] = unlock_match.group(1)
                    except Exception as e:
                        print(f"Error parsing unlock_time from common-auth: {e}")
                        
                if 'fail_interval=' in options:
                    try:
                        fail_interval_match = re.search(r'fail_interval=(\d+)', options)
                        if fail_interval_match:
                            common_auth_dict['fail_interval'] = fail_interval_match.group(1)
                    except Exception as e:
                        print(f"Error parsing fail_interval from common-auth: {e}")
                        
                if 'deny=' in options:
                    try:
                        deny_match = re.search(r'deny=(\d+)', options)
                        if deny_match:
                            common_auth_dict['deny'] = deny_match.group(1)
                    except Exception as e:
                        print(f"Error parsing deny from common-auth: {e}")
    
    # Attempts to match the policy name and check its value, then records hits/misses
    # TODO: Check functionality for all cases
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
                    actual_value = minlen_result.get('actual_value', 0)
                    
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
                    # Use faillock to verify lockout is working (Step 2)
                    faillock_info = get_faillock_info("root")
                    
                    # Check common-auth first (preferred for faillock), then common-password PAM, then LOGIN_RETRIES
                    deny_value = common_auth_dict.get("deny") or pam_settings_dict.get("deny")
                    if deny_value:
                        actual_value = int(deny_value)
                        if actual_value == expected_value:
                            # Verify faillock is available to enforce this
                            if faillock_info is not None:
                                record_hit(
                                    f"Account lockout threshold is set to {actual_value} failed attempts.", 
                                    vulnerability[1]["Points"]
                                )
                            else:
                                # Config is set but faillock not available
                                record_hit(
                                    f"Account lockout threshold is configured to {actual_value} failed attempts.", 
                                    vulnerability[1]["Points"]
                                )
                        else:
                            record_miss("Local Policy")
                    else:
                        # Fallback to LOGIN_RETRIES from login.defs
                        actual_value = int(policy_settings_dict.get("LOGIN_RETRIES", 0))
                        if actual_value == expected_value:
                            record_hit(
                                f"Maximum login tries is set to {actual_value}.", 
                                vulnerability[1]["Points"]
                            )
                        else:
                            record_miss("Local Policy")
                except (ValueError, TypeError, KeyError) as e:
                    print(f"Error checking {name}: {e}")
                    record_miss("Local Policy")
                    
            case "Lockout Duration":
                """
                Checks account lockout duration after failed login attempts.
                
                Linux Account Lockout Duration Configuration Methods (in priority order):

                1. /etc/security/faillock.conf (PRIORITY - Centralized faillock config)
                   Location: /etc/security/faillock.conf
                   Parameter: unlock_time = <seconds>
                   Example: unlock_time = 900
                   Notes: Centralized configuration file for pam_faillock
                          Takes precedence over inline PAM parameters if present
                          Introduced in newer versions of pam_faillock

                2. pam_faillock.so (Modern PAM faillock module)
                   Location: /etc/pam.d/common-auth or /etc/pam.d/system-auth
                   Parameter: unlock_time=<seconds>
                   Example: auth required pam_faillock.so unlock_time=900
                   Notes: Primary mechanism on modern systems (Ubuntu 20.04+, RHEL 8+)
                          unlock_time=0 means permanent lockout (admin must unlock)
                          Works in conjunction with deny= and fail_interval=
                
                Current Implementation Priority:
                - Checks pam_faillock.so unlock_time from /etc/pam.d/common-auth (common_auth_dict)
                - Falls back to configuration in /etc/security/faillock.conf (faillock_settings_content)
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
                    # Priority 0: Check /etc/security/faillock.conf (highest priority - centralized config)
                    # Priority 1: Check pam_faillock.so unlock_time from common-auth
                    unlock_time = (common_auth_dict.get("unlock_time") or 
                                   faillock_settings_content.get("unlock_time"))
                    if unlock_time:
                        actual_value = int(unlock_time)
                        if actual_value == expected_value:
                            record_hit(
                                f"Account lockout duration (unlock_time) is set to {actual_value} seconds.", 
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
                   Example: auth required pam_faillock.so fail_interval=900
                   Notes: Primary mechanism on modern systems (Ubuntu 20.04+, RHEL 8+)
                          Defines the time window for counting failed attempts
                          After this interval, the failure count resets to 0
                          Works with deny= to determine when lockout occurs
                
                2. /etc/security/faillock.conf (HIGH PRIORITY - Centralized faillock config)
                   Location: /etc/security/faillock.conf
                   Parameter: fail_interval = <seconds>
                   Example: fail_interval = 900
                   Notes: Centralized configuration file for pam_faillock
                          Takes precedence over inline PAM parameters if present
                          Introduced in newer versions of pam_faillock
                
                Current Implementation Priority:
                - Checks fail_interval from /etc/pam.d/common-auth (common_auth_dict)
                - Falls back to /etc/security/faillock.conf (faillock_settings_content)
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
                    # Priority 0: Check /etc/security/faillock.conf (highest priority - centralized config)
                    # Priority 1: Check pam_faillock.so fail_interval from common-auth
                    # Priority 2: Check fail_interval from common-password PAM settings
                    # Note: pwquality.conf does not contain fail_interval, so no fallback there
                    fail_interval = (common_auth_dict.get("fail_interval")  or faillock_settings_content.get("fail_interval"))
                    
                    if fail_interval:
                        actual_value = int(fail_interval)
                        if actual_value == expected_value:
                            record_hit(
                                f"Account lockout observation window (fail_interval) is set to {actual_value} seconds.", 
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
                print("TODO: Implement check Kernel")

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


# TODO: Modify after properly implementing 
def user_change_password(vulnerability):
    """
    Checks if a user's password has been changed and meets password policy requirements.
    Uses chage to verify password was recently changed, and test_password_requirements
    to ensure system-wide password policies are enforced.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    for vuln in vulnerability:
        if vuln != 1:
            username = vulnerability[vuln]["User Name"]
            
            # Step 1: Check if password was changed recently using chage
            try:
                # Get password change info for the specific user
                result = subprocess.run(
                    ["chage", "-l", username],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # Parse the "Last password change" line
                for line in result.stdout.splitlines():
                    if "Last password change" in line:
                        # Extract date from line like "Last password change                    : Dec 16, 2025"
                        date_part = line.split(":", 1)[1].strip()
                        
                        # Handle "never" case
                        if date_part.lower() in ("never", "password must be changed"):
                            record_miss("Account Management")
                            continue
                        
                        try:
                            # Parse the date
                            change_date = datetime.datetime.strptime(date_part, "%b %d, %Y")
                            today = datetime.datetime.now()
                            
                            # Check if password was changed today or within last 7 days
                            days_since_change = (today - change_date).days
                            
                            if days_since_change <= 7:  # Changed within last week
                                # Step 2: Verify password requirements are enforced system-wide
                                # Get the minimum requirements that should be met
                                requirements_to_check = {}
                                
                                # Build requirements dict from configured policies
                                # Check if there are any password quality requirements configured
                                if password_settings_content:
                                    if 'minlen' in password_settings_content:
                                        requirements_to_check['minlen'] = int(password_settings_content['minlen'])
                                    if 'dcredit' in password_settings_content:
                                        requirements_to_check['dcredit'] = int(password_settings_content['dcredit'])
                                    if 'ucredit' in password_settings_content:
                                        requirements_to_check['ucredit'] = int(password_settings_content['ucredit'])
                                    if 'lcredit' in password_settings_content:
                                        requirements_to_check['lcredit'] = int(password_settings_content['lcredit'])
                                    if 'ocredit' in password_settings_content:
                                        requirements_to_check['ocredit'] = int(password_settings_content['ocredit'])
                                
                                # If no specific requirements configured, just check if password was changed
                                if not requirements_to_check:
                                    record_hit(
                                        f"{username}'s password was changed recently.",
                                        vulnerability[vuln]["Points"],
                                    )
                                else:
                                    # Test if password requirements are actually enforced
                                    test_results = test_password_requirements(
                                        requirements_to_check,
                                        password_settings_content=password_settings_content,
                                        pamd_policy_settings_content=pamd_policy_settings_content,
                                        login_policy_settings_content=login_policy_settings_content
                                    )
                                    
                                    # Check if all configured requirements are enforced
                                    all_enforced = True
                                    for req_key, req_result in test_results.items():
                                        if not req_result.get('enforced', False):
                                            all_enforced = False
                                            break
                                    
                                    if all_enforced:
                                        record_hit(
                                            f"{username}'s password was changed and meets policy requirements.",
                                            vulnerability[vuln]["Points"],
                                        )
                                    else:
                                        # Password was changed but requirements not enforced
                                        print(f"Warning: {username}'s password was changed but password requirements may not be enforced.")
                                        record_miss("Account Management")
                            else:
                                record_miss("Account Management")
                                
                        except (ValueError, AttributeError) as e:
                            print(f"Warning: Could not parse password change date for {username}: {e}")
                            record_miss("Account Management")
                        break  # Found the line, no need to continue
                        
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
    Checks the update check period setting and records hits/misses.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    for vuln in vulnerability:
        if vuln != 1:
            with open("/etc/apt/apt.conf.d/10periodic", "r") as config_file:
                for line in config_file:
                    # What is the key?
                    if line.strip().startswith(key):
                        _, value = line.strip().split(None, 1)
                        val = value
            if val == '"1";':
                record_hit("Check Period is set to 1", vulnerability[vuln]["Points"])
            else:
                record_miss("Program Management")


# check
def add_text_to_file(vulnerability):
    """
    Checks if specific text has been added to a file and records hits/misses.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    for vuln in vulnerability:
        if vuln != 1:
            file = open(vulnerability[vuln]["File Path"], "r")
            content = file.read()
            file.close()
            if re.search(vulnerability[vuln]["Text to Add"], content):
                record_hit(
                    vulnerability[vuln]["Text to Add"]
                    + " has been added to "
                    + vulnerability[vuln]["File Path"],
                    vulnerability[vuln]["Points"],
                )
            else:
                record_miss("File Management")


# check
def remove_text_from_file(vulnerability):
    """
    Checks if specific text has been removed from a file and records hits/misses.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    for vuln in vulnerability:
        if vuln != 1:
            file = open(vulnerability[vuln]["File Path"], "r")
            content = file.read()
            file.close()
            if not re.search(vulnerability[vuln]["Text to Remove"], content):
                record_hit(
                    vulnerability[vuln]["Text to Remove"]
                    + " has been removed from "
                    + vulnerability[vuln]["File Path"],
                    vulnerability[vuln]["Points"],
                )
            else:
                record_miss("File Management")


def start_up_apps(vulnerability):
    """
    Checks if specific applications are set to run at startup and records hits/misses.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    startup_apps = []
    # List all files in the specified directory
    file_list = os.listdir("/etc/xdg/autostart")
    for filename in file_list:
        if filename.endswith(".desktop"):
            file_path = os.path.join("/etc/xdg/autostart", filename)
            config = configparser.ConfigParser()
            config.read(file_path)

            # Read the application name and command
            app_exec = config.get("Desktop Entry", "Exec")
            startup_apps.append({"command": app_exec})
    for vuln in vulnerability:
        if vuln != 1:
            if vulnerability[vuln] not in start_up_apps:
                record_hit(
                    vulnerability[vuln]["Checks"] + " has been removed from start up",
                    vulnerability[vuln]["Points"],
                )
            else:
                record_miss("File Management")


def check_hosts(vulnerability):
    """
    Checks the /etc/hosts file and records hits/misses based on its content.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    hosts_file_path = "/etc/hosts"
    with open(hosts_file_path, "r") as file:
        hosts_content = file.read().strip()
    for vuln in vulnerability:
        if vuln != 1:
            if not hosts_content:
                record_hit("Hosts file has been cleared", vulnerability[vuln]["Points"])
            else:
                record_miss("File Management")


# fix
def critical_services(vulnerability):
    """
    Checks for critical services and records penalties if their state has changed.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    for vuln in vulnerability:
        if vuln != 1:
            name = vulnerability[vuln]["Service Name"]
            if (
                name in services_content["unit"]
                and vulnerability[vuln]["Service State"] == services_content["active"]
            ):
                record_penalty(name + " was changed.", vulnerability[vuln]["Points"])


# fix
def manage_services(vulnerability):
    """
    Checks the state of services and records hits/misses based on their status.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    for vuln in vulnerability:
        if vuln != 1:
            name = vulnerability[vuln]["Service Name"]
            if name in services_content:
                if (
                    name in services_content["unit"]
                    and vulnerability[vuln]["Service State"]
                    == services_content["active"]
                ):
                    record_hit(
                        name
                        + " has been "
                        + vulnerability[vuln]["Service State"]
                        + " and set to "
                        + vulnerability[vuln]["Service Start Mode"],
                        vulnerability[vuln]["Points"],
                    )
                else:
                    record_miss("Program Management")


def disable_SSH_Root_Login(vulnerability):
    """
    Checks if SSH root login is disabled and records hits/misses.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    try:
        with open("/etc/ssh/sshd_config", "r") as ssh_config_file:
            for line in ssh_config_file:
                if line.strip().startswith("PermitRootLogin"):
                    value = line.strip().split()[1].lower()
                    if value in ("no", "without-password"):
                        record_hit(
                            "SSH_Root_Login Disabled.", vulnerability[1]["Points"]
                        )
                    else:
                        record_miss("Local Policy")

    except FileNotFoundError:
        record_hit("SSH_Root_Login Disabled.", vulnerability[1]["Points"])

    record_miss("Local Policy")


def check_kernel(Vulnerability):
    """
    Checks the kernel version against the expected version and records hits/misses.
    
    Args:
        Vulnerability (str): The expected kernel version.
    """
    kernel_version = platform.uname().release
    print("Kernel Version:", kernel_version)
    if Vulnerability is kernel_version:
        record_hit("Kernel is current version", Vulnerability[1]["Points"])
    else:
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
                    if vulnerability[vuln]["Version"] not in program_versions:
                        record_hit(
                            vulnerability[vuln]["Version"]
                            + " version of "
                            + vulnerability[vuln]["Program Name"],
                            vulnerability[vuln]["Points"],
                        )
                    else:
                        record_miss("Program Management")


def critical_programs(vulnerability):
    """
    Checks for critical programs and records hits/misses based on their installation status.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    for vuln in vulnerability:
        if vuln != 1:
            if vulnerability[vuln]["Program Name"] not in program_content:
                record_hit(
                    vulnerability[vuln]["Program Name"] + " is not installed",
                    vulnerability[vuln]["Points"],
                )
            else:
                record_penalty(
                    vulnerability[vuln]["Program Name"] + " is not installed",
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
    Checks for the existence of specific files and records hits/misses based on their presence.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    for vuln in vulnerability:
        if vuln != 1:
            if not os.path.exists(vulnerability[vuln]["File Path"]):
                record_hit(
                    "The item "
                    + vulnerability[vuln]["File Path"]
                    + " has been removed.",
                    vulnerability[vuln]["Points"],
                )
            else:
                record_miss("File Management")


def permission_checks(vulnerability):
    """
    Checks file permissions against expected values and records hits/misses.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    for vuln in vulnerability:
        if vuln != 1:
            if (
                oct(os.stat(vulnerability[vuln]["File Path"]).st_mode & 0o777)
                is vulnerability[vuln]["Permissions"]
            ):
                record_hit(
                    "The "
                    + vulnerability[vuln]["File Path"]
                    + " permissions have been updated.",
                    vulnerability[vuln]["Points"],
                )
            else:
                record_miss("File Management")


def no_scoring_available(name):
    """
    Displays an error message if no scoring definition is available for a given name.
    
    Args:
        name (str): The name of the item with no scoring definition.
    """
    messagebox.showerror(
        ("No scoring for:", name),
        (
            "There is no scoring definition for",
            name,
            ". Please remove this option if you are the image creator, if you are a competitor ignore this message.",
        ),
    )


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


def get_faillock_info(username="root"):
    """
    Gets account lockout information using faillock command.
    This shows the actual effective lockout settings.
    
    Args:
        username (str): The username to check. Defaults to "root".
    
    Returns:
        dict: Dictionary containing faillock information, or empty dict on error.
    """
    try:
        result = subprocess.run(
            ["faillock", "--user", username],
            capture_output=True,
            text=True,
            check=False  # Don't raise on non-zero exit (user might not exist)
        )
        
        faillock_info = {
            "failed_attempts": 0,
            "locked": False
        }
        
        # Parse the output for failed attempts
        for line in result.stdout.splitlines():
            if "failures:" in line.lower():
                try:
                    # Extract number from line like "When                Type  Source                                           Valid"
                    # or actual failure count
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.isdigit():
                            faillock_info["failed_attempts"] = int(part)
                            break
                except (ValueError, IndexError):
                    pass
                    
        return faillock_info
    except FileNotFoundError:
        print("Warning: faillock command not found. Install libpam-modules for lockout checking.")
        return {}


def test_password_requirements(requirements, password_settings_content=None, pamd_policy_settings_content=None, login_policy_settings_content=None, password_to_test=None):
    """
    Tests password requirements using pwscore/pwmake to verify they're actually enforced.
    Generates test passwords that should pass/fail based on requirements, OR tests a provided password.
    
    Args:
        requirements (dict): Dictionary of password requirements to test.
                           Supported keys: 'minlen', 'dcredit', 'ucredit', 'lcredit', 'ocredit'
        password_settings_content (dict): Password settings from /etc/security/pwquality.conf
        pamd_policy_settings_content (list): PAM password lines from /etc/pam.d/common-password
        login_policy_settings_content (list): Key-value pairs from /etc/login.defs
        password_to_test (str): Optional password to test against requirements. If provided,
                               the function will check this password instead of generating test passwords.
    
    Returns:
        dict: Results dictionary with keys for each requirement tested.
              Format: {
                  'minlen': {'configured': True/False, 'enforced': True/False, 'actual_value': int, 'password_passes': True/False},
                  'dcredit': {...},
                  ...
              }
              If password_to_test is provided, 'password_passes' indicates if the password meets the expected requirement.
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
            # 1. /etc/security/pwquality.conf
            # 2. PAM modules (pam_pwquality, pam_unix)
            # 3. /etc/login.defs
            actual_value = None
            
            # First check pwquality.conf
            if password_settings_content and 'minlen' in password_settings_content:
                try:
                    actual_value = int(password_settings_content['minlen'])
                except (ValueError, TypeError):
                    pass
            
            # If not found, check PAM modules
            if actual_value is None and pamd_policy_settings_content:
                # Parse PAM data to extract module settings
                pam_settings_dict = {}
                for pam_line in pamd_policy_settings_content:
                    normalized_line = pam_line.replace('\\t', '\t')
                    parts = re.split(r'[\t\s]+', normalized_line.strip())
                    parts = [p for p in parts if p]
                    
                    if len(parts) >= 3:
                        module_path = parts[2]
                        
                        # Check if pam_pwquality or pam_unix is enabled
                        if 'pam_pwquality.so' in module_path or 'pam_unix.so' in module_path:
                            # Extract module options
                            if len(parts) > 3:
                                for option in parts[3:]:
                                    if '=' in option:
                                        key, value = option.split('=', 1)
                                        pam_settings_dict[key.strip()] = value.strip()
                
                # Check for minlen in PAM settings
                if 'minlen' in pam_settings_dict:
                    try:
                        actual_value = int(pam_settings_dict['minlen'])
                    except (ValueError, TypeError):
                        pass
            
            # If still not found, check login.defs
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
            
            # If a password was provided, test it against the expected value
            if password_to_test is not None:
                password_length = len(password_to_test)
                password_passes = password_length >= expected_value
                results['minlen']['password_passes'] = password_passes
                # Don't do enforcement testing if a specific password was provided
            # Only test enforcement if configured (actual matches expected) and value > 0 and no password provided
            elif configured and expected_value > 0:
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
    snap_bin_file_names = get_file_names_in_directory("/snap/bin")

    all_file_names = usr_bin_file_names + snap_bin_file_names
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
        vulnerability = Vulnerabilities.get_option_table(vuln.name, False)
        if "Critical" in vuln.name:
            critical_items.append(vuln)
        elif vulnerability[1]["Enabled"]:
            if len(getfullargspec(vulnerability_def[vuln.name]).args) == 1:
                vulnerability_def[vuln.name](
                    vulnerability
                    if "vulnerability"
                    in getfullargspec(vulnerability_def[vuln.name]).args
                    else vuln.name
                )
            else:
                vulnerability_def[vuln.name](vulnerability, vuln.name)


# check1
def local_policies(vulnerabilities):
    """
    Manages local security policies based on the provided vulnerabilities and records hits/misses.
    
    Args:
        vulnerabilities (list): A list of vulnerabilities to check.
    """
    write_to_html("<H3>SECURITY POLICIES</H3>")
    vulnerability_def = {
        "Minimum Password Age": local_group_policy,
        "Maximum Password Age": local_group_policy,
        "Minimum Password Length": local_group_policy,
        "Maximum Login Tries": local_group_policy,
        "Lockout Duration": local_group_policy,
        "Lockout Reset Duration": local_group_policy,
        "Check Kernel": check_kernel,
        "Disable SSH Root Login": local_group_policy,
        "Password History": local_group_policy,
        "Audit": local_group_policy,
    }
    for vuln in vulnerabilities:
        vulnerability = Vulnerabilities.get_option_table(vuln.name, False)
        if vulnerability[1]["Enabled"]:
            if len(getfullargspec(vulnerability_def[vuln.name]).args) == 1:
                vulnerability_def[vuln.name](
                    vulnerability
                    if "vulnerability"
                    in getfullargspec(vulnerability_def[vuln.name]).args
                    else vuln.name
                )
            else:
                vulnerability_def[vuln.name](vulnerability, vuln.name)


# check1
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
    }
    # vulnerability_def = {"Good Program": programs, "Bad Program": programs, "Update Program": no_scoring_available, "Add Feature": no_scoring_available, "Remove Feature": no_scoring_available, "Services": manage_services}
    for vuln in vulnerabilities:
        vulnerability = Vulnerabilities.get_option_table(vuln.name, False)
        if "Critical" in vuln.name:
            critical_items.append(vuln)
        elif vulnerability[1]["Enabled"]:
            if len(getfullargspec(vulnerability_def[vuln.name]).args) == 1:
                vulnerability_def[vuln.name](
                    vulnerability
                    if "vulnerability"
                    in getfullargspec(vulnerability_def[vuln.name]).args
                    else vuln.name
                )
            else:
                vulnerability_def[vuln.name](vulnerability, vuln.name)


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
        "Bad File": bad_file,
        "Add Text to File": add_text_to_file,
        "Remove Text From File": remove_text_from_file,
        "File Permissions": permission_checks,
        "Check Startup": start_up_apps,
    }
    for vuln in vulnerabilities:
        vulnerability = Vulnerabilities.get_option_table(vuln.name, False)
        if vulnerability[1]["Enabled"]:
            if len(getfullargspec(vulnerability_def[vuln.name]).args) == 1:
                vulnerability_def[vuln.name](
                    vulnerability
                    if "vulnerability"
                    in getfullargspec(vulnerability_def[vuln.name]).args
                    else vuln.name
                )
            else:
                vulnerability_def[vuln.name](vulnerability, vuln.name)


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
        vulnerability = Vulnerabilities.get_option_table(vuln.name, False)
        if vulnerability[1]["Enabled"]:
            if len(getfullargspec(vulnerability_def[vuln.name]).args) == 1:
                vulnerability_def[vuln.name](
                    vulnerability
                    if "vulnerability"
                    in getfullargspec(vulnerability_def[vuln.name]).args
                    else vuln.name
                )
            else:
                vulnerability_def[vuln.name](vulnerability, vuln.name)


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
except:
    f = open("scoring_engine.log", "a")
    e = traceback.format_exc()
    f.write(str(e))
    f.close()
    messagebox.showerror(
        "Crash Report",
        "The scoring engine has stopped working, a log has been saved to "
        + os.path.abspath("scoring_engine.log"),
    )
    sys.exit()

total_points = 0
total_vulnerabilities = 0
prePoints = 0
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

# --------- Main Loop ---------#
check_runas()
iterations = 0
while True:
    try:
        # Reload settings from database each iteration to catch configuration updates
        menuSettings = Settings.get_settings(False)
        
        total_points = 0
        total_vulnerabilities = 0
        critical_items = []
        login_policy_settings_content, pamd_policy_settings_content, password_settings_content, common_auth_content, faillock_settings_content = load_policy_settings()
        services_content = load_services()
        program_content = load_programs()
        program_versions = load_versions()
        print("Scoring Engine loop 1st:" + str(iterations))
        time.sleep(15)
        draw_head()
        for category in categories:
            category_def[category.name](
                Vulnerabilities.get_option_template_by_category(category.id)
            )
        critical_functions(critical_items)
        draw_tail()
        check_score()
        print("Scoring Engine loop 2nd:" + str(iterations))
        time.sleep(15)
    except:
        f = open("scoring_engine.log", "w")
        e = traceback.format_exc()
        f.write(str(e))
        f.close()
        messagebox.showerror(
            "Crash Report",
            "The scoring engine has stopped working, a log has been saved to "
            + os.path.abspath("scoring_engine.log"),
        )

# TODO add Functions:
# updateautoinstall    ["Miscellaneous"]["Update Auto Install"]
# taskscheduler        ["Miscellaneous"]["Task Scheduler"]
