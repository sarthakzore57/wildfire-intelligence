#!/usr/bin/env python
"""
Database Initialization Script

This script initializes the SQLite database by creating all necessary tables
defined in the SQLAlchemy models.
"""

import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the path so we can import from the app package
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir.parent))

from app.db.session import Base, engine
from app.models import user, fire_risk  # Import all model modules to register them with the Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("init_db.log")
    ]
)
logger = logging.getLogger("init_db")

def init_db():
    """Initialize the database by creating all tables."""
    logger.info("Initializing database...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Successfully created all database tables")
        
        # List created tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        logger.info(f"Created tables: {', '.join(table_names)}")
        
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

def create_admin_user():
    """Create an admin user if no users exist."""
    from sqlalchemy.orm import Session
    from app.core.security import get_password_hash
    from app.models.user import User

    logger.info("Checking for existing users...")
    
    try:
        with Session(engine) as session:
            # Check if any users exist
            user_count = session.query(User).count()
            
            if user_count == 0:
                logger.info("No users found. Creating admin user...")
                
                # Create admin user with username instead of full_name
                admin_user = User(
                    email="admin@forestfire.com",
                    username="admin",
                    hashed_password=get_password_hash("adminpassword"),
                    is_superuser=True,
                    is_active=True
                )
                
                session.add(admin_user)
                session.commit()
                
                logger.info("Admin user created successfully")
                logger.info("Admin credentials:")
                logger.info("Email: admin@forestfire.com")
                logger.info("Username: admin")
                logger.info("Password: adminpassword")
                logger.info("Please change this password immediately after first login!")
            else:
                logger.info(f"Found {user_count} existing users. Skipping admin user creation.")
                
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")

def main():
    """Main function to run the database initialization process."""
    logger.info("Starting database initialization")
    
    try:
        # Initialize database
        init_db()
        
        # Create admin user
        create_admin_user()
        
        logger.info("Database initialization complete")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 