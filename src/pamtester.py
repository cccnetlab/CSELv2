"""
This is the PAM tester module for CSEL.
"""

import os
import subprocess
import time
import shutil

# ======================================================================
# PAM Tester Helper Functions
# ======================================================================

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
					parts = line.split()
					for part in parts:
						if part.isdigit():
							faillock_info["failed_attempts"] = int(part)
							break
				except (ValueError, IndexError):
					pass
			line_lower = line.lower()
			if "locked" in line_lower and "not" not in line_lower and "no" not in line_lower:
				faillock_info["locked"] = True

		return faillock_info
	except FileNotFoundError:
		print("Warning: faillock command not found. Install libpam-modules for lockout checking.")
		return {}


def _parse_auth_modules(service):
    """
    Returns a list of PAM auth modules for a service.
    """
    modules = []
    try:
        with open(f"/etc/pam.d/{service}", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 3 and parts[0] == "auth":
                    modules.append(parts[2])
    except FileNotFoundError:
        return []
    return modules


def select_pamtester_service():
    """
    Selects an available PAM service to use with pamtester.
    Prefers services that include pam_faillock in auth stack.
    Returns the service name or None if no suitable service is found.
    """
    candidates = ["login", "su", "sshd", "sudo", "system-auth", "common-auth"]
    best = None
    for service in candidates:
        if not os.path.exists(f"/etc/pam.d/{service}"):
            continue
        auth_modules = _parse_auth_modules(service)
        if any("pam_faillock.so" in m for m in auth_modules):
            return service
        if best is None:
            best = service
    return best


def generate_pamtest_password():
	"""
	Generates a password likely to satisfy common PAM password policies.
	"""
	try:
		pwmake_result = subprocess.run(
			["pwmake", "128"],
			capture_output=True,
			text=True,
			check=True
		)
		password = pwmake_result.stdout.strip()
		if password:
			return password
	except (subprocess.CalledProcessError, FileNotFoundError):
		pass
	# Fallback strong password (length 24+, mixed case, digits, symbols)
	return "TempP@ssw0rd!SecureTest#2026"


def pamtester_authenticate(service, username, password, run_as_user=None):
    """
    Runs pamtester authenticate for a given service/user/password.
    If run_as_user is provided, runs pamtester as that user via su so
    pam_faillock tracks failures against that user's UID without
    retaining root privileges.
    Returns (returncode, stdout, stderr).
    """
    if run_as_user:
        # Use su to fully drop to the target user's UID so pam_faillock
        # records failures correctly. sudo retains root context and bypasses
        # faillock tracking.
        cmd = ["su", "-s", "/bin/bash", "-c",
               f"pamtester {service} {username} authenticate",
               run_as_user]
    else:
        cmd = ["pamtester", service, username, "authenticate"]

    result = subprocess.run(
        cmd,
        input=f"{password}\n",
        capture_output=True,
        text=True,
        check=False
    )
    return result.returncode, result.stdout, result.stderr


def create_temp_user(username, password):
	"""
	Creates a temporary user and sets its password.
	Returns True on success, False otherwise.
	"""
	create_result = subprocess.run(
		["useradd", "-m", "-s", "/bin/bash", username],
		capture_output=True,
		text=True,
		check=False
	)
	if create_result.returncode != 0:
		print(f"Warning: useradd failed for {username}: {create_result.stderr.strip()}")
	passwd_result = subprocess.run(
		["chpasswd"],
		input=f"{username}:{password}",
		capture_output=True,
		text=True,
		check=False
	)
	if passwd_result.returncode != 0:
		print(f"Warning: Could not set password for test user {username}: {passwd_result.stderr.strip()}")
		return False
	return True


def cleanup_temp_user(username):
	"""
	Deletes a temporary user and its home directory.
	"""
	subprocess.run(
		["userdel", "-r", username],
		capture_output=True,
		text=True,
		check=False
	)
	
# ======================================================================
# Main PAM Tester Function
# ======================================================================


def test_max_login_tries_with_pamtester(expected_value):
	"""
	Uses pamtester to attempt failed logins and verify lockout.
	Returns True if lockout occurs at/after expected_value attempts,
	False if it appears not enforced or locks too early,
	None if test cannot be performed.
	"""
	debug_enabled = True
	def debug_log(message):
		if debug_enabled:
			print(f"DEBUG: {message}")

	print(f"Testing PAM max login tries with pamtester (expected lockout at {expected_value} attempts)...")
	if expected_value <= 0:
		debug_log("Expected value <= 0, skipping pamtester check")
		return None

	if not shutil.which("pamtester"):
		print("Warning: pamtester not available. Install pamtester to validate lockout enforcement.")
		debug_log("pamtester binary not found in PATH")
		return None

	service = select_pamtester_service()
	if not service:
		print("Warning: No suitable PAM service found for pamtester.")
		debug_log("No PAM service found in /etc/pam.d")
		return None
	debug_log(f"Selected PAM service: {service}")

	auth_modules = _parse_auth_modules(service)
	if not any("pam_faillock.so" in m for m in auth_modules):
		print(f"Warning: Selected PAM service '{service}' does not include pam_faillock in auth stack; cannot test lockout.")
		debug_log(f"Auth modules for {service}: {auth_modules}")
		return None

	temp_user = f"csel_pamtest_{int(time.time())}"
	test_password = generate_pamtest_password()
	debug_log(f"Temporary user: {temp_user}")

	if not create_temp_user(temp_user, test_password):
		debug_log("Failed to create/set password for temporary user")
		cleanup_temp_user(temp_user)
		return None

	try:
		if shutil.which("faillock"):
			subprocess.run(
				["faillock", "--reset", "--user", temp_user],
				capture_output=True,
				text=True,
				check=False
			)
			debug_log("faillock reset executed")
		else:
			debug_log("faillock binary not found; will rely on pamtester output only")

		wrong_password = "WrongP@ssword!123"

		# Sanity check 1: correct password must succeed before we start
		rc, out, err = pamtester_authenticate(service, temp_user, test_password, run_as_user=temp_user)
		debug_log(f"Sanity check (correct password) rc={rc} out='{out.strip()}' err='{err.strip()}'")
		if rc != 0:
			print(f"Warning: Correct password failed pre-check on service '{service}'; cannot test lockout.")
			return None

		# Reset faillock after the successful sanity check
		if shutil.which("faillock"):
			subprocess.run(
				["faillock", "--reset", "--user", temp_user],
				capture_output=True, text=True, check=False
			)
			debug_log("faillock reset after correct-password sanity check")

		# Sanity check 2: wrong password must fail
		rc, out, err = pamtester_authenticate(service, temp_user, wrong_password, run_as_user=temp_user)
		debug_log(f"Sanity check (wrong password) rc={rc} out='{out.strip()}' err='{err.strip()}'")
		if rc == 0:
			print(f"Warning: PAM service '{service}' authenticates wrong passwords; cannot test lockout.")
			return None

		# Reset again so the sanity-check failure doesn't count toward the threshold
		if shutil.which("faillock"):
			subprocess.run(
				["faillock", "--reset", "--user", temp_user],
				capture_output=True, text=True, check=False
			)
			debug_log("faillock reset after wrong-password sanity check")

		# Accumulate exactly expected_value - 1 failures, verify not locked early
		if expected_value > 1:
			for attempt in range(1, expected_value):
				rc, out, err = pamtester_authenticate(service, temp_user, wrong_password, run_as_user=temp_user)
				debug_log(f"Attempt {attempt}/{expected_value - 1} rc={rc} out='{out.strip()}' err='{err.strip()}'")

			faillock_info = get_faillock_info(temp_user) if shutil.which("faillock") else {}
			debug_log(f"faillock info after {expected_value - 1} failures: {faillock_info}")
			if faillock_info.get("locked"):
				debug_log("Account locked earlier than expected; deny is set too low")
				return False

		# Final failure to reach the lockout threshold
		rc, out, err = pamtester_authenticate(service, temp_user, wrong_password, run_as_user=temp_user)
		debug_log(f"Final failure rc={rc} out='{out.strip()}' err='{err.strip()}'")

		# Correct password should now be rejected if lockout is enforced
		rc, out, err = pamtester_authenticate(service, temp_user, test_password, run_as_user=temp_user)
		debug_log(f"Correct password attempt after threshold rc={rc} out='{out.strip()}' err='{err.strip()}'")
		if rc != 0:
			debug_log("Correct password rejected after threshold; lockout confirmed")
			return True

		# Correct password succeeded — lockout not enforced
		debug_log("Correct password succeeded after threshold; lockout NOT enforced")
		return False
	finally:
		if shutil.which("faillock"):
			subprocess.run(
				["faillock", "--reset", "--user", temp_user],
				capture_output=True,
				text=True,
				check=False
			)
			debug_log("faillock reset executed (cleanup)")
		cleanup_temp_user(temp_user)
		debug_log("Temporary user cleaned up")
