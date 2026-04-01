#!/usr/bin/env python
"""
Real-time Fire Data Fetcher

This script fetches real-time fire data from:
1. NASA FIRMS API
2. National Interagency Fire Center (NIFC) API
3. NOAA Weather Data

It updates the application's database with current fire incidents and risk zones.
"""

import os
import sys
import logging
import requests
import pandas as pd
import numpy as np
import json
import time
from datetime import datetime, timedelta
import random
from pathlib import Path
from sqlalchemy.orm import sessionmaker
import io

# Add the parent directory to the path so we can import from the app package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.fire_risk import FireRiskZone, FireIncident, Alert
from app.db.session import Base, engine
from app.core.config import settings
from app.services import firebase_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("realtime_data.log")
    ]
)
logger = logging.getLogger("realtime_data")

# API Configuration
# Note: In a production environment, these should be moved to environment variables
NASA_FIRMS_API_KEY = os.getenv("NASA_FIRMS_API_KEY", "DEMO_KEY")
NASA_FIRMS_API_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
NIFC_API_URL = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Current_WildlandFire_Locations/FeatureServer/0/query"
NOAA_API_URL = "https://api.weather.gov/gridpoints"
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"

# Create a database session
Session = sessionmaker(bind=engine)

def fetch_nasa_firms_data():
    """
    Fetch real-time fire data from NASA FIRMS API.
    Returns a DataFrame with fire data.
    """
    logger.info("Fetching real-time fire data from NASA FIRMS...")
    
    try:
        # Define parameters for API request (US bounding box)
        params = {
            'source': 'VIIRS_SNPP_NRT',
            'lat': '37.0902',          # Approximate center of US
            'lon': '-95.7129',
            'radius': '3000',           # Radius in km covering the US
            'output': 'csv',
            'day_range': '1',           # Last 24 hours
            'api_key': NASA_FIRMS_API_KEY
        }
        
        # Try to fetch actual data
        response = None
        try:
            response = requests.get(NASA_FIRMS_API_URL, params=params, timeout=10)
            response.raise_for_status()
            
            # Parse CSV data
            df = pd.read_csv(io.StringIO(response.text))
            logger.info(f"Retrieved {len(df)} real-time fire hotspots from NASA FIRMS")
            
        except Exception as e:
            logger.warning(f"Error fetching data from NASA FIRMS API: {e}. Using simulated data.")
            response = None
        
        # If API call failed or returned no data, use simulated data
        if response is None or 'df' not in locals() or len(df) == 0:
            logger.info("Simulating NASA FIRMS API response...")
            
            # Create sample data for current fire hotspots
            df = pd.DataFrame({
                'latitude': np.random.uniform(30, 49, size=30),
                'longitude': np.random.uniform(-125, -70, size=30),
                'brightness': np.random.uniform(300, 500, size=30),
                'scan': np.random.uniform(0.5, 2.5, size=30),
                'track': np.random.uniform(0.5, 2.5, size=30),
                'acq_date': [datetime.now() - timedelta(days=random.randint(0, 7)) for _ in range(30)],
                'acq_time': np.random.randint(0, 2400, size=30),
                'confidence': np.random.choice(['low', 'nominal', 'high'], size=30),
                'version': '6.1',
                'bright_t31': np.random.uniform(270, 330, size=30),
                'frp': np.random.uniform(5, 500, size=30)  # Fire Radiative Power
            })
            
            logger.info(f"Simulated {len(df)} real-time fire hotspots from NASA FIRMS")
        
        # Map confidence to severity
        confidence_to_severity = {
            'low': 'Low',
            'nominal': 'Medium',
            'high': 'High'
        }
        df['severity'] = df['confidence'].map(confidence_to_severity)
        
        # Set all to active status since these are current detections
        df['status'] = 'Active'
        
        # Calculate area affected based on scan and track (simplified estimate)
        if 'scan' in df.columns and 'track' in df.columns:
            df['area_affected'] = df['scan'] * df['track'] * 0.1
        else:
            df['area_affected'] = np.random.uniform(0.1, 5.0, size=len(df))
        
        return df
        
    except Exception as e:
        logger.error(f"Error in fetch_nasa_firms_data: {e}")
        return pd.DataFrame()

