#!/usr/bin/env python
"""
Debug API Endpoints

This script checks if all the required API endpoints are working correctly.
"""

import sys
import requests
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("api_debug")

# API Configuration
BASE_URL = "http://localhost:8000/api/v1"

def check_user_info():
    """Check if user info API is working"""
    logger.info("Checking user info API...")
    
    # Get auth token - Update with correct credentials
    auth_data = {
        "username": "admin@forestfire.com",
        "password": "adminpassword"
    }
    
    try:
        # Login to get token - Fix the URL to use the correct endpoint
        auth_response = requests.post(
            f"{BASE_URL}/auth/login/access-token", 
            data=auth_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        auth_response.raise_for_status()
        token = auth_response.json().get("access_token")
        
        if not token:
            logger.error("Failed to get authentication token")
            return False
        
        # Get user info
        headers = {"Authorization": f"Bearer {token}"}
        user_response = requests.get(f"{BASE_URL}/users/me", headers=headers)
        user_response.raise_for_status()
        user_data = user_response.json()
        
        logger.info(f"✅ User info API working. Current user: {user_data.get('email')}")
        return True
        
    except Exception as e:
        logger.error(f"❌ User info API error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_details = e.response.json()
                logger.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                logger.error(f"Status code: {e.response.status_code}, Response: {e.response.text}")
        return False

def check_fire_incidents():
    """Check if fire incidents API is working"""
    logger.info("Checking fire incidents API...")
    
    # Get auth token - Update with correct credentials
    auth_data = {
        "username": "admin@forestfire.com",
        "password": "adminpassword"
    }
    
    try:
        # Login to get token
        auth_response = requests.post(
            f"{BASE_URL}/auth/login/access-token", 
            data=auth_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        auth_response.raise_for_status()
        token = auth_response.json().get("access_token")
        
        if not token:
            logger.error("Failed to get authentication token")
            return False
        
        # Get fire incidents
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/fire-incidents/", headers=headers)
        response.raise_for_status()
        incidents = response.json()
        
        logger.info(f"✅ Fire incidents API working. Found {len(incidents)} incidents.")
        return True
        
    except Exception as e:
        logger.error(f"❌ Fire incidents API error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_details = e.response.json()
                logger.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                logger.error(f"Status code: {e.response.status_code}, Response: {e.response.text}")
        return False

def check_fire_risk_zones():
    """Check if fire risk zones API is working"""
    logger.info("Checking fire risk zones API...")
    
    # Get auth token - Update with correct credentials
    auth_data = {
        "username": "admin@forestfire.com",
        "password": "adminpassword"
    }
    
    try:
        # Login to get token
        auth_response = requests.post(
            f"{BASE_URL}/auth/login/access-token", 
            data=auth_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        auth_response.raise_for_status()
        token = auth_response.json().get("access_token")
        
        if not token:
            logger.error("Failed to get authentication token")
            return False
        
        # Get fire risk zones
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/fire-risk/zones", headers=headers)
        response.raise_for_status()
        zones = response.json()
        
        logger.info(f"✅ Fire risk zones API working. Found {len(zones)} zones.")
        return True
        
    except Exception as e:
        logger.error(f"❌ Fire risk zones API error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_details = e.response.json()
                logger.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                logger.error(f"Status code: {e.response.status_code}, Response: {e.response.text}")
        return False

def check_fire_spread_prediction():
    """Check if fire spread prediction API is working"""
    logger.info("Checking fire spread prediction API...")
    
    # Get auth token - Update with correct credentials
    auth_data = {
        "username": "admin@forestfire.com",
        "password": "adminpassword"
    }
    
    try:
        # Login to get token
        auth_response = requests.post(
            f"{BASE_URL}/auth/login/access-token", 
            data=auth_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        auth_response.raise_for_status()
        token = auth_response.json().get("access_token")
        
        if not token:
            logger.error("Failed to get authentication token")
            return False
        
        # First get a fire risk zone to use for prediction
        headers = {"Authorization": f"Bearer {token}"}
        zones_response = requests.get(f"{BASE_URL}/fire-risk/zones", headers=headers)
        zones_response.raise_for_status()
        zones = zones_response.json()
        
        if not zones:
            logger.error("No fire risk zones found for testing fire spread prediction")
            return False
        
        zone_id = zones[0]['id']
        
        # Test fire spread prediction
        prediction_data = {
            "zone_id": zone_id
        }
        
        response = requests.post(
            f"{BASE_URL}/predictions/fire-spread", 
            headers=headers,
            json=prediction_data
        )
        response.raise_for_status()
        prediction = response.json()
        
        logger.info(f"✅ Fire spread prediction API working. Prediction details:")
        logger.info(f"   - Original zone: {prediction.get('original_zone', {}).get('region_name')}")
        logger.info(f"   - Spread points: {len(prediction.get('spread_points', []))}")
        logger.info(f"   - Max spread: {prediction.get('max_spread_distance')} km")
        logger.info(f"   - Wind direction: {prediction.get('wind_direction')}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Fire spread prediction API error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_details = e.response.json()
                logger.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                logger.error(f"Status code: {e.response.status_code}, Response: {e.response.text}")
        return False

def main():
    """Run all API checks and summarize results"""
    logger.info("Starting API debug checks...")
    
    results = {
        "user_info": check_user_info(),
        "fire_incidents": check_fire_incidents(),
        "fire_risk_zones": check_fire_risk_zones(),
        "fire_spread_prediction": check_fire_spread_prediction()
    }
    
    logger.info("\nAPI Debug Results Summary:")
    logger.info("-------------------------")
    for api_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{api_name}: {status}")
    
    all_passed = all(results.values())
    if all_passed:
        logger.info("\n🎉 All API endpoints are working correctly!")
    else:
        failed_apis = [api for api, success in results.items() if not success]
        logger.warning(f"\n⚠️ Some API endpoints are not working: {', '.join(failed_apis)}")
    
    return all_passed

if __name__ == "__main__":
    sys.exit(main()) 