#!/bin/bash
# run_binary.sh
# Updates the current git repository and then executes a specified file, 
# treating .py files as Python scripts and others as direct executables.

# Exit immediately if a command exits with a non-zero status
set -e

# --- 1. Argument Check ---
if [ -z "$1" ]; then
    echo "Error: Please provide the filename to run as the first argument." >&2
    echo "Usage: $0 <filename> [optional_args_for_file...]"
    exit 1
fi

FILE_TO_RUN="$1"

# --- 2. Git Pull ---
echo "--- Running git pull to update the repository ---"

# Check if we are inside a Git repository
if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    # Run git pull.
    git pull
    echo "--- Repository update complete ---"
else
    echo "Warning: Not inside a Git repository. Skipping 'git pull'." >&2
fi

# --- 3. Execution Check and Preparation ---

# Check if the file exists
if [ ! -f "$FILE_TO_RUN" ]; then
    echo "Error: File '$FILE_TO_RUN' not found in the current directory." >&2
    exit 1
fi

# --- 4. Execute File ---

# Check if the file name ends with .py
if [[ "$FILE_TO_RUN" == *.py ]]; then
    echo "--- Identified as Python script. Executing with python3 ---"
    # Execute the Python script. $1 is the script name, and ${@:2} are its arguments.
    python3 "$FILE_TO_RUN" "${@:2}"
else
    # Treat as a regular binary/executable.
    if [ ! -x "$FILE_TO_RUN" ]; then
        echo "Making '$FILE_TO_RUN' executable..."
        chmod +x "$FILE_TO_RUN"
    fi
    echo "--- Identified as binary executable. Executing directly ---"
    # Execute the binary directly. $1 is the binary path, and ${@:2} are its arguments.
    ./"$FILE_TO_RUN" "${@:2}"
fi

EXIT_CODE=$?
echo "--- Execution of $FILE_TO_RUN finished with exit code $EXIT_CODE ---"

# Exit with the same status as the executed program
exit $EXIT_CODE
