import os
import json
import logging
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, db, firestore
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# Check if Firebase credentials exist
firebase_initialized = False
firebase_db = None
firestore_db = None

def init_firebase():
    """Initialize Firebase with credentials from environment or config file"""
    global firebase_initialized, firebase_db, firestore_db
    
    if firebase_initialized:
        return firebase_db, firestore_db
    
    try:
        # Check for Firebase credentials
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        if cred_path and Path(cred_path).exists():
            cred = credentials.Certificate(cred_path)
        else:
            # Look for credentials file in config directory
            config_dir = Path(__file__).parent.parent / "core" / "config"
            cred_file = config_dir / "firebase-credentials.json"
            
            if not cred_file.exists():
                logger.warning("Firebase credentials not found. Creating placeholder file.")
                
                # Create directory if it doesn't exist
                config_dir.mkdir(exist_ok=True)
                
                # Create placeholder credentials file with instructions
                placeholder = {
                    "type": "service_account",
                    "project_id": "your-project-id",
                    "private_key_id": "your-private-key-id",
                    "private_key": "your-private-key",
                    "client_email": "your-client-email",
                    "client_id": "your-client-id",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_x509_cert_url": "your-cert-url"
                }
                
                with open(cred_file, "w") as f:
                    json.dump(placeholder, f, indent=2)
                
                logger.info(f"Created placeholder Firebase credentials at {cred_file}")
                logger.info("Please replace with actual Firebase credentials")
                return None, None
            
            cred = credentials.Certificate(str(cred_file))
        
        # Initialize Firebase
        firebase_app = firebase_admin.initialize_app(cred, {
            'databaseURL': os.getenv("FIREBASE_DATABASE_URL", "https://forest-fire-prediction-default-rtdb.firebaseio.com/")
        })
        
        # Get database references
        firebase_db = db.reference()
        firestore_db = firestore.client()
        
        firebase_initialized = True
        logger.info("Firebase initialized successfully")
        
        return firebase_db, firestore_db
        
    except Exception as e:
        logger.error(f"Error initializing Firebase: {e}")
        return None, None

def update_fire_data(fire_incidents: List[Dict[str, Any]], risk_zones: List[Dict[str, Any]]) -> bool:
    """
    Update Firebase with fire incidents and risk zones data
    
    Args:
        fire_incidents: List of fire incident data
        risk_zones: List of fire risk zone data
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    db_ref, _ = init_firebase()
    if not db_ref:
        logger.warning("Firebase not initialized. Can't update fire data.")
        return False
    
    try:
        # Update fire incidents
        incidents_ref = db_ref.child('fire_incidents')
        
        # Create a map of incidents by ID for efficient updates
        incidents_data = {}
        for incident in fire_incidents:
            incident_id = incident.get('id', None)
            if incident_id:
                incidents_data[str(incident_id)] = incident
        
        incidents_ref.update(incidents_data)
        
        # Update risk zones
        zones_ref = db_ref.child('risk_zones')
        
        # Create a map of zones by ID for efficient updates
        zones_data = {}
        for zone in risk_zones:
            zone_id = zone.get('id', None)
            if zone_id:
                zones_data[str(zone_id)] = zone
        
        zones_ref.update(zones_data)
        
        logger.info(f"Updated Firebase with {len(fire_incidents)} incidents and {len(risk_zones)} risk zones")
        return True
        
    except Exception as e:
        logger.error(f"Error updating Firebase: {e}")
        return False

def get_latest_fire_data() -> Dict[str, Any]:
    """
    Get the latest fire data from Firebase
    
    Returns:
        Dict containing fire incidents and risk zones
    """
    db_ref, _ = init_firebase()
    if not db_ref:
        logger.warning("Firebase not initialized. Can't get fire data.")
        return {"incidents": [], "risk_zones": []}
    
    try:
        # Get fire incidents
        incidents_ref = db_ref.child('fire_incidents')
        incidents_data = incidents_ref.get() or {}
        
        # Get risk zones
        zones_ref = db_ref.child('risk_zones')
        zones_data = zones_ref.get() or {}
        
        return {
            "incidents": list(incidents_data.values()),
            "risk_zones": list(zones_data.values())
        }
        
    except Exception as e:
        logger.error(f"Error getting data from Firebase: {e}")
        return {"incidents": [], "risk_zones": []} 