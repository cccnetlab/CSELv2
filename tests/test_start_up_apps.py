#!/usr/bin/env python3
"""
Interactive test harness for start_up_apps / _is_valid_autostart_file.

Must be run as root (or with sudo) so it can write to /etc/xdg/autostart.

Usage:
    sudo python3 tests/test_start_up_apps.py
"""

import os
import sys
import shutil
import textwrap
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap imports from the project root
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# We only need _is_valid_autostart_file — extract it via AST so we never have
# to execute the module-level scoring-engine bootstrap (DB connections, etc.).
import ast

def _load_helpers():
    """
    Extract _is_valid_autostart_file from scoring_engine.py using AST so that
    none of the module-level bootstrap code (DB, inotify, tkinter…) is executed.
    The function only depends on configparser, re, os, and shutil — all stdlib.
    """
    src_path = PROJECT_ROOT / "src" / "scoring_engine.py"
    source   = src_path.read_text()
    tree     = ast.parse(source)
    lines    = source.splitlines()

    func_source = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_is_valid_autostart_file":
            func_source = "\n".join(lines[node.lineno - 1 : node.end_lineno])
            break

    if func_source is None:
        raise RuntimeError(
            "Could not find _is_valid_autostart_file in src/scoring_engine.py. "
            "Has the function been renamed or moved?"
        )

    import configparser, re
    ns = {
        "configparser": configparser,
        "re": re,
        "os": os,
        "shutil": shutil,
    }
    exec(compile(func_source, str(src_path), "exec"), ns)  # noqa: S102
    return ns["_is_valid_autostart_file"]


# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------
GREEN  = "\033[32m"
RED    = "\033[31m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def banner(text):
    width = 70
    print()
    print(BOLD + CYAN + "=" * width + RESET)
    print(BOLD + CYAN + f"  {text}" + RESET)
    print(BOLD + CYAN + "=" * width + RESET)

def section(text):
    print()
    print(BOLD + YELLOW + f"--- {text} ---" + RESET)

def pause(expected: str, notes: str = ""):
    """
    Print expected behaviour and ask the user to confirm.
    Returns True if the user said 'y', False for 'n'.
    """
    print()
    print(BOLD + "Expected: " + RESET + expected)
    if notes:
        print(BOLD + "Notes:    " + RESET + notes)
    while True:
        answer = input(BOLD + "Did the engine behave correctly? [y/n]: " + RESET).strip().lower()
        if answer in ("y", "n"):
            if answer == "y":
                print(GREEN + "✓ PASS" + RESET)
            else:
                print(RED + "✗ FAIL" + RESET)
            return answer == "y"
        print("Please enter y or n.")


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------
PROG        = "csel-test-app"
DESKTOP     = f"{PROG}.desktop"
GLOBAL_DIR  = Path("/etc/xdg/autostart")
SUDO_USER   = os.environ.get("SUDO_USER", "")
USER_HOME   = Path(f"/home/{SUDO_USER}") if SUDO_USER else Path.home()
USER_DIR    = USER_HOME / ".config/autostart"

# A real binary that exists on every system
VALID_EXEC  = "/usr/bin/bash"

GLOBAL_PATH = GLOBAL_DIR  / DESKTOP
USER_PATH   = USER_DIR    / DESKTOP


def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content))
    print(f"  [wrote] {path}")


def remove_file(path: Path):
    if path.exists():
        path.unlink()
        print(f"  [removed] {path}")


def remove_both():
    remove_file(GLOBAL_PATH)
    remove_file(USER_PATH)


