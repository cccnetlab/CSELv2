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
		}

		# Parse the output for failed attempts.
		# faillock outputs one row per failure entry; each row ends with
		# "V" (valid/counted) or "I" (invalid/not counted). Count the "V" lines.
		for line in result.stdout.splitlines():
			stripped = line.strip()
			if stripped.endswith(" V") or stripped == "V":
				faillock_info["failed_attempts"] += 1

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
    Runs pamtester to authenticate username against a PAM service.
    If run_as_user is set, uses runuser to drop privileges to that UID first
    so pam_faillock records failures for a non-root process (avoids root bypass).
    """
    if run_as_user:
        cmd = ["runuser", "-u", run_as_user, "--", "pamtester", service, username, "authenticate"]
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


# --- nobody approach (commented out) ---
# def set_nobody_password(password):
# 	"""
# 	Temporarily sets a password for the nobody user so pamtester can
# 	authenticate as nobody. Returns True on success, False otherwise.
# 	"""
# 	result = subprocess.run(
# 		["chpasswd"],
# 		input=f"nobody:{password}",
# 		capture_output=True,
# 		text=True,
# 		check=False
# 	)
# 	if result.returncode != 0:
# 		print(f"Warning: Could not set password for nobody: {result.stderr.strip()}")
# 		return False
# 	# Explicitly unlock the account - chpasswd sets the hash but may not
# 	# remove the '!' lock prefix in shadow, which pam_unix treats as locked.
# 	unlock_result = subprocess.run(
# 		["passwd", "-u", "nobody"],
# 		capture_output=True,
# 		text=True,
# 		check=False
# 	)
# 	if unlock_result.returncode != 0:
# 		print(f"Warning: Could not unlock nobody account: {unlock_result.stderr.strip()}")
# 	return True
#
# def lock_nobody_account():
# 	"""
# 	Locks the nobody account by disabling its password.
# 	This restores nobody to its default locked state after testing.
# 	"""
# 	subprocess.run(
# 		["passwd", "-l", "nobody"],
# 		capture_output=True,
# 		text=True,
# 		check=False
# 	)


def create_temp_user(username, password):
	"""
	Creates a temporary local user for PAM testing.
	The user gets a real shell (/bin/bash) and a known password so that
	pam_faillock will track failures correctly (no nologin/PAM account rejection).
	Returns True on success, False otherwise.
	"""
	result = subprocess.run(
		["useradd", "-m", "-s", "/bin/bash", username],
		capture_output=True,
		text=True,
		check=False
	)
	if result.returncode != 0:
		print(f"Warning: Could not create temp user '{username}': {result.stderr.strip()}")
		return False
	chpasswd_result = subprocess.run(
		["chpasswd"],
		input=f"{username}:{password}",
		capture_output=True,
		text=True,
		check=False
	)
	if chpasswd_result.returncode != 0:
		print(f"Warning: Could not set password for '{username}': {chpasswd_result.stderr.strip()}")
		subprocess.run(["userdel", "-r", username], capture_output=True, check=False)
		return False
	return True


