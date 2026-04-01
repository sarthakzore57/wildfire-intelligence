import os
import sys
import logging
from pathlib import Path
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("fix_fire_incidents")

# Import the app modules
from app.db.session import engine, SessionLocal
from app.services import fire_risk_service
from app.models.fire_risk import FireIncident

def test_get_fire_incidents():
    """Try to reproduce the issue with get_fire_incidents"""
    logger.info("Testing get_fire_incidents function")
    
    try:
        # Create a database session
        db = SessionLocal()
        
        # Call the function with debug logging
        logger.info("Calling get_fire_incidents")
        incidents = fire_risk_service.get_fire_incidents(db)
        
        # Log the result
        logger.info(f"Successfully retrieved {len(incidents)} fire incidents")
        
        # Print first 5 incidents for debugging
        for i, incident in enumerate(incidents[:5]):
            logger.info(f"Incident {i+1}:")
            logger.info(f"  ID: {incident.id}")
            logger.info(f"  Risk Zone ID: {incident.risk_zone_id}")
            logger.info(f"  Location: {incident.latitude}, {incident.longitude}")
            logger.info(f"  Severity: {incident.severity}")
            logger.info(f"  Status: {incident.status}")
            logger.info(f"  Source: {incident.source}")
        
    except Exception as e:
        logger.error(f"Error in get_fire_incidents: {e}", exc_info=True)
    finally:
        db.close()

def check_fire_incidents_table():
    """Check the structure of the fire_incidents table"""
    logger.info("Checking fire_incidents table structure")
    
    try:
        # Create a database session
        db = SessionLocal()
        
        # Get the table schema
        from sqlalchemy import inspect
        inspector = inspect(engine)
        columns = inspector.get_columns('fire_incidents')
        
        logger.info("Fire incidents table columns:")
        for column in columns:
            logger.info(f"  {column['name']}: {column['type']}")
        
        # Check if there are any records
        count = db.query(FireIncident).count()
        logger.info(f"Found {count} fire incident records in the database")
        
        # If there are no records, try to understand why
        if count == 0:
            logger.info("No fire incidents found. Checking if import script was run")
            # You might want to check logs or run the import script here
        
    except Exception as e:
        logger.error(f"Error checking fire_incidents table: {e}", exc_info=True)
    finally:
        db.close()

def check_fire_incident_model():
    """Check the FireIncident model definition"""
    logger.info("Checking FireIncident model")
    
    try:
        # Print the model attributes
        for attr in dir(FireIncident):
            if not attr.startswith('_'):
                logger.info(f"  {attr}: {getattr(FireIncident, attr)}")
        
    except Exception as e:
        logger.error(f"Error checking FireIncident model: {e}", exc_info=True)

def test_create_fire_incident():
    """Try to create a test fire incident to check the model"""
    logger.info("Testing fire incident creation")
    
    try:
        # Create a database session
        db = SessionLocal()
        
        # First, get a risk zone to associate with
        from app.models.fire_risk import FireRiskZone
        risk_zone = db.query(FireRiskZone).first()
        
        if not risk_zone:
            logger.error("No risk zones found to associate with fire incident")
            return
        
        logger.info(f"Found risk zone with ID {risk_zone.id}")
        
        # Try to create a simple fire incident
        from datetime import datetime
        test_incident = FireIncident(
            risk_zone_id=risk_zone.id,
            latitude=risk_zone.latitude,
            longitude=risk_zone.longitude,
            start_date=datetime.utcnow(),
            severity="Medium",
            status="Active",
            source="Test Script",
            description="Test fire incident for debugging"
        )
        
        # Don't commit, just check if the model instantiates correctly
        logger.info("Successfully created test fire incident")
        logger.info(f"  ID: {test_incident.id}")
        logger.info(f"  Risk Zone ID: {test_incident.risk_zone_id}")
        logger.info(f"  Location: {test_incident.latitude}, {test_incident.longitude}")
        logger.info(f"  Severity: {test_incident.severity}")
        logger.info(f"  Status: {test_incident.status}")
        logger.info(f"  Source: {test_incident.source}")
        
    except Exception as e:
        logger.error(f"Error creating test fire incident: {e}", exc_info=True)
    finally:
        db.close()

def main():
    """Run all debug tests"""
    logger.info("Starting fire incidents debug tests")
    
    # Run each test function
    check_fire_incidents_table()
    check_fire_incident_model()
    test_get_fire_incidents()
    test_create_fire_incident()
    
    logger.info("Completed fire incidents debug tests")

if __name__ == "__main__":
    main() 