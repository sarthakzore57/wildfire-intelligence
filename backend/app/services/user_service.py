from typing import Optional, List
import logging

from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app import models, schemas
from app.core.security import get_password_hash, verify_password

# Configure logging
logger = logging.getLogger(__name__)

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    """
    Get a user by ID
    """
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """
    Get a user by email
    """
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """
    Get a user by username
    """
    return db.query(models.User).filter(models.User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[models.User]:
    """
    Get multiple users with pagination
    """
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user_in: schemas.UserCreate) -> Optional[models.User]:
    """
    Create a new user with improved error handling
    """
    try:
        # Check if a user with this email already exists
        existing_user = get_user_by_email(db, email=user_in.email)
        if existing_user:
            logger.warning(f"Attempted to create user with existing email: {user_in.email}")
            return None
        
        # Check if a user with this username already exists
        existing_username = get_user_by_username(db, username=user_in.username)
        if existing_username:
            logger.warning(f"Attempted to create user with existing username: {user_in.username}")
            return None
            
        # Create user object with all fields
        db_user = models.User(
            email=user_in.email,
            username=user_in.username,
            hashed_password=get_password_hash(user_in.password),
            is_active=True,
            is_superuser=False,
            latitude=user_in.latitude,
            longitude=user_in.longitude,
            region_name=user_in.region_name,
            alert_threshold=user_in.alert_threshold,
            email_alerts=user_in.email_alerts,
            sms_alerts=user_in.sms_alerts,
            phone_number=user_in.phone_number,
        )
        
        # Add to database
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"User created successfully: {user_in.username}")
        return db_user
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError creating user: {e}")
        return None
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"SQLAlchemyError creating user: {e}")
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating user: {e}")
        return None


def update_user(
    db: Session, user_id: int, user_in: schemas.UserUpdate
) -> Optional[models.User]:
    """
    Update a user
    """
    try:
        db_user = get_user(db, user_id)
        if not db_user:
            return None
        
        # Convert Pydantic model to dict, excluding unset fields
        update_data = user_in.model_dump(exclude_unset=True)
        
        # Handle password update separately
        if "password" in update_data and update_data["password"]:
            hashed_password = get_password_hash(update_data["password"])
            update_data["hashed_password"] = hashed_password
            del update_data["password"]
        
        # Update user model with the new data
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"User updated successfully: {db_user.username}")
        return db_user
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"SQLAlchemyError updating user: {e}")
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error updating user: {e}")
        return None


def delete_user(db: Session, user_id: int) -> bool:
    """
    Delete a user
    """
    try:
        db_user = get_user(db, user_id)
        if not db_user:
            return False
            
        db.delete(db_user)
        db.commit()
        
        logger.info(f"User deleted successfully: ID {user_id}")
        return True
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"SQLAlchemyError deleting user: {e}")
        return False
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error deleting user: {e}")
        return False


def authenticate(db: Session, email: str, password: str) -> Optional[models.User]:
    """
    Authenticate a user
    """
    try:
        user = get_user_by_email(db, email=email)
        if not user:
            logger.warning(f"Authentication failed: no user with email {email}")
            return None
            
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Authentication failed: invalid password for {email}")
            return None
            
        logger.info(f"User authenticated successfully: {email}")
        return user
        
    except Exception as e:
        logger.error(f"Error during authentication: {e}")
        return None


def check_db_connection(db: Session) -> bool:
    """
    Check if the database connection is working properly
    Returns True if connection is OK, False otherwise
    """
    try:
        # Execute a simple query to check connection
        db.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return False 
