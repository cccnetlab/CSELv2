#!/bin/bash
# run_binary.sh
# Updates the current git repository, executes a specified file, redirects 
# all output to 'output.txt', and then conditionally commits/pushes the log.

# --- Configuration ---
OUTPUT_FILE="output.txt"

# Redirect stdout and stderr of the entire script to the output file.
# NOTE: All subsequent script and program output will be written to this file.
exec > "$OUTPUT_FILE" 2>&1

# Exit immediately if a command exits with a non-zero status
# (We manage the program's exit code separately, but set -e applies to git commands)
set -e

# --- 1. Argument Check ---
if [ -z "$1" ]; then
    echo "Error: Please provide the filename to run as the first argument."
    echo "Usage: $0 <filename> [optional_args_for_file...]"
    # Since we are redirecting output, we still exit here but the error is logged.
    exit 1
fi

FILE_TO_RUN="$1"
echo "Target file: $FILE_TO_RUN"
echo "Log file: $OUTPUT_FILE"

# --- 2. Git Pull ---
echo "--- Running git pull to update the repository ---"

# Check if we are inside a Git repository
if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    # Run git pull.
    git pull
    echo "--- Repository update complete ---"
else
    echo "Warning: Not inside a Git repository. Skipping 'git pull'."
fi

# --- 3. Execution Check and Preparation ---

# Check if the file exists
if [ ! -f "$FILE_TO_RUN" ]; then
    echo "Error: File '$FILE_TO_RUN' not found in the current directory."
    exit 1
fi

# --- 4. Execute File ---

PROGRAM_EXIT_CODE=0 # Initialize exit code

# Check if the file name ends with .py
if [[ "$FILE_TO_RUN" == *.py ]]; then
    echo "--- Identified as Python script. Executing with python3 ---"
    # Execute the Python script. $1 is the script name, and ${@:2} are its arguments.
    python3 "$FILE_TO_RUN" "${@:2}"
    PROGRAM_EXIT_CODE=$?
else
    # Treat as a regular binary/executable.
    if [ ! -x "$FILE_TO_RUN" ]; then
        echo "Making '$FILE_TO_RUN' executable..."
        chmod +x "$FILE_TO_RUN"
    fi
    echo "--- Identified as binary executable. Executing directly ---"
    # Execute the binary directly. $1 is the binary path, and ${@:2} are its arguments.
    ./"$FILE_TO_RUN" "${@:2}"
    PROGRAM_EXIT_CODE=$?
fi

echo "--- Program Execution finished with exit code $PROGRAM_EXIT_CODE ---"

# --- 5. Conditional Git Push ---

echo "--- Post-execution tasks ---"

if [ $PROGRAM_EXIT_CODE -eq 0 ]; then
    echo "Program executed successfully. Starting Git commit and push of $OUTPUT_FILE."
    
    # Re-check if we are inside a Git repository before attempting to push
    if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
        
        # Add the generated output file
        git add "$OUTPUT_FILE"
        
        # Commit the change
        COMMIT_MSG="[Automated Run] Log for $FILE_TO_RUN (Exit Code 0) on $(date +%Y-%m-%d_%H:%M:%S)"
        git commit -m "$COMMIT_MSG"
        
        # Push the commit
        echo "Attempting to push changes..."
        # We wrap git push in a block to catch errors explicitly instead of relying on set -e
        if git push; then
            echo "Successfully pushed changes to remote."
        else
            # Error output from git push will already be in output.txt due to redirection
            echo "Error: Git push failed. Check the log for details."
            # We don't change the final exit code of the script based on push failure
        fi
    else
        echo "Warning: Not inside a Git repository. Skipping Git commit/push."
    fi
else
    echo "Program failed (Exit Code: $PROGRAM_EXIT_CODE). Skipping Git commit/push."
fi

# Exit with the same status as the executed program
exit $PROGRAM_EXIT_CODE
