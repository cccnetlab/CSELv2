#!/bin/bash

# Safe Scoring Engine Starter
# Ensures only one instance is running at a time

echo "================================================"
echo "Safe Scoring Engine Starter"
echo "================================================"
echo ""

# Check if already running
RUNNING=$(pgrep -f "scoring_engine.py" | wc -l)

if [ $RUNNING -gt 0 ]; then
    echo "⚠️  WARNING: Scoring engine is already running!"
    echo ""
    echo "Running processes:"
    ps aux | grep scoring_engine | grep -v grep
    echo ""
    echo -n "Do you want to stop all instances and restart? (y/N): "
    read -r response
    
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo ""
        echo "Stopping all scoring_engine processes..."
        sudo pkill -f scoring_engine.py
        sleep 2
        
        # Verify they're stopped
        STILL_RUNNING=$(pgrep -f "scoring_engine.py" | wc -l)
        if [ $STILL_RUNNING -gt 0 ]; then
            echo "✗ Failed to stop all processes. Force killing..."
            sudo pkill -9 -f scoring_engine.py
            sleep 1
        fi
        echo "✓ All instances stopped"
    else
        echo "Exiting without changes."
        exit 0
    fi
fi

echo ""
echo "Starting scoring engine (ONE instance only)..."
echo ""

# Change to script directory(Works using git root to ensure correct path, must be run inside git repo)
cd "$(git rev-parse --show-toplevel)"

# Start the scoring engine
sudo .venv/bin/python3.12 src/scoring_engine.py