def cleanup_temp_user(username):
	"""
	Removes a temporary user created for PAM testing, including home directory.
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

	test_password = generate_pamtest_password()

	# Create a temporary user with a real shell (/bin/bash) so that:
	#   1. The PAM account stack does not reject auth (no nologin shell).
	#   2. pam_faillock records failures under a non-root UID via runuser.
	test_user = f"csel_pt_{int(time.time())}"
	debug_log(f"Creating temp user: {test_user}")
	if not create_temp_user(test_user, test_password):
		debug_log(f"Failed to create temp user '{test_user}'")
		return None

	# --- nobody approach (commented out) ---
	# # Use the existing nobody user as the test target.
	# # nobody is a standard system user (UID 65534) present on all Linux systems.
	# # Pamtester is run via 'su nobody' so the process UID is 65534, not 0,
	# # which means pam_faillock will record failures normally without root bypass.
	# test_user = "nobody"
	# debug_log(f"Test user: {test_user} (existing system user)")
	# if not set_nobody_password(test_password):
	# 	debug_log("Failed to set password for nobody")
	# 	return None

	try:
		if shutil.which("faillock"):
			subprocess.run(
				["faillock", "--reset", "--user", test_user],
				capture_output=True,
				text=True,
				check=False
			)
			debug_log("faillock reset executed")
		else:
			debug_log("faillock binary not found; will rely on pamtester output only")

		wrong_password = "WrongP@ssword!123"

		# Diagnostic: test correct password as root first to confirm PAM stack works at all
		rc_root, out_root, err_root = pamtester_authenticate(service, test_user, test_password, run_as_user=None)
		debug_log(f"Diagnostic (correct password as root) rc={rc_root} out='{out_root.strip()}' err='{err_root.strip()}'")
		if rc_root != 0:
			print(f"Warning: PAM service '{service}' rejects correct password even as root; PAM stack may be misconfigured.")
			debug_log("Check /etc/pam.d/common-auth — pam_faillock authfail must come AFTER pam_unix, not before.")
			return None

		# Reset faillock so root diagnostic attempt doesn't count
		if shutil.which("faillock"):
			subprocess.run(
				["faillock", "--reset", "--user", test_user],
				capture_output=True, text=True, check=False
			)
			debug_log("faillock reset after root diagnostic")

		# Sanity check 1: correct password must succeed as temp user (via runuser)
		rc, out, err = pamtester_authenticate(service, test_user, test_password, run_as_user=test_user)
		debug_log(f"Sanity check (correct password as temp user via runuser) rc={rc} out='{out.strip()}' err='{err.strip()}'")
		if rc != 0:
			# runuser failed — fall back to root-invoked pamtester.
			# Note: root-invoked pamtester bypasses pam_faillock unless even_deny_root is set.
			debug_log("runuser approach failed; falling back to root-invoked pamtester.")
			run_as = None
		else:
			run_as = test_user

		# Reset faillock after the successful sanity check
		if shutil.which("faillock"):
			subprocess.run(
				["faillock", "--reset", "--user", test_user],
				capture_output=True, text=True, check=False
			)
			debug_log("faillock reset after correct-password sanity check")

		# Sanity check 2: wrong password must fail
		rc, out, err = pamtester_authenticate(service, test_user, wrong_password, run_as_user=run_as)
		debug_log(f"Sanity check (wrong password) rc={rc} out='{out.strip()}' err='{err.strip()}'")
		if rc == 0:
			print(f"Warning: PAM service '{service}' authenticates wrong passwords; cannot test lockout.")
			return None

		# Reset again so the sanity-check failure doesn't count toward the threshold
		if shutil.which("faillock"):
			subprocess.run(
				["faillock", "--reset", "--user", test_user],
				capture_output=True, text=True, check=False
			)
			debug_log("faillock reset after wrong-password sanity check")

		# Accumulate exactly expected_value - 1 failures, then verify not locked early
		# by attempting the correct password — it should still succeed.
		# A successful auth also resets the faillock counter, so we re-run the
		# expected_value - 1 failures again before the final threshold attempt.
		if expected_value > 1:
			for attempt in range(1, expected_value):
				rc, out, err = pamtester_authenticate(service, test_user, wrong_password, run_as_user=run_as)
				debug_log(f"Pre-check attempt {attempt}/{expected_value - 1} rc={rc} out='{out.strip()}' err='{err.strip()}'")

			rc, out, err = pamtester_authenticate(service, test_user, test_password, run_as_user=run_as)
			debug_log(f"Early-lockout check (correct password after {expected_value - 1} failures) rc={rc} out='{out.strip()}' err='{err.strip()}'")
			if rc != 0:
				debug_log("Account locked earlier than expected; deny is set too low")
				return False
			# Correct password succeeded (and reset the faillock counter).
			# Re-accumulate expected_value - 1 failures to set up for the threshold.
			if shutil.which("faillock"):
				subprocess.run(
					["faillock", "--reset", "--user", test_user],
					capture_output=True, text=True, check=False
				)
				debug_log("faillock reset before re-accumulation")

			for attempt in range(1, expected_value):
				rc, out, err = pamtester_authenticate(service, test_user, wrong_password, run_as_user=run_as)
				debug_log(f"Re-accumulate attempt {attempt}/{expected_value - 1} rc={rc} out='{out.strip()}' err='{err.strip()}'")

		# Final failure to reach the lockout threshold
		rc, out, err = pamtester_authenticate(service, test_user, wrong_password, run_as_user=run_as)
		debug_log(f"Final failure rc={rc} out='{out.strip()}' err='{err.strip()}'")

		# Correct password should now be rejected if lockout is enforced
		rc, out, err = pamtester_authenticate(service, test_user, test_password, run_as_user=run_as)
		debug_log(f"Correct password attempt after threshold rc={rc} out='{out.strip()}' err='{err.strip()}'")
		if rc != 0:
			debug_log("Correct password rejected after threshold; lockout confirmed")
			return True

		# Correct password succeeded — lockout not enforced
		debug_log("Correct password succeeded after threshold; lockout NOT enforced")
		return False
	finally:
		# Always reset faillock for the test user and remove the temp account
		if shutil.which("faillock"):
			subprocess.run(
				["faillock", "--reset", "--user", test_user],
				capture_output=True,
				text=True,
				check=False
			)
			debug_log("faillock reset executed (cleanup)")
		cleanup_temp_user(test_user)
		debug_log(f"Temp user '{test_user}' removed (cleanup)")
		# lock_nobody_account()  # nobody approach: re-lock nobody account
		# debug_log("nobody account re-locked (cleanup)")
