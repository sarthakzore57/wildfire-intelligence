#!/usr/bin/env python
"""
Setup Script for Forest Fire Prediction System

This script sets up the necessary directories and checks for required data files.
It also creates the SQLite database and initializes it with tables if they don't exist.
"""

import os
import sys
import logging
import shutil
from pathlib import Path
import subprocess

# Add the parent directory to the path so we can import from the app package
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("setup.log")
    ]
)
logger = logging.getLogger("setup")

def create_directories():
    """Create necessary directories for the application."""
    logger.info("Creating necessary directories...")
    
    # Define directories to create
    dirs = [
        script_dir / "data",
        script_dir / "data" / "raw",
        script_dir / "data" / "processed",
        script_dir / "logs",
    ]
    
    for directory in dirs:
        if not directory.exists():
            logger.info(f"Creating directory: {directory}")
            directory.mkdir(parents=True, exist_ok=True)
        else:
            logger.info(f"Directory already exists: {directory}")
    
    logger.info("Directory creation complete")

def check_environment():
    """Check if the environment is properly set up."""
    logger.info("Checking environment setup...")
    
    # Check for .env file
    env_file = script_dir.parent / ".env"
    if not env_file.exists():
        logger.warning(".env file not found. Creating from example...")
        env_example = script_dir.parent / ".env.example"
        if env_example.exists():
            shutil.copy(env_example, env_file)
            logger.info("Created .env file from .env.example")
        else:
            logger.error(".env.example file not found. Please create a .env file manually.")
    else:
        logger.info(".env file exists")
    
    # Check for SQLite database
    db_file = script_dir.parent / "sqlite.db"
    if not db_file.exists():
        logger.info("SQLite database not found. It will be created automatically when you run 'init_db.py'")
    else:
        logger.info(f"SQLite database exists at {db_file}")
    
    logger.info("Environment check complete")

def install_requirements():
    """Install required Python packages."""
    logger.info("Checking and installing required packages...")
    
    requirements_file = script_dir.parent / "requirements.txt"
    if not requirements_file.exists():
        logger.error("requirements.txt file not found")
        return
    
    try:
        logger.info("Installing required packages...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)], check=True)
        logger.info("Package installation complete")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing packages: {e}")

def setup_database():
    """Set up the database by running the initialization script."""
    logger.info("Setting up database...")
    
    init_db_script = script_dir / "init_db.py"
    if not init_db_script.exists():
        logger.error("init_db.py script not found")
        return
    
    try:
        logger.info("Running database initialization script...")
        subprocess.run([sys.executable, str(init_db_script)], check=True)
        logger.info("Database setup complete")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error setting up database: {e}")

def main():
    """Main function to run the setup process."""
    logger.info("Starting setup process for Forest Fire Prediction System")
    
    create_directories()
    check_environment()
    install_requirements()
    
    # We'll skip the database setup here since it will be run separately
    
    logger.info("Setup process complete")
    logger.info("\nNext steps:")
    logger.info("1. Run database initialization: python scripts/init_db.py")
    logger.info("2. Import historical fire data: python scripts/import_historical_fire_data.py")
    logger.info("3. Set up realtime data fetching: python scripts/realtime_fire_data.py")
    logger.info("4. Start the application: uvicorn app.main:app --reload")

if __name__ == "__main__":
    main() 