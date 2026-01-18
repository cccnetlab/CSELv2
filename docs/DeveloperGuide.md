# CSELv2.1 Developer Guide
## Adding Dependencies
In order for **build.py** to recognize new dependencies, make sure the new requirements are installable via pip, and add them to **requirements.txt** using format:
    
    # Name of Dependency
    dependency>=x.x.x

## Updating Distribution Compatibility

For linux distributions:
- Build.py(Need to update *install_tkinter()* for untested distributions)

## Development Tips

- When developing, instead of compiling the files into binaries and services, just run **sudo .venv/bin/python3.12(or latest version) src/configurator.py(or scoring_engine.py)
- Test workflow: Open configurator, add a configuration for the feature you are testing, run or ensure scoring_engine.py is running, test for all edge cases.
- For updating, included useful ***DEVNOTE*** comments.

# Filestructure summary
### /src
Contains all python files essential to scoring engine functionality.

### /useful_scripts
Contains extra scripts you can use to aid development.

### /docs
Contains file documentation, developer guide, setup guides.

# Files

### build.py
Builds the files as binaries.

- Removes previous build artifacts with clean_build().
- Checks for tktinter, lsb-release, and pip and installs them automatically.
- Parses through requirements.txt and uses pip to install dependencies.
- Compiles binaries for configurator.py and scoring_engine.py

*Note: Virtual Environments should be installed for cleaner build and isolation.*

### dep_install.sh
Installs all dependencies using both pip and apt.

- For python packages, add them to `requirements.txt` as needed.
- For other linux packages, add them to the PKGS variable.


### service_setup.py
Sets up scoring_engine binary from dist/ as a service via symlink located in: **/usr/local/bin/scoring_engine_DO_NOT_TOUCH**

- Set the service to run on startup and reload using systemd(systemctl is the cli). Name: **scoring_engine.service**
- Sets up assets in **/etc/CYBERPATRIOT_DO_NOT_REMOVE**
- Optionally runs both binaries.

### configurator.py
Main job is to set and send configurations for the scoring engine to **db_handler** to persist and manage.

