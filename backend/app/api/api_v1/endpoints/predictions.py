from datetime import datetime, timedelta
import random
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, field_validator

from app import schemas
from app.api import deps
from app.services import fire_risk_service, global_risk_service

router = APIRouter()


class FireRiskPredictionRequest(BaseModel):
    latitude: float
    longitude: float
    region_name: str | None = None

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, value: float) -> float:
        if not -90 <= value <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        return value

    @field_validator("longitude")
    @classmethod
    def normalize_longitude(cls, value: float) -> float:
        normalized = ((value + 180) % 360) - 180
        return 180.0 if normalized == -180 and value > 0 else normalized


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

    prediction_payload = global_risk_service.build_global_risk_zone_payload(
        latitude=request.latitude,
        longitude=request.longitude,
        region_name=request.region_name,
    )

    fire_risk_in = schemas.FireRiskZoneCreate(
        region_name=prediction_payload["region_name"],
        latitude=prediction_payload["latitude"],
        longitude=prediction_payload["longitude"],
        risk_level=prediction_payload["risk_level"],
        risk_category=prediction_payload["risk_category"],
        temperature=prediction_payload["temperature"],
        humidity=prediction_payload["humidity"],
        wind_speed=prediction_payload["wind_speed"],
        precipitation=prediction_payload["precipitation"],
        vegetation_density=prediction_payload["vegetation_density"],
        vegetation_type=prediction_payload["vegetation_type"],
        soil_moisture=prediction_payload["soil_moisture"],
        prediction_model=prediction_payload["prediction_model"],
        confidence_score=prediction_payload["confidence_score"],
    )
    zone = fire_risk_service.create_fire_risk_zone(fire_risk_in=fire_risk_in)

    if current_user.alert_threshold and zone["risk_level"] >= current_user.alert_threshold:
        fire_risk_service.create_alert(
            user_id=current_user.id,
            risk_zone_id=zone["id"],
            risk_level=zone["risk_level"],
            message=f"High fire risk detected in {zone['region_name']}. Risk level: {zone['risk_level']:.2f}",
        )

    return schemas.FireRiskZone.model_validate(zone)


class FireSpreadRequest(BaseModel):
    zone_id: str
    hours_ahead: int = 24

    @field_validator("hours_ahead")
    @classmethod
    def validate_hours_ahead(cls, value: int) -> int:
        if not 1 <= value <= 48:
            raise ValueError("hours_ahead must be between 1 and 48")
        return value


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

    lat = float(zone["latitude"])
    lng = ((float(zone["longitude"]) + 180) % 360) - 180
    spread_points = []
    current_time = datetime.utcnow()
    wind_speed = float(zone.get("wind_speed") or 0.0)
    wind_direction = random.uniform(0, 360)
    risk_level = float(zone["risk_level"])
    base_distance_km = min(1.8, 0.08 + (wind_speed * 0.025) + (risk_level * 0.65))

    for hour in range(1, request.hours_ahead + 1):
        import math

        angle_rad = math.radians(wind_direction)
        hour_distance_km = base_distance_km * (0.92 ** (hour - 1))
        direction_noise_deg = random.uniform(-12, 12)
        noisy_angle = math.radians(wind_direction + direction_noise_deg)
        delta_north_km = (hour_distance_km * math.cos(noisy_angle)) + random.uniform(-0.12, 0.12)
        delta_east_km = (hour_distance_km * math.sin(noisy_angle)) + random.uniform(-0.12, 0.12)

        lat += delta_north_km / 111.0
        lng += delta_east_km / max(1e-6, 111.0 * math.cos(math.radians(lat)))
        lng = ((lng + 180) % 360) - 180
        lat = max(-90.0, min(90.0, lat))

        spread_points.append(
            {
                "latitude": lat,
                "longitude": lng,
                "timestamp": (current_time + timedelta(hours=hour)).isoformat(),
                "risk_level": max(0.15, min(1.0, risk_level - (hour * 0.012) + random.uniform(-0.015, 0.015))),
            }
        )

    return {
        "original_zone": {
            "id": zone["id"],
            "latitude": float(zone["latitude"]),
            "longitude": ((float(zone["longitude"]) + 180) % 360) - 180,
            "risk_level": risk_level,
            "risk_category": zone["risk_category"],
        },
        "spread_points": spread_points,
        "max_spread_distance_km": sum(base_distance_km * (0.92 ** (hour - 1)) for hour in range(1, request.hours_ahead + 1)),
        "wind_direction_degrees": wind_direction,
    }
