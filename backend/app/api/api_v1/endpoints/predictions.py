from datetime import datetime, timedelta
from typing import Any
import random

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel

from app import schemas
from app.api import deps
from app.services import fire_risk_service

router = APIRouter()


class FireRiskPredictionRequest(BaseModel):
    latitude: float
    longitude: float
    region_name: str | None = None


@router.post("/fire-risk/zones", response_model=schemas.FireRiskZone)
def predict_fire_risk_zone(
    *,
    request: FireRiskPredictionRequest = Body(...),
    current_user: schemas.User = Depends(deps.get_current_user),
) -> Any:
    existing_zone = fire_risk_service.get_fire_risk_zone_by_coords(
        latitude=request.latitude, longitude=request.longitude
    )
    if existing_zone and existing_zone["timestamp"] > datetime.utcnow() - timedelta(hours=1):
        return schemas.FireRiskZone.model_validate(existing_zone)

    risk_level = random.uniform(0, 1)
    risk_category = "Low"
    if risk_level > 0.7:
        risk_category = "High"
    elif risk_level > 0.4:
        risk_category = "Medium"

    fire_risk_in = schemas.FireRiskZoneCreate(
        region_name=request.region_name or f"Region near {request.latitude:.2f}, {request.longitude:.2f}",
        latitude=request.latitude,
        longitude=request.longitude,
        risk_level=risk_level,
        risk_category=risk_category,
        temperature=random.uniform(15, 35),
        humidity=random.uniform(20, 80),
        wind_speed=random.uniform(0, 25),
        precipitation=random.uniform(0, 10),
        vegetation_density=random.uniform(0, 1),
        vegetation_type=random.choice(["Forest", "Grassland", "Shrubland", "Mixed"]),
        soil_moisture=random.uniform(0, 1),
        prediction_model="DemoRandomModel",
        confidence_score=random.uniform(0.7, 0.99),
    )
    zone = fire_risk_service.create_fire_risk_zone(fire_risk_in=fire_risk_in)

    if current_user.alert_threshold and risk_level >= current_user.alert_threshold:
        fire_risk_service.create_alert(
            user_id=current_user.id,
            risk_zone_id=zone["id"],
            risk_level=risk_level,
            message=f"High fire risk detected in {zone['region_name']}. Risk level: {risk_level:.2f}",
        )

    return schemas.FireRiskZone.model_validate(zone)


class FireSpreadRequest(BaseModel):
    zone_id: str
    hours_ahead: int = 24


@router.post("/fire-spread", response_model=dict)
def predict_fire_spread(
    *,
    request: FireSpreadRequest = Body(...),
    current_user: schemas.User = Depends(deps.get_current_user),
) -> Any:
    zone = fire_risk_service.get_fire_risk_zone(zone_id=request.zone_id)
    if not zone:
        raise HTTPException(
            status_code=404,
            detail=f"Fire risk zone with ID {request.zone_id} not found",
        )

    lat, lng = zone["latitude"], zone["longitude"]
    spread_points = []
    current_time = datetime.utcnow()
    wind_factor = zone.get("wind_speed", 1) / 10 if zone.get("wind_speed") else 0.1
    wind_direction = random.uniform(0, 360)
    risk_factor = zone["risk_level"] * 2

    for hour in range(1, request.hours_ahead + 1):
        import math

        angle_rad = math.radians(wind_direction)
        distance = wind_factor * risk_factor * 0.01
        lat += distance * math.cos(angle_rad) + random.uniform(-0.005, 0.005)
        lng += distance * math.sin(angle_rad) + random.uniform(-0.005, 0.005)
        spread_points.append(
            {
                "latitude": lat,
                "longitude": lng,
                "timestamp": (current_time + timedelta(hours=hour)).isoformat(),
                "risk_level": min(1.0, zone["risk_level"] + (hour * 0.01)),
            }
        )

    return {
        "original_zone": {
            "id": zone["id"],
            "latitude": zone["latitude"],
            "longitude": zone["longitude"],
            "risk_level": zone["risk_level"],
            "risk_category": zone["risk_category"],
        },
        "spread_points": spread_points,
        "max_spread_distance_km": wind_factor * risk_factor * request.hours_ahead,
        "wind_direction_degrees": wind_direction,
    }