- **vulnerability_template** is fed into the db_handler, so any changes require a complete database recreation by deleting the old database located in the **/etc/CYBERPATRIOT/** directory and then running the configurator again.
- Tkinter is the main package that is responsible for creating many of the widgets, buttons, etc in the ui.
- *commit* will restart the scoring engine, comment out the line and stop the service *scoring_engine* for development purposes and re-enable after testing.

### db_handler.py
Maintains persistence for the scoring engine to check configurations from.

### scoring_engine.py
File that constantly checks for configurations specified in **configurator.py**. Updates the score to add or remove points updating scoring report and notifying the user of points gained or lost.

# Vulnerability Implementation
This next section includes details information about how the scoring machine scores each vulnerability.

## **Format:**
**Function:** `func_name(args)`  
**Implementation:** Step by step implementation  
**Scoring Behavior:** What counts as a hit or miss for the vulnerability  
**Tests:** Step by step manual tests to run:  
- [x] Completed test
- [ ] Incomplete test

**Configuration Files Checked:(For Local Policy)** Files checked  
**Note:(optional)** Extra information

# **Account Management**

## Critical Users
**Function:** `critical_users(vulnerability)`

Monitors system for the removal of critical or required user accounts and applies penalties when detected.

**Implementation:**
- Retrieves all system users using `pwd.getpwall()`
- Iterates through configured critical user vulnerabilities
- Checks if each critical user exists in the system user list
- Records penalty if critical user is missing from system

**Scoring Behavior:**
- Penalty applied when critical user is removed
- Points deducted based on configured penalty value

## Add Admin
**Function:** `group_manipulation(vulnerability, "Add Admin")`

Scores competitors for properly elevating standard user accounts to administrator privileges.

**Implementation:**
- Uses `grp.getgrnam("sudo")[3]` to retrieve members of the sudo group
- Iterates through configured admin promotion vulnerabilities
- Checks if specified user is present in sudo group membership
- Records hit when user successfully added to administrator group

**Scoring Behavior:**
- Awards points when specified user is member of sudo group
- Records miss if user not found in sudo group

## Remove Admin
**Function:** `group_manipulation(vulnerability, "Remove Admin")`

Scores competitors for properly demoting unauthorized users from administrator privileges.

**Implementation:**
- Uses `grp.getgrnam("sudo")[3]` to retrieve members of the sudo group
- Iterates through configured admin demotion vulnerabilities
- Checks if specified user is absent from sudo group membership
- Records hit when user successfully removed from administrator group

**Scoring Behavior:**
- Awards points when specified user is not a member of sudo group
- Records miss if user still found in sudo group

## Add User
**Function:** `users_manipulation(vulnerability, "Add User")`

Scores competitors for creating required user accounts on the system.

**Implementation:**
- Retrieves all system groups using `grp.getgrall()`
- Builds list of all existing usernames from group information
- Iterates through configured user addition vulnerabilities
- Checks if specified user exists in the system user list
- Records hit when user account found on system

**Scoring Behavior:**
- Awards points when specified user exists on system
- Records miss if user not found in system

**Note:** Uses group information to enumerate users rather than password database to capture all user types.

## Remove User
**Function:** `users_manipulation(vulnerability, "Remove User")`

Scores competitors for removing unauthorized or unnecessary user accounts from the system.

**Implementation:**
- Retrieves all system groups using `grp.getgrall()`
- Builds list of all existing usernames from group information
- Iterates through configured user removal vulnerabilities
- Checks if specified user is absent from system user list
- Records hit when user account not found on system

**Scoring Behavior:**
- Awards points when specified user does not exist on system
- Records miss if user still found in system

**Note:** Uses group information to enumerate users rather than password database to capture all user types.

## User Change Password
**Function:** `user_change_password(vulnerability)`

Scores competitors for changing a specified user's password to match the password requirements specified in the configurator.

**Implementation:**
- **IMPORTANT**: Modifies `/etc/pam.d/common-password` so that *pwquality.so* has *enforce_for_root* and is at the top to avoid bypassing this check.
- Gathers manually inserted password requirements using `build_password_requirements_cache()` 
- Uses **chage -l username** to extract the value in the *Last password change* line as a fallback.
- Checks if all requirements from `build_password_requirements_cache()` are configured correctly.
- Checks if the time the password hash changes is after the time all configurations are correct.
- Records miss if the password is not changed or is changed before all configurations are correct.
- Records hit if both checks pass.
- Falls back to the **chage -l username** check if something fails.

**Scoring Behavior:**
- Awards points when specified user has changed their password after all configurations were made.
- Records miss if the password was not changed with **chage** after configurations in **requirements**.

**Tests:**
- [x] Create a working configuration, should yield no points
- [x] Try to use passwd to change the password to invalid password, should not be hit
- [x] Use passwd to change the password and record a hit
- [x] Change the password again after another loop, should still be a hit
- [x] Break the configuration, should cause a miss
- [x] Change the password, should still miss
- [x] Fix configuration, should still miss
- [x] Change password, should record a hit


## Add User to Group
**Function:** `group_manipulation(vulnerability, "Add User to Group")`

Scores competitors for properly adding users to required security or functional groups (excluding admin/sudo group).

**Implementation:**
- Retrieves all system groups using `grp.getgrall()`
- Iterates through configured group membership vulnerabilities
- Uses `grp.getgrnam(group_name)[3]` to get members of specified group
- Checks if specified user is present in the group's member list
- Records hit when user successfully added to target group
- Handles `KeyError` if group doesn't exist (records miss if group missing)

**Scoring Behavior:**
- Awards points when specified user is a member of specified group
- Records miss if user not found in group membership
- Records miss if target group does not exist

**Note:** This is distinct from Add Admin - used for non-administrative groups like "audio", "video", "www-data", etc.

## Remove User from Group
**Function:** `group_manipulation(vulnerability, "Remove User from Group")`

Scores competitors for properly removing users from unauthorized or unnecessary groups (excluding admin/sudo group).

**Implementation:**
- Retrieves all system groups using `grp.getgrall()`
- Iterates through configured group removal vulnerabilities
- Uses `grp.getgrnam(group_name)[3]` to get members of specified group
- Checks if specified user is absent from the group's member list
- Records hit when user successfully removed from target group
- Handles `KeyError` if group doesn't exist (records hit if group missing, as user cannot be in non-existent group)

**Scoring Behavior:**
- Awards points when specified user is not a member of specified group
- Awards points if target group does not exist (user cannot be in non-existent group)
- Records miss if user still found in group membership

**Note:** This is distinct from Remove Admin - used for non-administrative groups. Useful for removing users from privileged groups like "sudo", "shadow", or functional groups they shouldn't access.


# **Local Group Policy**

## Minimum Password Age
**Function:** `local_group_policy(vulnerability, "Minimum Password Age")`

Scores competitors for configuring the minimum number of days before a password can be changed after being set.

**Implementation:**
- Retrieves expected value from vulnerability configuration using `vulnerability[1].get("Value", 0)`
- Uses `get_chage_info()` to get actual effective password aging settings from system
  - Creates temporary test user to verify system defaults
  - Parses `chage -l` output for "Minimum number of days between password change" field
  - Cleans up test user after extraction
- Falls back to `/etc/login.defs` PASS_MIN_DAYS parameter if chage fails
- Compares actual value with expected value from configurator
- Records hit if values match exactly

**Scoring Behavior:**
- Awards points when minimum password age matches configured value
- Records miss if expected value is 0 (not configured)
- Records miss if actual value does not match expected value

**Configuration Files Checked:**
1. System defaults via `chage -l` on temporary user (primary)
2. `/etc/login.defs` - PASS_MIN_DAYS parameter (fallback)

## Maximum Password Age
**Function:** `local_group_policy(vulnerability, "Maximum Password Age")`

Scores competitors for configuring the maximum number of days a password can be used before requiring a change.

**Implementation:**
- Retrieves expected value from vulnerability configuration using `vulnerability[1].get("Value", 0)`
- Uses `get_chage_info()` to get actual effective password aging settings from system
  - Creates temporary test user to verify system defaults
  - Parses `chage -l` output for "Maximum number of days between password change" field
  - Cleans up test user after extraction
- Falls back to `/etc/login.defs` PASS_MAX_DAYS parameter if chage fails (default 99999)
- Compares actual value with expected value from configurator
- Records hit if values match exactly

**Scoring Behavior:**
- Awards points when maximum password age matches configured value
- Records miss if expected value is 0 (not configured)
- Records miss if actual value does not match expected value

**Configuration Files Checked:**
1. System defaults via `chage -l` on temporary user (primary)
2. `/etc/login.defs` - PASS_MAX_DAYS parameter (fallback)

## Minimum Password Length
**Function:** `local_group_policy(vulnerability, "Minimum Password Length")`

Scores competitors for configuring and enforcing minimum password length requirements.

**Implementation:**
- Retrieves expected value from vulnerability configuration using `vulnerability[1].get("Value", 0)`
- Uses `test_password_requirements()` with `{'minlen': expected_value}` to verify enforcement
  - Checks `/etc/security/pwquality.conf` for minlen parameter
  - Checks `/etc/pam.d/common-password` for pam_pwquality.so minlen option
  - Checks `/etc/pam.d/common-password` for pam_unix.so minlen option
  - Tests actual enforcement using `pwscore` to validate system rejects short passwords
- Prioritizes pwquality.conf over PAM inline parameters
- Verifies configuration is both set correctly and enforced by system
- Awards points even if enforcement test fails (missing pwscore) as long as configuration matches

**Scoring Behavior:**
- Awards points when minimum length is configured to expected value and enforced
- Awards points when minimum length is configured correctly (even if enforcement test unavailable)
- Records miss if expected value is 0 (not configured)
- Records miss if actual value does not match expected value

**Configuration Files Checked:**
1. `/etc/security/pwquality.conf` - minlen parameter (priority)
2. `/etc/pam.d/common-password` - pam_pwquality.so minlen option
3. `/etc/pam.d/common-password` - pam_unix.so minlen option (fallback)

**Note:** Uses pwscore/pwmake to verify actual enforcement beyond just configuration presence.

## Maximum Login Tries
**Function:** `local_group_policy(vulnerability, "Maximum Login Tries")`

Scores competitors for configuring account lockout threshold after consecutive failed login attempts.

**Implementation:**
- Retrieves expected value from vulnerability configuration using `vulnerability[1].get("Value", 0)`
- Uses `get_faillock_info("root")` to verify faillock functionality
- Checks `/etc/pam.d/common-auth` for pam_faillock.so deny parameter (priority)
- Falls back to `/etc/pam.d/common-password` pam_faillock.so deny parameter
- Falls back to `/etc/login.defs` LOGIN_RETRIES parameter if PAM not configured
- Compares actual value with expected value from configurator
- Verifies faillock command is available to enforce lockout

**Scoring Behavior:**
- Awards points when deny/LOGIN_RETRIES matches expected value and faillock available
- Awards points when deny/LOGIN_RETRIES configured correctly even if faillock unavailable
- Records miss if expected value is 0 (not configured)
- Records miss if actual value does not match expected value

**Configuration Files Checked:**
1. `/etc/pam.d/common-auth` - pam_faillock.so deny parameter (priority)
2. `/etc/pam.d/common-password` - pam_faillock.so deny parameter
3. `/etc/login.defs` - LOGIN_RETRIES parameter (fallback)

**Note:** Modern systems use pam_faillock module; older systems may use LOGIN_RETRIES.

## Lockout Duration
**Function:** `local_group_policy(vulnerability, "Lockout Duration")`

Scores competitors for configuring how long accounts remain locked after exceeding failed login attempts.

**Implementation:**
- Retrieves expected value from vulnerability configuration in seconds using `vulnerability[1].get("Value", 0)`
- Checks `/etc/security/faillock.conf` for unlock_time parameter (priority - centralized config)
- Checks `/etc/pam.d/common-auth` for pam_faillock.so unlock_time parameter (fallback)
- Compares actual value with expected value from configurator
- unlock_time=0 indicates permanent lockout requiring admin intervention

**Scoring Behavior:**
- Awards points when unlock_time matches expected value in seconds
- Records miss if expected value is 0 (not configured)
- Records miss if unlock_time not found in any configuration file
- Records miss if actual value does not match expected value

**Configuration Files Checked:**
1. `/etc/security/faillock.conf` - unlock_time parameter (priority - Ubuntu 20.04+, RHEL 8+)
2. `/etc/pam.d/common-auth` - pam_faillock.so unlock_time parameter (fallback)

**Note:** Works with pam_faillock module. unlock_time value is in seconds (e.g., 900 = 15 minutes).

## Lockout Reset Duration
**Function:** `local_group_policy(vulnerability, "Lockout Reset Duration")`

Scores competitors for configuring the observation window in which failed login attempts are counted before resetting.

**Implementation:**
- Retrieves expected value from vulnerability configuration in seconds using `vulnerability[1].get("Value", 0)`
- Checks `/etc/pam.d/common-auth` for pam_faillock.so fail_interval parameter (priority)
- Falls back to `/etc/security/faillock.conf` fail_interval parameter
- Compares actual value with expected value from configurator
- After fail_interval seconds, the failed attempt counter resets to 0

**Scoring Behavior:**
- Awards points when fail_interval matches expected value in seconds
- Records miss if expected value is 0 (not configured)
- Records miss if fail_interval not found in any configuration file
- Records miss if actual value does not match expected value

**Configuration Files Checked:**
1. `/etc/pam.d/common-auth` - pam_faillock.so fail_interval parameter (priority)
2. `/etc/security/faillock.conf` - fail_interval parameter (fallback)

**Note:** Defines time window for counting failed attempts. Works with deny= parameter to determine lockout trigger.

## Password History
**Function:** `local_group_policy(vulnerability, "Password History")`

Scores competitors for configuring password history to prevent reuse of recent passwords.

**Implementation:**
- Retrieves expected value from vulnerability configuration using `vulnerability[1].get("Value", 0)`
- Checks `/etc/pam.d/common-password` for pam_unix.so remember parameter (priority)
- Falls back to `/etc/security/pwquality.conf` remember parameter
- Compares actual value with expected value from configurator
- System stores hashed passwords in `/etc/security/opasswd` to enforce history

**Scoring Behavior:**
- Awards points when remember parameter matches expected value
- Records miss if expected value is 0 (not configured)
- Records miss if remember not found in any configuration file
- Records miss if actual value does not match expected value

**Configuration Files Checked:**
1. `/etc/pam.d/common-password` - pam_unix.so remember parameter (priority)
2. `/etc/security/pwquality.conf` - remember parameter (fallback)

**Note:** Prevents password reuse by storing history of previous password hashes. Value indicates number of previous passwords remembered.

## Audit
**Function:** `local_group_policy(vulnerability, "Audit")` calls `audit_check()`

Scores competitors for enabling the audit daemon (auditd) for system security auditing.

**Implementation:**
- Uses `systemctl is-active auditd` to check service status
- Captures stdout and checks if "inactive" is present in output
- Returns True if auditd is active, False otherwise
- Records hit if audit daemon is running

**Scoring Behavior:**
- Awards points when auditd service is active
- Records miss if auditd service is inactive or not installed

## Disable SSH Root Login
**Function:** `local_group_policy(vulnerability, "Disable SSH Root Login")` calls `disable_SSH_Root_Login(vulnerability)`

Scores competitors for disabling direct root login via SSH to improve security.

**Implementation:**
- Opens `/etc/ssh/sshd_config` and searches for "PermitRootLogin" directive
- Parses the value after PermitRootLogin (space-delimited)
- Checks if value is "no" or "without-password" (case-insensitive)
- Records hit if root login is properly disabled
- If sshd_config file doesn't exist, awards points (SSH not installed)

**Scoring Behavior:**
- Awards points when PermitRootLogin is set to "no" or "without-password"
- Awards points if `/etc/ssh/sshd_config` not found (SSH not installed = root can't login)
- Records miss if PermitRootLogin is set to "yes" or "prohibit-password" with keys allowed
- Records miss if PermitRootLogin directive not found in config

**Configuration Files Checked:**
1. `/etc/ssh/sshd_config` - PermitRootLogin directive

**Note:** Best practice is "no" for maximum security. "without-password" allows key-based auth but blocks password auth for root.

## Check Kernel
**Function:** `local_group_policy(vulnerability, "Check Kernel")` calls `check_kernel(vulnerability)`

Scores competitors for updating kernel to latest available version and rebooting to load it.

**Implementation:**
- Uses `platform.uname().release` to get currently running kernel version
- Detects Ubuntu base version for proper HWE kernel detection:
  - Reads `/etc/os-release` for `UBUNTU_CODENAME` (priority - for Ubuntu derivatives like Linux Mint)
  - Falls back to `VERSION_ID` if `UBUNTU_CODENAME` not present
  - Maps codename to version using lookup table (e.g., noble → 24.04, jammy → 22.04)
  - Important for Ubuntu derivatives (Linux Mint, Pop!_OS) that use different versioning
- Detects HWE (Hardware Enablement) kernel track:
  - First tries version-specific package: `linux-image-generic-hwe-{ubuntu_version}` (e.g., linux-image-generic-hwe-24.04)
  - Falls back to generic package: `linux-image-generic-hwe`
  - Uses standard package `linux-image-generic` if no HWE kernel found
- Queries `apt-cache policy` for the detected meta-package to find latest available kernel
- Parses "Candidate:" line to extract latest version
- Uses `apt-cache depends` on meta-package to determine specific kernel image package name
- Extracts package name matching pattern `linux-image-[\d\.]+-\d+-\w+` (e.g., linux-image-5.15.0-92-generic)
- Uses `dpkg -l <package>` to verify kernel package is installed (status "ii")
- Calls `is_kernel_running(expected_version, running_kernel)` helper to verify system is running the installed kernel
  - Extracts version numbers using regex `\d+` from both version strings
  - Compares first 4 version numbers (major.minor.patch-build)
  - Returns True if versions match
- Awards points only if kernel is both installed AND running (requires reboot)

**Scoring Behavior:**
- Awards points when latest kernel package is installed AND system is running that kernel
- Records miss if cannot detect Ubuntu version (unable to detect HWE package name)
- Records miss if cannot determine latest kernel (no internet or apt cache not updated)
- Records miss if latest kernel package is not installed (need `apt upgrade`)
- Records miss if latest kernel is installed but not running (need reboot)

**Note:** Requires internet access to query repositories. Most likely not being used.

**Tests:**
- [x] Update, install, and reboot, should record a hit.
- [x] Boot older version, should record a miss.
- [ ] Remove newest version installed so that booted version is newest installed, record miss.
- [ ] Reinstall, miss still.
- [ ] Reactivate and reboot, record hit.


# **Program Management**

## Good Program
**Function:** `programs(vulnerability, "Good Program")` called by `program_management(vulnerabilities)`

Scores competitors for installing required or beneficial programs on the system.

**Implementation:**
- Uses `load_programs()` to collect all executable file names from system directories
- Iterates through configured "Good Program" vulnerabilities
- Performs set membership test to check if specified program name exists in `program_content`
- Records hit if program found in the pre-loaded set
- Records miss if program not found in system directories

**Scoring Behavior:**
- Awards points when specified program is installed (exists in `/usr/bin`, `/usr/sbin`, `/snap/bin`, or `/usr/games`)
- Records miss if program is not found in any checked directory
- Program name must exactly match the executable filename

**Tests:**
- [x] Configure a good program that is already installed (e.g., "sl"), should record a hit
- [x] Configure a good program that is not installed (e.g., "nonexistent-app"), should record a miss
- [x] Install the missing program using `apt install`, wait for next scoring cycle, should record a hit
- [x] Uninstall the program using `apt remove`, wait for next scoring cycle, should record a miss
- [x] Install program via snap (e.g., "hello-world"), ensure it appears in `/snap/bin`, should record a hit
- [x] Repeat process for snap program.

**Note:** Requires installing packages using `apt install -d <pkg>` ahead of time due to netlabs internet restriction.

## Bad Program
**Function:** `programs(vulnerability, "Bad Program")` called by `program_management(vulnerabilities)`

Scores competitors for removing unauthorized, malicious, or policy-violating programs from the system.

**Implementation:**
- Uses `load_programs()` to collect all executable file names from system directories
- Iterates through configured "Bad Program" vulnerabilities
- Performs set membership test to check if specified program name is absent from `program_content`
- Records hit if program NOT found in the pre-loaded set (successfully removed)
- Records miss if program still found in system directories

**Scoring Behavior:**
- Awards points when specified program is NOT installed (does not exist in `/usr/bin`, `/usr/sbin`, `/snap/bin`, or `/usr/games`)
- Records miss if program is still found in any checked directory
- Program name must exactly match the executable filename

**Tests:**
- [x] Configure a bad program that is already installed (e.g., "hello"), should record a miss
- [x] Remove the bad program using `apt remove hello` or `apt purge hello`, wait for next scoring cycle, should record a hit
- [x] Reinstall the program using `apt install`, wait for next scoring cycle, should record a miss
- [x] Configure a bad program that is not installed (e.g., "john"), should record a hit immediately
- [x] Install the bad program, wait for next scoring cycle, should record a miss

## Update Program
**Function:** `programs(vulnerability, "Update Program")` called by `program_management(vulnerabilities)`

Scores competitors for updating packages to a specified version or newer.

**Implementation:**
- Uses `load_versions()` to query dpkg for installed package versions
- Iterates through configured "Update Program" vulnerabilities
- Searches `program_versions` list for matching package by name and compares installed version with expected version
- Records hit if package found and version matches expected
- Records miss if package not found or version doesn't match

**Scoring Behavior:**
- Awards points when specified package is installed AND version exactly matches configured value
- Records miss if package is not installed
- Records miss if package is installed but version doesn't match
- Records miss if "Program Name" or "Version" fields are missing or empty in configuration
- Package name must match dpkg package name (not executable name)

**Tests:**
- [x] Install package and configure with correct version, record hit
- [x] Reconfigure package to different version in configurator, record miss
- [x] Add invalid package name, record miss
- [x] Add empty values, record miss

**Note:** Package names in dpkg may differ from executable names. For example, `openssh-server` package provides `sshd` executable. Use `dpkg -l | grep <name>` to find correct package names. Consider using `dpkg --compare-versions` for more flexible version checking (>=) instead of exact match.

## Critical Programs
**Function:** `critical_programs(vulnerability)` called by `critical_functions(vulnerabilities)`

Penalizes competitors for removing or uninstalling critical programs that must remain on the system.

**Implementation:**
- Iterates through configured critical program vulnerabilities
- Uses `load_programs()` to check all executable file names from system directories
- Checks if specified critical program name exists in `program_content` (pre-loaded set of installed programs)
- If program is NOT found in system directories, records a penalty (deducts points)
- If program is still installed, no penalty is applied

**Scoring Behavior:**
- Deducts points (penalty) when critical program has been removed from the system
- No penalty if critical program remains installed

**Tests:**
- [x] Configure critical program that is not currently installed, should immediately show penalty
- [x] Install that program, wait for next cycle, penalty should be removed
- [x] Remove the critical program using `apt remove vim`, wait for next cycle, should record a penalty
- [x] Reinstall the program using `apt install vim`, wait for next cycle, should remove penalty


## Services
**Function:** `manage_services(vulnerability)` called by `program_management(vulnerabilities)`

Scores competitors for properly configuring system services to specified states and start modes. Checks both runtime state (active/inactive) and boot configuration (enabled/disabled/masked).

**Implementation:**
- Iterates through configured service vulnerabilities
- Ensures service name has `.service` extension for systemctl compatibility
- Uses `systemctl status <service>` to verify service exists and determine actual runtime state
  - Parses output for "active (running)", "active (exited)", "inactive (dead)", or "failed"
  - Records miss if service "could not be found" or "not loaded"
- Uses `systemctl is-enabled <service>` to determine actual start mode
  - Returns "enabled", "disabled", "masked", "static", etc.
- Compares both actual state and start mode against configured expected values
- Records hit only when both state AND start mode match expectations
- Records miss if either state or start mode doesn't match, or if service check fails

**Scoring Behavior:**
- Awards points when specified service has BOTH:
  - Correct runtime state (active/inactive)
  - Correct start mode (enabled/disabled/masked)
- Records miss if service does not exist on the system
- Records miss if service state doesn't match expected value
- Records miss if service start mode doesn't match expected value
- Records miss if service check encounters an error

**Tests:**
- [x] Configure service with state="active" and start_mode="enabled" for a running enabled service, should record a hit
- [x] Stop the service using `systemctl stop <service>`, wait for next cycle, should record a miss
- [x] Start the service again using `systemctl start <service>`, wait for next cycle, should record a hit
- [x] Disable the service using `systemctl disable <service>` while keeping it running, wait for next cycle, should record a miss
- [x] Enable again using `systemctl enable <service>`, wait for next cycle, should record a hit
- [x] Configure service with state="inactive" and start_mode="disabled" for a stopped disabled service
- [x] Ensure service is stopped and disabled, should record a hit
- [x] Start the service, should record a miss
- [x] Stop and disable again, should record a hit
- [x] Enable the service using `systemctl enable <service>`, should record a miss 
- [x] Disable again using `systemctl disable <service>`, wait for next cycle, should record a hit
- [x] Configure service with state="inactive" and start_mode="masked" for a masked service
- [x] Configure a non-existent service name, should record a miss
- [x] Test with service name without .service extension, should still work correctly

## Critical Services
**Function:** `critical_services(vulnerability)` called by `critical_functions(vulnerabilities)`

Penalizes competitors for modifying the state or start mode of critical services that must remain in their configured state.

**Implementation:**
- Iterates through configured critical service vulnerabilities
- Ensures service name has `.service` extension for systemctl compatibility
- Searches `services_content` (pre-loaded system service list) for matching service by unit name
- Extracts actual runtime state from service data structure
- Uses `systemctl is-enabled <service>` to determine actual start mode
- Compares both actual state and start mode against configured expected values
- Records penalty if EITHER state OR start mode differs from expected configuration

**Scoring Behavior:**
- Deducts points (penalty) when critical service has been changed from its expected configuration:
  - If runtime state changed from expected value (e.g., active → inactive)
  - If start mode changed from expected value (e.g., enabled → disabled)
- Penalty applied if either condition is violated (not both required)
- Shows detailed penalty message indicating what was changed from original configuration

**Tests:**
- [x] Configure critical service with state="active" and start_mode="enabled" for essential service (e.g., "networking.service"), should show no penalty initially
- [x] Stop the service using `systemctl stop <service>`, wait for next cycle, should record a penalty
- [x] Start the service again, should remove penalty
- [x] Disable the service using `systemctl disable <service>` while keeping it running, should record a penalty
- [x] Enable the service again, should remove penalty
- [x] Configure critical service with state="inactive" and start_mode="disabled"
- [x] Start the service, should record a penalty
- [x] Stop the service, should remove penalty
- [x] Enable the service while keeping it stopped, should record a penalty
- [x] Disable the service again, should remove penalty
- [x] Modify both state and start mode simultaneously, should record a penalty

**Note:** Unlike regular Services which require both conditions to match for points, Critical Services apply penalties if EITHER condition is violated. This is intentional to protect critical system services from any unauthorized changes.

# **File Management**

## Forensic
**Function:** `forensic_question(vulnerability)`

Scores competitors for correctly answering forensic questions placed on their desktop.

**Implementation:**
- Iterates through configured forensic question vulnerabilities
- Opens the forensic question file at the specified location
- Reads the file content line by line
- Searches for lines containing "ANSWER:"
- Compares the text after "ANSWER:" with the configured correct answer
- Records hit if the answer matches the configured answer string
- Records miss if the answer is incorrect, missing, or file cannot be read

**Scoring Behavior:**
- Awards points when the answer in the file matches the configured correct answer
- Records miss if the file does not exist or cannot be read
- Records miss if no "ANSWER:" line is found in the file
- Records miss if the answer provided does not match the configured answer
- Answer comparison is case-sensitive and must match exactly

**Tests:**
- [x] Leave location blank and wait for engine to loop, should not cause scoring engine to error
- [x] Configure a forensic question with correct answer, file should be created on desktop
- [x] Verify file has write permissions for basic users (0o666)
- [x] Type the correct answer after "ANSWER:", should record a hit
- [x] Type an incorrect answer after "ANSWER:", should record a miss
- [x] Type the correct answer with different capitalization, should record a miss (case-sensitive)
- [x] Delete the forensic question file, should record a miss (file not found)
- [x] Recreate file by saving/committing configuration, file should be recreated
- [x] Delete a forensic question file and add a new forensic question, should not be set to the same location as the deleted file ending up with duplicate locations.
- [x] Create 3 questions and save, then delete question 2 and its file and save, finally create a new question which should then be the new question 2.
- [x] Modify the question text in configurator, file should be reset on next save/commit

### **File Creation:**
- Forensic question files are created by `create_forensic()` in configurator.py
- Files are created with permissions 0o666 (rw-rw-rw-) to allow basic users to write answers
- Default location is the user's desktop as specified in configurator settings
- Files are automatically created/updated when configuration is saved or committed
- File naming scheme: `/home/<user>/Desktop/Forensic Question <number>.txt`

**Note:** The forensic question file format is:
```
This is a forensics question. Answer it below
------------------------
<Question text from configuration>

ANSWER: <TypeAnswerHere>
```
Users must replace `<TypeAnswerHere>` with their answer. The answer check is performed by string matching on the text after "ANSWER:" in the file.

## Bad File
**Function:** `file_manipulation(vulnerability, "Bad File")`

Scores competitors for removing unauthorized or malicious files from the system.

**Implementation:**
- Uses `os.path.isfile()` to check if each specified bad file exists
- Records hit if file is not found (successfully removed)
- Records miss if file still exists

**Scoring Behavior:**
- Awards points when specified file is NOT present on the system
- Records miss if file is still found

**Tests:**
- [x] Configure a bad file that doesn't exit, should record a hit
- [x] Create the bad file, should record a miss
- [x] Remove the bad file using `rm`, should record a hit
- [x] Configure a bad directory that doesn't exit, should record a hit
- [x] Create the bad directory, should record a miss
- [x] Remove the bad directory using `rm -rf`, should record a hit

## Add Text to File
**Function:** `add_text_to_file(vulnerability)`

Scores competitors for adding specific text content to a designated file.

**Implementation:**
- Iterates through configured "Add Text to File" vulnerabilities
- Validates file path is not empty or whitespace-only
  - Skips vulnerability if file path is empty or invalid
- Opens specified file at configured file path in read mode
- Reads entire file content into memory
- Uses `re.search()` with configured text pattern to check if text exists in file
- Records hit if text pattern is found in file content
- Records miss if text is not found in the file
- Silently skips if file doesn't exist, can't be read, or encounters an error

**Scoring Behavior:**
- Awards points when specified text is present in the target file
- Records miss if text is not found in file
- Supports regex patterns for flexible text matching
- File must be readable by scoring engine

**Tests:**
- [x] Configure "Add Text to File" with file path and text pattern, should record a miss
- [x] Add the exact text to the file, should record a hit
- [x] Add extra text, shouldn't change the result.
- [x] Remove the text from file, should record a miss
- [x] Test with regex pattern (e.g., "^admin.*user$"), verify regex matching works
- [x] Remove the file, should record a miss

## Remove Text From File
**Function:** `remove_text_from_file(vulnerability)`

Scores competitors for removing specific text content from a designated file.

**Implementation:**
- Iterates through configured "Remove Text From File" vulnerabilities
- Validates file path is not empty or whitespace-only
  - Skips vulnerability if file path is empty or invalid
- Opens specified file at configured file path in read mode
- Reads entire file content into memory
- Uses `re.search()` with configured text pattern to check if text is absent from file
- Records hit if text pattern is NOT found in file content (successfully removed)
- Records miss if text is still present in the file
- Silently skips if file doesn't exist, can't be read, or encounters an error

**Scoring Behavior:**
- Awards points when specified text is NOT present in the target file
- Records miss if text is still found in file
- Supports regex patterns for flexible text matching
- File must be readable by scoring engine

**Tests:**
- [x] Configure "Remove Text From File" with file path and text pattern that exists in file, should record a miss
- [x] Modify the text from the file, should record a hit
- [x] Completely empty the file, should record a hit
- [x] Add the text back to file, should record a miss
- [x] Test with regex pattern, verify pattern no longer matches after removal
- [x] Remove the file, should record a miss

## File Permissions
**Function:** `permission_checks(vulnerability)`

Scores competitors for properly configuring file or directory permissions for specific users to restrict or grant read, write, and execute access.

**Implementation:**
- Retrieves file path from `vulnerability[vuln].get("Object Path")`
- Gets target username from `vulnerability[vuln].get("Users to Modify")`
- Gets expected permission digit (0-7) from `vulnerability[vuln].get("Permissions(R/W/X)", "")`
- Treats empty permission string as 0 (no permissions)
- Calls `get_user_permission_on_file(username, file_path)` to determine user's actual permissions:
  - If user is the file owner → returns owner permission bits (first octal digit)
  - Else if user is in file's group → returns group permission bits (second octal digit)
  - Else → returns other permission bits (third octal digit)
- Compares actual permission digit (0-7) with expected permission digit
- Records hit if permissions match exactly

**Scoring Behavior:**
- Awards points when specified user has exactly the configured permission level on the file/directory
- Records miss if username is missing from configuration
- Records miss if file/directory doesn't exist or permissions cannot be checked
- Records miss if user's actual permission differs from expected permission

**Tests:**
- [x] Create test file (`testfile.txt`) and test user (`testuser`), make testuser owner of file
- [x] Set file to 600 (rw- for owner), configure for testuser with permission 6, should record a hit
- [x] Change to 700, configure for testuser with permission 6, should record a miss (expects rw-, has rwx)
- [x] Create test group (`testgroup`), add testuser to testgroup, change file owner to root, set file group to testgroup
- [x] Set file to 060 (rw- for group), configure for testuser with permission 6, should record a hit
- [x] Change to 070, configure for testuser with permission 6, should record a miss (expects rw-, has rwx)
- [x] Remove testuser from testgroup, ensure testuser is NOT file owner and NOT in file group
- [x] Set file to 006 (rw- for other), configure for testuser with permission 6, should record a hit
- [x] Change to 007, configure for testuser with permission 6, should record a miss (expects rw-, has rwx)
- [x] Test with permission field left empty (defaults to 0), create file should record miss
- [x] Set file permissions to 0 for user, group, or other, whichever group your test user falls into.
- [x] Test with non-existent file path, should record a miss and log error
- [x] Test with non-existent username, should record a miss and log error
- [x] Test with directory instead of file, should work identically