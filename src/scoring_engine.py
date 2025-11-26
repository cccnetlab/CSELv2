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
    if name == "Add User":
        for vuln in vulnerability:
            if vuln != 1:
                if vulnerability[vuln]["User Name"] in user_list:
                    record_hit(
                        vulnerability[vuln]["User Name"] + " has been added.",
                        vulnerability[vuln]["Points"],
                    )
                else:
                    record_miss("Account Management")
    if name == "Remove User":
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
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
        name (str): The name of the policy being checked.
    """
    # Create a dictionary from the list of tuples for easier lookup
    policy_settings_dict = dict(login_policy_settings_content)
    
    # Parse PAM data to extract module settings
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
                            print(f"DEBUG: Found unlock_time setting: {unlock_match.group(1)}")
                    except Exception as e:
                        print(f"DEBUG: Error parsing unlock_time: {e}")
                        
                if 'deny=' in options:
                    try:
                        deny_match = re.search(r'deny=(\d+)', options)
                        if deny_match:
                            pam_settings_dict['deny'] = deny_match.group(1)
                            print(f"DEBUG: Found deny setting: {deny_match.group(1)}")
                    except Exception as e:
                        print(f"DEBUG: Error parsing deny: {e}")
    
    # Attempts to match the policy name and check its, then records hits/misses
    try:
        match name:
            case "Minimum Password Age":
                min_days = int(policy_settings_dict.get("PASS_MIN_DAYS", 0))
                if 30 <= min_days <= 60:
                    record_hit(
                        f"Minimum password age is set to {min_days} days.", vulnerability[1]["Points"]
                    )
                else:
                    record_miss("Local Policy")
                    
            case "Maximum Password Age":
                max_days = int(policy_settings_dict.get("PASS_MAX_DAYS", 0))
                if 60 <= max_days <= 90:
                    record_hit(
                        f"Maximum password age is set to {max_days} days.", vulnerability[1]["Points"]
                    )
                else:
                    record_miss("Local Policy")

            case "Minimum Password Length":
                minlen_value = password_settings_content.get("minlen")
                if minlen_value:
                    try:
                        min_length = int(minlen_value)
                        if min_length >= 10:
                            record_hit(
                                f"Minimum password length is set to {min_length}.",
                                vulnerability[1]["Points"],
                            )
                        else:
                            record_miss("Local Policy")
                    except (ValueError, TypeError):
                        record_miss("Local Policy")
                else:
                    record_miss("Local Policy")

            case "Maximum Login Tries":
                # Check PAM deny setting first, then LOGIN_RETRIES
                pam_deny = pam_settings_dict.get("deny")
                if pam_deny:
                    try:
                        max_attempts = int(pam_deny)
                        if 3 <= max_attempts <= 5:
                            record_hit(
                                f"Account lockout threshold is set to {max_attempts} failed attempts.", vulnerability[1]["Points"]
                            )
                        else:
                            record_miss("Local Policy")
                    except (ValueError, TypeError):
                        record_miss("Local Policy")
                else:
                    # Fallback to LOGIN_RETRIES from login.defs
                    login_retries = int(policy_settings_dict.get("LOGIN_RETRIES", 0))
                    if 3 <= login_retries <= 5:
                        record_hit(
                            f"Maximum login tries is set to {login_retries}.", vulnerability[1]["Points"]
                        )
                    else:
                        record_miss("Local Policy")
                    
            case "Lockout Duration":
                timeout = int(policy_settings_dict.get("LOGIN_TIMEOUT", 0))
                if timeout >= 30:
                    record_hit(f"Lockout duration is set to {timeout} seconds.", vulnerability[1]["Points"])
                else:
                    record_miss("Local Policy")
                    
            case "Lockout Reset Duration":
                # Check both PAM settings and password settings for unlock_time
                unlock_time = pam_settings_dict.get("unlock_time") or password_settings_content.get("unlock_time", "0")
                try:
                    reset_value = int(unlock_time)
                    if reset_value >= 30:
                        record_hit(
                            f"Account lockout reset duration is set to {reset_value} seconds.", vulnerability[1]["Points"]
                        )
                    else:
                        record_miss("Local Policy")
                except (ValueError, TypeError):
                    record_miss("Local Policy")
                    
            case "Password History":
                # Check PAM settings first, then fallback to password settings
                remember_value = pam_settings_dict.get("remember") or password_settings_content.get("remember")
                if remember_value:
                    try:
                        history_size = int(remember_value)
                        if history_size >= 5:
                            record_hit(
                                f"Password history size is set to {history_size}.", vulnerability[1]["Points"]
                            )
                        else:
                            record_miss("Local Policy")
                    except (ValueError, TypeError):
                        record_miss("Local Policy")
                else:
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
        warnings.warn(f"Error processing policy '{name}': {e}")


# test
def group_manipulation(vulnerability, name):
    """
    Checks for group manipulation actions (add/remove) and records hits/misses.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
        name (str): The action being checked (Add Admin, Remove Admin, etc.).
    """
    groups = grp.getgrall()
    if name == "Add Admin":
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
    if name == "Remove Admin":
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
    if name == "Add User to Group":
        for vuln in vulnerability:
            if vuln != 1:
                if (
                    vulnerability[vuln]["User Name"]
                    in grp.getgrnam[vulnerability[vuln]["Group Name"]][3]
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
    if name == "Remove User from Group":
        for vuln in vulnerability:
            if vuln != 1:
                if (
                    vulnerability[vuln]["User Name"]
                    not in grp.getgrnam[vulnerability[vuln]["Group Name"]][3]
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


# check
def user_change_password(vulnerability):
    """
    Checks if a user's password has been changed recently.
    
    Args:
        vulnerability (list): A list of vulnerabilities to check.
    """
    for vuln in vulnerability:
        file = open("user_" + vulnerability[vuln]["User Name"].lower() + ".txt")
        content = file.read()
        file.close()
        last_changed_list = (
            re.search(r"(?<=Password last set\s{12})\S+", content).group(0).split("/")
        )
        last_changed = ""
        for date in last_changed_list:
            if int(date) < 10:
                temp = "0" + date
            else:
                temp = date
            last_changed = last_changed + temp + "/"
        if (
            datetime.datetime.now().strftime("%m/%d/%Y")
            == last_changed.rsplit("/", 1)[0]
        ):
            record_hit(
                vulnerability[vuln]["User Name"] + "'s password was changed.",
                vulnerability[vuln]["Points"],
            )
        else:
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
    if name == "Good Program":
        for vuln in vulnerability:
            if vuln != 1:
                if vulnerability[vuln]["Program Name"] in program_content:
                    record_hit(
                        vulnerability[vuln]["Program Name"] + " is installed",
                        vulnerability[vuln]["Points"],
                    )
                else:
                    record_miss("Program Management")
    if name == "Bad Program":
        for vuln in vulnerability:
            if vuln != 1:
                if vulnerability[vuln]["Program Name"] not in program_content:
                    record_hit(
                        vulnerability[vuln]["Program Name"] + " is not installed",
                        vulnerability[vuln]["Points"],
                    )
                else:
                    record_miss("Program Management")
    if name == "Update Program":
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
    Loads policy settings from the /etc/login.defs file and returns them as a list.
    
    Returns:
        list: A list of tuples containing key-value pairs of policy settings.
    """
    with open("/etc/login.defs", "r") as file:
        lines = file.readlines()
    login_defs_list = []
    pamd_defs_list = []

    # Scans through each line in the file and extracts key-value pairs
    for line in lines:
        line = line.strip()
        if not line.startswith("#") and line: # Ignore comments and empty lines
            key, value = line.split()
            login_defs_list.append((key, value))

    with open("/etc/pam.d/common-password", "r") as common_password_file:
        for line in common_password_file:
            line = line.strip()
            if line.startswith("password"):
                pamd_defs_list.append(line)

    return login_defs_list, pamd_defs_list


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


# fix
def load_password_settings():
    """
    Loads password settings from the /etc/security/pwquality.conf file.
    
    Returns:
        dict: A dictionary of password settings.
    """
    password_settings = {}
    with open("/etc/security/pwquality.conf", "r") as file:
        lines = file.readlines()
    for line in lines:
        line = line.strip()
        if line and "=" in line:
            key, value = line.split("=")
            key = key.strip().lstrip("# ")
            password_settings[key.strip()] = value.strip()
    return password_settings


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
        login_policy_settings_content, pamd_policy_settings_content = load_policy_settings() # Split into login_defs_list and pamd_defs_list to handle different data types
        password_settings_content = load_password_settings()
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
