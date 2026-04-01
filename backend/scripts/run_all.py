#!/usr/bin/env python
"""
Run All Scripts

This script runs all the necessary scripts to set up the system and import data.
It's a one-click solution to initialize the Forest Fire Prediction System.
"""

import os
import sys
import logging
import subprocess
import time
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("run_all.log")
    ]
)
logger = logging.getLogger("run_all")

# Script directory
script_dir = Path(__file__).resolve().parent

def run_script(script_name):
    """Run a Python script and return True if successful."""
    script_path = script_dir / script_name
    
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False
    
    try:
        logger.info(f"Running {script_name}...")
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Log output
        if result.stdout:
            for line in result.stdout.splitlines():
                logger.info(f"[{script_name}] {line}")
        
        if result.stderr:
            for line in result.stderr.splitlines():
                logger.warning(f"[{script_name}] {line}")
        
        logger.info(f"Successfully completed {script_name}")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running {script_name}: {e}")
        if e.stdout:
            logger.info(f"Output: {e.stdout}")
        if e.stderr:
            logger.error(f"Error: {e.stderr}")
        return False

def setup_firebase():
    """Set up placeholder Firebase credentials if not exists."""
    try:
        # Check for Firebase credentials
        config_dir = Path(__file__).resolve().parent.parent / "app" / "core" / "config"
        config_dir.mkdir(exist_ok=True)
        cred_file = config_dir / "firebase-credentials.json"
        
        if not cred_file.exists():
            logger.info("Setting up Firebase credentials placeholder...")
            
            # Create a placeholder credentials file
            placeholder = {
                "type": "service_account",
                "project_id": "forest-fire-prediction-demo",
                "private_key_id": "your-private-key-id-here",
                "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----\n",
                "client_email": "firebase-adminsdk-xxxxx@forest-fire-prediction-demo.iam.gserviceaccount.com",
                "client_id": "your-client-id-here",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": "your-cert-url-here"
            }
            
            with open(cred_file, "w") as f:
                json.dump(placeholder, f, indent=2)
            
            logger.info(f"Created placeholder Firebase credentials at {cred_file}")
            logger.info("Please replace with actual Firebase credentials for real-time updates")
            
            # Add Firebase URL to .env file if not already there
            env_file = Path(__file__).resolve().parent.parent.parent / ".env"
            if env_file.exists():
                with open(env_file, "r") as f:
                    env_content = f.read()
                
                # Check if Firebase URL is already in the file
                if "FIREBASE_DATABASE_URL" not in env_content:
                    with open(env_file, "a") as f:
                        f.write("\n# Firebase settings\n")
                        f.write("FIREBASE_DATABASE_URL=https://forest-fire-prediction-default-rtdb.firebaseio.com/\n")
                        f.write("FIREBASE_CREDENTIALS_PATH=app/core/config/firebase-credentials.json\n")
                    
                    logger.info(f"Added Firebase configuration to {env_file}")
                    
            return True
            
        else:
            logger.info(f"Firebase credentials already exist at {cred_file}")
            return True
            
    except Exception as e:
        logger.error(f"Error setting up Firebase: {e}")
        return False

def main():
    """Main function to run all scripts in sequence."""
    logger.info("Starting Forest Fire Prediction System initialization")
    
    # Set up Firebase first
    setup_firebase()
    
    # Define scripts to run in order
    scripts = [
        "setup.py",
        "init_db.py",
        "import_historical_fire_data.py",
        "realtime_fire_data.py"
    ]
    
    # Track successful scripts
    successful = 0
    
    # Run each script
    for script in scripts:
        if run_script(script):
            successful += 1
        else:
            logger.warning(f"Script {script} failed or was skipped")
    
    # Print summary
    logger.info("\n" + "="*50)
    logger.info(f"Initialization complete: {successful}/{len(scripts)} scripts ran successfully")
    logger.info("="*50)
    
    if successful == len(scripts):
        logger.info("Forest Fire Prediction System is now ready to use!")
        logger.info("You can start the backend server with: uvicorn app.main:app --reload")
        logger.info("You can start the frontend with: cd ../frontend && npm start")
        logger.info("")
        logger.info("NOTE: To enable real-time updates with Firebase:")
        logger.info("1. Create a Firebase project at https://console.firebase.google.com/")
        logger.info("2. Set up Realtime Database")
        logger.info("3. Generate a private key for service account")
        logger.info("4. Replace the placeholder credentials in app/core/config/firebase-credentials.json")
    else:
        logger.warning("Some scripts failed. Please check the logs and fix the issues before starting the system.")

if __name__ == "__main__":
    main() 