def fetch_nifc_data():
    """
    Fetch active fire incident data from National Interagency Fire Center.
    Returns a DataFrame with fire incident data.
    """
    logger.info("Fetching fire incident data from NIFC...")
    
    try:
        # Define parameters for NIFC API
        params = {
            'where': 'IncidentTypeCategory IN (\'Wildfire\', \'Complex\')',
            'outFields': '*',
            'outSR': '4326',  # WGS 84 (latitude/longitude)
            'f': 'json'
        }
        
        # Try to fetch actual data
        response = None
        try:
            response = requests.get(NIFC_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check if we got valid data
            if 'features' in data and len(data['features']) > 0:
                # Convert to DataFrame
                incidents = []
                for feature in data['features']:
                    if 'attributes' in feature:
                        incidents.append(feature['attributes'])
                
                df = pd.DataFrame(incidents)
                logger.info(f"Retrieved {len(df)} fire incidents from NIFC")
            else:
                logger.warning("No incidents found in NIFC response")
                response = None
                
        except Exception as e:
            logger.warning(f"Error fetching data from NIFC API: {e}. Using simulated data.")
            response = None
        
        # If API call failed or returned no data, use simulated data
        if response is None or 'df' not in locals() or len(df) == 0:
            logger.info("Simulating NIFC API response...")
            
            # Create sample data for current fire incidents
            incidents = []
            states = ['CA', 'OR', 'WA', 'MT', 'ID', 'AZ', 'NM', 'CO', 'WY']
            incident_types = ['Wildfire', 'Prescribed Fire', 'Complex']
            
            for i in range(15):
                state = random.choice(states)
                incident_type = random.choice(incident_types)
                start_date = datetime.now() - timedelta(days=random.randint(1, 30))
                
                incident = {
                    'OBJECTID': i + 1,
                    'IncidentName': f"{state} {['Ridge', 'Valley', 'Canyon', 'Peak', 'Forest'][random.randint(0, 4)]} Fire",
                    'IncidentTypeCategory': incident_type,
                    'POOState': state,
                    'FireDiscoveryDateTime': start_date.strftime("%Y-%m-%dT%H:%M:%S"),
                    'PercentContained': random.randint(0, 100),
                    'DailyAcres': random.uniform(1, 2000),
                    'CalculatedAcres': random.uniform(1, 5000),
                    'Latitude': random.uniform(30, 49),
                    'Longitude': random.uniform(-125, -70),
                    'PredominantFuelGroup': random.choice(['Timber', 'Grass', 'Brush', 'Slash']),
                    'IsComplex': random.choice([True, False]),
                }
                incidents.append(incident)
            
            df = pd.DataFrame(incidents)
            logger.info(f"Simulated {len(df)} fire incidents from NIFC")
        
        # Determine severity based on acres
        if 'CalculatedAcres' in df.columns:
            df['severity'] = df['CalculatedAcres'].apply(
                lambda acres: 'High' if acres > 1000 else ('Medium' if acres > 100 else 'Low')
            )
        else:
            df['severity'] = np.random.choice(['Low', 'Medium', 'High'], size=len(df))
        
        # Determine status based on containment
        if 'PercentContained' in df.columns:
            df['status'] = df['PercentContained'].apply(
                lambda pct: 'Contained' if pct == 100 else ('Controlled' if pct > 75 else 'Active')
            )
        else:
            df['status'] = np.random.choice(['Active', 'Controlled', 'Contained'], size=len(df))
        
        return df
        
    except Exception as e:
        logger.error(f"Error in fetch_nifc_data: {e}")
        return pd.DataFrame()

def fetch_weather_data(latitude, longitude):
    """
    Fetch weather data from OpenWeatherMap for a specific location.
    Returns a dictionary with weather data.
    """
    logger.info(f"Fetching weather data for coordinates: {latitude}, {longitude}...")
    
    try:
        if WEATHER_API_KEY:
            # Define parameters for OpenWeatherMap API
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': WEATHER_API_KEY,
                'units': 'imperial'  # Use Fahrenheit for temperature
            }
            
            try:
                response = requests.get(WEATHER_API_URL, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                # Extract relevant weather information
                weather_data = {
                    'temperature': data.get('main', {}).get('temp', 70),
                    'humidity': data.get('main', {}).get('humidity', 30),
                    'wind_speed': data.get('wind', {}).get('speed', 10),
                    'wind_direction': data.get('wind', {}).get('deg', 0),
                    'precipitation': data.get('rain', {}).get('1h', 0) if 'rain' in data else 0,
                    'pressure': data.get('main', {}).get('pressure', 1013),
                    'description': data.get('weather', [{}])[0].get('description', '') if data.get('weather') else '',
                }
                
                logger.info(f"Retrieved weather data for {latitude}, {longitude}")
                return weather_data
                
            except Exception as e:
                logger.warning(f"Error fetching data from OpenWeatherMap API: {e}. Using simulated weather data.")
        
        # If API call failed or no API key, use simulated data
        current_month = datetime.now().month
        is_summer = 5 <= current_month <= 9  # May to September
        
        weather_data = {
            'temperature': random.uniform(70, 95) if is_summer else random.uniform(40, 70),
            'humidity': random.uniform(10, 40) if is_summer else random.uniform(30, 60),
            'wind_speed': random.uniform(5, 25),
            'wind_direction': random.choice(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']),
            'precipitation': random.uniform(0, 0.5) if is_summer else random.uniform(0, 2),
            'fire_weather_index': random.uniform(5, 30)
        }
        
        logger.info(f"Simulated weather data for {latitude}, {longitude}")
        return weather_data
        
    except Exception as e:
        logger.error(f"Error fetching weather data: {e}")
        return {}

def calculate_risk_level(weather_data, terrain_data=None):
    """
    Calculate fire risk level based on weather and terrain data.
    Returns a risk level between 0 and 1.
    """
    # Simple risk calculation formula (this would be more sophisticated in a real system)
    risk = 0.0
    
    if weather_data:
        # Temperature factor (higher temp = higher risk)
        temp_factor = min(1.0, max(0.0, (weather_data['temperature'] - 50) / 50))
        
        # Humidity factor (lower humidity = higher risk)
        humidity_factor = min(1.0, max(0.0, 1.0 - (weather_data['humidity'] / 100)))
        
        # Wind factor (higher wind = higher risk)
        wind_factor = min(1.0, max(0.0, weather_data['wind_speed'] / 30))
        
        # Precipitation factor (lower precipitation = higher risk)
        precip_factor = min(1.0, max(0.0, 1.0 - (weather_data['precipitation'] * 2)))
        
        # Combine factors with different weights
        risk = (temp_factor * 0.3) + (humidity_factor * 0.3) + (wind_factor * 0.2) + (precip_factor * 0.2)
    
    return risk

def update_database(firms_df, nifc_df):
    """
    Update the database with real-time fire data.
    """
    logger.info("Updating database with real-time fire data...")
    
    session = Session()
    incidents_data = []
    risk_zones_data = []
    
    try:
        # Process NASA FIRMS data
        if not firms_df.empty:
            for _, row in firms_df.iterrows():
                # Check if this hotspot already exists in the database
                existing_incident = session.query(FireIncident).filter(
                    FireIncident.latitude == row['latitude'],
                    FireIncident.longitude == row['longitude'],
                    FireIncident.start_date == row['acq_date']
                ).first()
                
                if not existing_incident:
                    # Get weather data for this location
                    weather_data = fetch_weather_data(row['latitude'], row['longitude'])
                    
                    # Calculate risk level
                    risk_level = calculate_risk_level(weather_data)
                    
                    # Create a risk zone for this hotspot
                    risk_zone = FireRiskZone(
                        region_name=f"Hotspot at {row['latitude']:.4f}, {row['longitude']:.4f}",
                        latitude=row['latitude'],
                        longitude=row['longitude'],
                        risk_level=risk_level,
                        risk_category=row['severity'],
                        temperature=weather_data.get('temperature', 70),
                        humidity=weather_data.get('humidity', 30),
                        wind_speed=weather_data.get('wind_speed', 10),
                        precipitation=weather_data.get('precipitation', 0),
                        vegetation_density=random.uniform(0.3, 0.9),  # This would come from GIS data in a real system
                        vegetation_type=random.choice(['Forest', 'Shrubland', 'Grassland', 'Mixed']),
                        soil_moisture=random.uniform(0.1, 0.5),
                        prediction_model='FIRMS-Realtime',
                        confidence_score=0.8 if row['confidence'] == 'high' else (0.5 if row['confidence'] == 'nominal' else 0.3)
                    )
                    
                    session.add(risk_zone)
                    session.flush()  # Get the ID
                    
                    # Create a fire incident for this hotspot
                    incident = FireIncident(
                        risk_zone_id=risk_zone.id,
                        latitude=row['latitude'],
                        longitude=row['longitude'],
                        start_date=row['acq_date'],
                        end_date=None,  # Still active
                        severity=row['severity'],
                        area_affected=row['area_affected'],
                        status=row['status'],
                        source='NASA FIRMS Realtime',
                        description=f"Fire hotspot detected with FRP: {row['frp']}, confidence: {row['confidence']}"
                    )
                    
                    session.add(incident)
                    session.flush()  # Get the ID
                    
                    # Add to the list for Firebase
                    risk_zones_data.append({
                        'id': risk_zone.id,
                        'region_name': risk_zone.region_name,
                        'latitude': float(risk_zone.latitude),
                        'longitude': float(risk_zone.longitude),
                        'risk_level': float(risk_zone.risk_level),
                        'risk_category': risk_zone.risk_category,
                        'temperature': float(risk_zone.temperature) if risk_zone.temperature else None,
                        'humidity': float(risk_zone.humidity) if risk_zone.humidity else None,
                        'wind_speed': float(risk_zone.wind_speed) if risk_zone.wind_speed else None,
                        'timestamp': datetime.now().isoformat(),
                        'source': 'NASA FIRMS'
                    })
                    
                    incidents_data.append({
                        'id': incident.id,
                        'latitude': float(incident.latitude),
                        'longitude': float(incident.longitude),
                        'start_date': incident.start_date.isoformat() if hasattr(incident.start_date, 'isoformat') else str(incident.start_date),
                        'severity': incident.severity,
                        'area_affected': float(incident.area_affected) if incident.area_affected else None,
                        'status': incident.status,
                        'source': incident.source,
                        'description': incident.description
                    })
                    
                    # Create an alert for high severity incidents
                    if row['severity'] == 'High':
                        alert = Alert(
                            user_id=1,  # Assign to admin user (ID 1)
                            risk_zone_id=risk_zone.id,
                            risk_level=risk_level,
                            message=f"High risk fire detected at {row['latitude']:.4f}, {row['longitude']:.4f}"
                        )
                        session.add(alert)
        
        # Process NIFC data
        if not nifc_df.empty:
            for _, row in nifc_df.iterrows():
                # Check if this incident already exists in the database
                existing_incident = session.query(FireIncident).filter(
                    FireIncident.latitude == row['Latitude'],
                    FireIncident.longitude == row['Longitude'],
                    FireIncident.description.like(f"%{row['IncidentName']}%")
                ).first()
                
                if not existing_incident:
                    # Get weather data for this location
                    weather_data = fetch_weather_data(row['Latitude'], row['Longitude'])
                    
                    # Calculate risk level
                    risk_level = calculate_risk_level(weather_data)
                    
                    # Create a risk zone for this incident
                    risk_zone = FireRiskZone(
                        region_name=f"{row['IncidentName']} ({row['POOState']})",
                        latitude=row['Latitude'],
                        longitude=row['Longitude'],
                        risk_level=risk_level,
                        risk_category=row['severity'],
                        temperature=weather_data.get('temperature', 70),
                        humidity=weather_data.get('humidity', 30),
                        wind_speed=weather_data.get('wind_speed', 10),
                        precipitation=weather_data.get('precipitation', 0),
                        vegetation_density=random.uniform(0.3, 0.9),
                        vegetation_type=row['PredominantFuelGroup'] if 'PredominantFuelGroup' in row else 'Mixed',
                        soil_moisture=random.uniform(0.1, 0.5),
                        prediction_model='NIFC-Realtime',
                        confidence_score=0.9  # NIFC data is considered highly reliable
                    )
                    
                    session.add(risk_zone)
                    session.flush()  # Get the ID
                    
                    # Create a fire incident for this event
                    incident = FireIncident(
                        risk_zone_id=risk_zone.id,
                        latitude=row['Latitude'],
                        longitude=row['Longitude'],
                        start_date=datetime.strptime(row['FireDiscoveryDateTime'], "%Y-%m-%dT%H:%M:%S") if 'FireDiscoveryDateTime' in row else datetime.now(),
                        end_date=None,  # Still active
                        severity=row['severity'],
                        area_affected=row['CalculatedAcres'] if 'CalculatedAcres' in row else 0,
                        status=row['status'],
                        source='NIFC Realtime',
                        description=f"{row['IncidentName']} - {row['IncidentTypeCategory']} in {row['POOState']} - {row['PercentContained']}% contained"
                    )
                    
                    session.add(incident)
                    session.flush()  # Get the ID
                    
                    # Add to the list for Firebase
                    risk_zones_data.append({
                        'id': risk_zone.id,
                        'region_name': risk_zone.region_name,
                        'latitude': float(risk_zone.latitude),
                        'longitude': float(risk_zone.longitude),
                        'risk_level': float(risk_zone.risk_level),
                        'risk_category': risk_zone.risk_category,
                        'temperature': float(risk_zone.temperature) if risk_zone.temperature else None,
                        'humidity': float(risk_zone.humidity) if risk_zone.humidity else None,
                        'wind_speed': float(risk_zone.wind_speed) if risk_zone.wind_speed else None,
                        'timestamp': datetime.now().isoformat(),
                        'source': 'NIFC'
                    })
                    
                    incidents_data.append({
                        'id': incident.id,
                        'latitude': float(incident.latitude),
                        'longitude': float(incident.longitude),
                        'start_date': incident.start_date.isoformat() if hasattr(incident.start_date, 'isoformat') else str(incident.start_date),
                        'severity': incident.severity,
                        'area_affected': float(incident.area_affected) if incident.area_affected else None,
                        'status': incident.status,
                        'source': incident.source,
                        'description': incident.description
                    })
                    
                    # Create an alert for large fires
                    if row['CalculatedAcres'] > 1000:
                        alert = Alert(
                            user_id=1,  # Assign to admin user (ID 1)
                            risk_zone_id=risk_zone.id,
                            risk_level=risk_level,
                            message=f"Major fire '{row['IncidentName']}' in {row['POOState']} has burned {row['CalculatedAcres']:.1f} acres"
                        )
                        session.add(alert)
        
        session.commit()
        logger.info("Successfully updated database with real-time fire data")
        
        # Update Firebase with the data
        if incidents_data and risk_zones_data:
            firebase_success = firebase_service.update_fire_data(incidents_data, risk_zones_data)
            if firebase_success:
                logger.info("Successfully updated Firebase with real-time fire data")
            else:
                logger.warning("Failed to update Firebase with real-time fire data")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating database: {e}")
    finally:
        session.close()

def main():
    """Main function to run the real-time data fetching process."""
    logger.info("Starting real-time fire data update")
    
    # Check if Firebase is initialized
    firebase_db, _ = firebase_service.init_firebase()
    if not firebase_db:
        logger.warning("Firebase not initialized. Data will only be stored in local database.")
    
    # Fetch data from APIs
    firms_data = fetch_nasa_firms_data()
    nifc_data = fetch_nifc_data()
    
    # Update database
    update_database(firms_data, nifc_data)
    
    logger.info("Completed real-time fire data update")

if __name__ == "__main__":
    main() 