# ---------------------------------------------------------------------------
# Thin scorer shim — wraps _is_valid_autostart_file to print what it sees
# ---------------------------------------------------------------------------
def evaluate(label: str, fn_valid):
    """
    Call _is_valid_autostart_file on both paths and print a human-readable
    summary of what the engine will do for this program.
    """
    section(f"Engine evaluation for: {label}")

    user_valid, user_hidden = fn_valid(USER_PATH)   if USER_PATH.exists()   else (False, False)
    glob_valid, glob_hidden = fn_valid(GLOBAL_PATH) if GLOBAL_PATH.exists() else (False, False)

    def fmt(exists, valid, hidden):
        if not exists:  return RED    + "does not exist"   + RESET
        if not valid:   return YELLOW + "INVALID"          + RESET
        hid = (GREEN + "Hidden=true"  + RESET) if hidden else (RED + "Hidden≠true" + RESET)
        return GREEN + "valid" + RESET + f", {hid}"

    print(f"  User file   ({USER_PATH}): "
          f"{fmt(USER_PATH.exists(),   user_valid, user_hidden)}")
    print(f"  Global file ({GLOBAL_PATH}): "
          f"{fmt(GLOBAL_PATH.exists(), glob_valid, glob_hidden)}")

    # Replicate the scoring logic verbatim
    if USER_PATH.exists() and user_valid:
        decision = "HIT" if user_hidden else "MISS"
        reason   = "user file is valid — scoring on Hidden"
    elif GLOBAL_PATH.exists() and glob_valid:
        decision = "HIT" if glob_hidden else "MISS"
        reason   = "user file absent/invalid — global file is valid — scoring on Hidden"
    else:
        decision  = "HIT"
        reason    = "no valid autostart entry — program is not configured to autostart"

    colour = GREEN if decision == "HIT" else RED
    print(f"\n  {BOLD}Engine decision → {colour}{decision}{RESET}{BOLD}  ({reason}){RESET}")
    return decision


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------
def run_tests(fn_valid):
    results = []

    def record(name, passed):
        results.append((name, passed))

    # -----------------------------------------------------------------------
    banner("TEST 1 — No files exist → HIT")
    # -----------------------------------------------------------------------
    remove_both()
    evaluate("no files", fn_valid)
    ok = pause(
        "HIT — no autostart file found anywhere, program is not configured to autostart.",
    )
    record("No files exist → HIT", ok)

    # -----------------------------------------------------------------------
    banner("TEST 2 — Valid global file, Hidden=true → HIT")
    # -----------------------------------------------------------------------
    remove_both()
    write_file(GLOBAL_PATH, f"""\
        [Desktop Entry]
        Name=CSEL Test App
        Exec={VALID_EXEC}
        Type=Application
        Hidden=true
    """)
    evaluate("valid global, Hidden=true", fn_valid)
    ok = pause(
        "HIT — global file is valid and Hidden=true.",
    )
    record("Valid global, Hidden=true → HIT", ok)

    # -----------------------------------------------------------------------
    banner("TEST 3 — Valid global file, Hidden=false → MISS")
    # -----------------------------------------------------------------------
    remove_both()
    write_file(GLOBAL_PATH, f"""\
        [Desktop Entry]
        Name=CSEL Test App
        Exec={VALID_EXEC}
        Type=Application
        Hidden=false
    """)
    evaluate("valid global, Hidden=false", fn_valid)
    ok = pause(
        "MISS — global file is valid but Hidden is not 'true'.",
    )
    record("Valid global, Hidden=false → MISS", ok)

    # -----------------------------------------------------------------------
    banner("TEST 4 — Valid global file, no Hidden key → MISS")
    # -----------------------------------------------------------------------
    remove_both()
    write_file(GLOBAL_PATH, f"""\
        [Desktop Entry]
        Name=CSEL Test App
        Exec={VALID_EXEC}
        Type=Application
    """)
    evaluate("valid global, no Hidden", fn_valid)
    ok = pause(
        "MISS — global file is valid but no Hidden key present.",
    )
    record("Valid global, no Hidden → MISS", ok)

    # -----------------------------------------------------------------------
    banner("TEST 5 — Valid global (Hidden=false), valid user (Hidden=true) → HIT")
    # -----------------------------------------------------------------------
    remove_both()
    write_file(GLOBAL_PATH, f"""\
        [Desktop Entry]
        Name=CSEL Test App
        Exec={VALID_EXEC}
        Type=Application
        Hidden=false
    """)
    write_file(USER_PATH, f"""\
        [Desktop Entry]
        Name=CSEL Test App
        Exec={VALID_EXEC}
        Type=Application
        Hidden=true
    """)
    evaluate("global Hidden=false, user Hidden=true", fn_valid)
    ok = pause(
        "HIT — user file is checked first; it is valid and Hidden=true.",
    )
    record("User overrides global (user Hidden=true) → HIT", ok)

    # -----------------------------------------------------------------------
    banner("TEST 6 — Valid global (Hidden=true), valid user (Hidden=false) → MISS")
    # -----------------------------------------------------------------------
    remove_both()
    write_file(GLOBAL_PATH, f"""\
        [Desktop Entry]
        Name=CSEL Test App
        Exec={VALID_EXEC}
        Type=Application
        Hidden=true
    """)
    write_file(USER_PATH, f"""\
        [Desktop Entry]
        Name=CSEL Test App
        Exec={VALID_EXEC}
        Type=Application
        Hidden=false
    """)
    evaluate("global Hidden=true, user Hidden=false", fn_valid)
    ok = pause(
        "MISS — user file is checked first; it is valid but Hidden is not 'true'.",
    )
    record("User overrides global (user Hidden=false) → MISS", ok)

    # -----------------------------------------------------------------------
    banner("TEST 7 — Valid global (Hidden=true), INVALID user file → HIT (falls back to global)")
    # -----------------------------------------------------------------------
    remove_both()
    write_file(GLOBAL_PATH, f"""\
        [Desktop Entry]
        Name=CSEL Test App
        Exec={VALID_EXEC}
        Type=Application
        Hidden=true
    """)
    write_file(USER_PATH, """\
        [Desktop Entry]
        Name=CSEL Test App
        Type=Application
        Hidden=true
    """)  # Missing Exec — invalid
    evaluate("global valid Hidden=true, user missing Exec", fn_valid)
    ok = pause(
        "HIT — user file is invalid (missing Exec); falls back to global which is valid and Hidden=true.",
    )
    record("Invalid user (no Exec) falls back to global Hidden=true → HIT", ok)

    # -----------------------------------------------------------------------
    banner("TEST 8 — Invalid global (bad Exec path), no user file → HIT (no valid entry)")
    # -----------------------------------------------------------------------
    remove_both()
    write_file(GLOBAL_PATH, """\
        [Desktop Entry]
        Name=CSEL Test App
        Exec=/nonexistent/binary/that/does/not/exist
        Type=Application
        Hidden=true
    """)
    evaluate("global invalid Exec, no user", fn_valid)
    ok = pause(
        "HIT — global file is invalid (Exec binary not found); no valid entry anywhere.",
    )
    record("Invalid global Exec, no user → HIT", ok)

    # -----------------------------------------------------------------------
    banner("TEST 9 — Global file missing [Desktop Entry] section → falls through → HIT")
    # -----------------------------------------------------------------------
    remove_both()
    write_file(GLOBAL_PATH, f"""\
        Name=CSEL Test App
        Exec={VALID_EXEC}
        Type=Application
        Hidden=true
    """)  # No [Desktop Entry] header
    evaluate("global no section header", fn_valid)
    ok = pause(
        "HIT — global file has no [Desktop Entry] section so it is invalid; no valid entry.",
    )
    record("Global missing [Desktop Entry] → HIT", ok)

    # -----------------------------------------------------------------------
    banner("TEST 10 — Whitespace around '=' in Hidden (Hidden = true) → HIT")
    # -----------------------------------------------------------------------
    remove_both()
    write_file(USER_PATH, f"""\
        [Desktop Entry]
        Name=CSEL Test App
        Exec={VALID_EXEC}
        Type=Application
        Hidden = true
    """)
    evaluate("user, Hidden = true (spaces around =)", fn_valid)
    ok = pause(
        "HIT — 'Hidden = true' with spaces around '=' should be treated the same as 'Hidden=true'.",
        notes="configparser strips whitespace around the value automatically.",
    )
    record("Hidden = true (whitespace-insensitive) → HIT", ok)

    # -----------------------------------------------------------------------
    banner("TEST 11 — Hidden=TRUE (wrong case) → MISS")
    # -----------------------------------------------------------------------
    remove_both()
    write_file(USER_PATH, f"""\
        [Desktop Entry]
        Name=CSEL Test App
        Exec={VALID_EXEC}
        Type=Application
        Hidden=TRUE
    """)
    evaluate("user, Hidden=TRUE", fn_valid)
    ok = pause(
        "MISS — 'Hidden=TRUE' uses uppercase 'TRUE'; the check is case-sensitive and only 'true' qualifies.",
    )
    record("Hidden=TRUE (case-sensitive) → MISS", ok)

    # -----------------------------------------------------------------------
    banner("TEST 12 — Type=application (lowercase) → still valid → HIT")
    # -----------------------------------------------------------------------
    remove_both()
    write_file(USER_PATH, f"""\
        [Desktop Entry]
        Name=CSEL Test App
        Exec={VALID_EXEC}
        Type=application
        Hidden=true
    """)
    evaluate("user, Type=application (lowercase)", fn_valid)
    ok = pause(
        "HIT — Type matching is case-insensitive; 'application' == 'Application'.",
    )
    record("Type=application (case-insensitive) → HIT", ok)

    # -----------------------------------------------------------------------
    # Cleanup
    # -----------------------------------------------------------------------
    remove_both()

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    banner("RESULTS")
    passed = sum(1 for _, r in results if r)
    total  = len(results)
    for name, ok in results:
        mark = GREEN + "PASS" + RESET if ok else RED + "FAIL" + RESET
        print(f"  [{mark}]  {name}")
    print()
    colour = GREEN if passed == total else RED
    print(BOLD + colour + f"  {passed}/{total} tests passed" + RESET)
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if os.geteuid() != 0:
        print(RED + "ERROR: This test must be run as root (writes to /etc/xdg/autostart)." + RESET)
        print("  sudo python3 tests/test_start_up_apps.py")
        sys.exit(1)

    if not SUDO_USER:
        print(YELLOW + "WARNING: SUDO_USER not set — user autostart dir will be " + str(USER_DIR) + RESET)

    print(BOLD + "\nCSEL start_up_apps interactive test harness" + RESET)
    print(f"  Program under test : {PROG}")
    print(f"  User autostart dir : {USER_DIR}")
    print(f"  Global autostart   : {GLOBAL_DIR}")
    print(f"  Valid Exec binary  : {VALID_EXEC}")

    fn_valid = _load_helpers()
    run_tests(fn_valid)
