#!/bin/bash
# Run All Script for Forest Fire Prediction System
# This shell script runs all data integration scripts in sequence

# Exit on any error
set -e

# Set script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Log file
LOG_FILE="$SCRIPT_DIR/run_all_shell.log"

# Function to log messages
log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Create log file
touch "$LOG_FILE"
log "Starting Forest Fire Prediction System initialization"

# Run setup script
log "Running setup.py..."
python setup.py
log "Setup complete"

# Run database initialization
log "Running init_db.py..."
python init_db.py
log "Database initialization complete"

# Import historical data
log "Running import_historical_fire_data.py..."
python import_historical_fire_data.py
log "Historical data import complete"

# Fetch real-time data
log "Running realtime_fire_data.py..."
python realtime_fire_data.py
log "Real-time data fetch complete"

# Done
log "All scripts completed successfully"
log "Forest Fire Prediction System is now ready to use!"
log "You can start the backend server with: uvicorn app.main:app --reload"

echo ""
echo "================================================"
echo "  Forest Fire Prediction System is ready to use  "
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Start the backend server: cd .. && uvicorn app.main:app --reload"
echo "2. Start the frontend server: cd ../../frontend && npm start"
echo "" 