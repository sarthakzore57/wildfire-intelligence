from typing import Any, Dict
from datetime import datetime, timedelta
import random # This is for demonstration, in production this would use actual ML models

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app import models, schemas
from app.api import deps
from app.services import fire_risk_service
from app.core.config import settings

router = APIRouter()


class FireRiskPredictionRequest(BaseModel):
    latitude: float
    longitude: float
    region_name: str | None = None


@router.post("/fire-risk/zones", response_model=schemas.FireRiskZone)
def predict_fire_risk_zone(
    *,
    db: Session = Depends(deps.get_db),
    request: FireRiskPredictionRequest = Body(...),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Predict fire risk for a location based on current conditions.
    This is a simplified example, in production this would call actual ML models.
    """
    # Check if we already have a recent prediction for this location
    existing_zone = fire_risk_service.get_fire_risk_zone_by_coords(
        db, latitude=request.latitude, longitude=request.longitude
    )
    
    # If we have a recent prediction (less than 1 hour old), return it
    if existing_zone and existing_zone.timestamp > datetime.utcnow() - timedelta(hours=1):
        return existing_zone
    
    # For demonstration purposes, we'll generate a random risk level
    # In a real system, this would come from an ML model
    risk_level = random.uniform(0, 1)
    
    # Determine risk category based on risk level
    risk_category = "Low"
    if risk_level > 0.7:
        risk_category = "High"
    elif risk_level > 0.4:
        risk_category = "Medium"
    
    # Generate random weather data for demonstration
    # In a real system, this would come from weather APIs or sensors
    temperature = random.uniform(15, 35)  # in Celsius
    humidity = random.uniform(20, 80)     # in percentage
    wind_speed = random.uniform(0, 25)    # in km/h
    precipitation = random.uniform(0, 10) # in mm
    
    # Vegetation data for demonstration
    vegetation_density = random.uniform(0, 1)
    vegetation_types = ["Forest", "Grassland", "Shrubland", "Mixed"]
    vegetation_type = random.choice(vegetation_types)
    soil_moisture = random.uniform(0, 1)
    
    # Create fire risk zone object
    fire_risk_in = schemas.FireRiskZoneCreate(
        region_name=request.region_name or f"Region near {request.latitude:.2f}, {request.longitude:.2f}",
        latitude=request.latitude,
        longitude=request.longitude,
        risk_level=risk_level,
        risk_category=risk_category,
        temperature=temperature,
        humidity=humidity,
        wind_speed=wind_speed,
        precipitation=precipitation,
        vegetation_density=vegetation_density,
        vegetation_type=vegetation_type,
        soil_moisture=soil_moisture,
        prediction_model="DemoRandomModel",  # In production, use actual model name
        confidence_score=random.uniform(0.7, 0.99),  # In production, use actual confidence score
    )
    
    # Save the prediction
    zone = fire_risk_service.create_fire_risk_zone(db, fire_risk_in=fire_risk_in)
    
    # Check if risk level exceeds user's threshold and create alert if needed
    # This would typically be done in a background task
    if current_user.alert_threshold and risk_level >= current_user.alert_threshold:
        create_alert_for_user(
            db=db,
            user_id=current_user.id,
            risk_zone_id=zone.id,
            risk_level=risk_level,
            message=f"High fire risk detected in {zone.region_name}. Risk level: {risk_level:.2f}"
        )
    
    return zone


# Define a Pydantic model for fire spread prediction request
class FireSpreadRequest(BaseModel):
    zone_id: int
    hours_ahead: int = 24


@router.post("/fire-spread", response_model=Dict)
def predict_fire_spread(
    *,
    db: Session = Depends(deps.get_db),
    request: FireSpreadRequest = Body(...),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Predict potential fire spread from a current fire risk zone.
    This is a simplified example, in production this would use fire spread models.
    """
    # Get the fire risk zone
    zone = fire_risk_service.get_fire_risk_zone(db, zone_id=request.zone_id)
    if not zone:
        raise HTTPException(
            status_code=404,
            detail=f"Fire risk zone with ID {request.zone_id} not found",
        )
    
    # For demonstration, generate random fire spread data
    # In production, this would use actual fire spread models
    
    # Starting point
    lat, lng = zone.latitude, zone.longitude
    
    # Generate spread points for each hour
    spread_points = []
    current_time = datetime.utcnow()
    
    # Adjust spread based on wind speed and direction (simplified)
    # In a real model, this would be much more complex
    wind_factor = zone.wind_speed / 10 if zone.wind_speed else 0.1
    
    # Random wind direction for demonstration
    wind_direction = random.uniform(0, 360)  # degrees
    
    # Higher risk means faster spread
    risk_factor = zone.risk_level * 2
    
    for hour in range(1, request.hours_ahead + 1):
        # Calculate new position based on wind and risk
        # This is a very simplified model for demonstration purposes
        import math
        angle_rad = math.radians(wind_direction)
        
        # Distance in degrees (very approximate)
        distance = wind_factor * risk_factor * 0.01
        
        # Update lat/lng based on wind direction
        lat += distance * math.cos(angle_rad)
        lng += distance * math.sin(angle_rad)
        
        # Add small random variation
        lat += random.uniform(-0.005, 0.005)
        lng += random.uniform(-0.005, 0.005)
        
        # Add to spread points
        spread_points.append({
            "latitude": lat,
            "longitude": lng,
            "timestamp": (current_time + timedelta(hours=hour)).isoformat(),
            "risk_level": min(1.0, zone.risk_level + (hour * 0.01)),  # Risk increases with time
        })
    
    return {
        "original_zone": {
            "id": zone.id,
            "latitude": zone.latitude,
            "longitude": zone.longitude,
            "risk_level": zone.risk_level,
            "risk_category": zone.risk_category,
        },
        "spread_points": spread_points,
        "max_spread_distance_km": wind_factor * risk_factor * request.hours_ahead,
        "wind_direction_degrees": wind_direction,
    }


def create_alert_for_user(
    db: Session, user_id: int, risk_zone_id: int, risk_level: float, message: str
) -> models.Alert:
    """
    Create an alert for a user based on fire risk prediction.
    """
    alert = models.Alert(
        user_id=user_id,
        risk_zone_id=risk_zone_id,
        risk_level=risk_level,
        message=message,
        is_read=False,
        is_sent_email=False,
        is_sent_sms=False,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    # In a production system, we would trigger email/SMS notifications here
    
    return alert 
