from __future__ import annotations

import json
import logging
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

try:
    import joblib
except ImportError:  # pragma: no cover - handled at runtime
    joblib = None

try:
    import pandas as pd
except ImportError:  # pragma: no cover - handled at runtime
    pd = None


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
EONET_EVENTS_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"
MODEL_ARTIFACT_PATH = Path(__file__).resolve().parent.parent / "models" / "trained" / "global_fire_risk_model.joblib"
MODEL_METADATA_PATH = Path(__file__).resolve().parent.parent / "models" / "trained" / "global_fire_risk_model.meta.json"
MODEL_REGISTRY_PATH = Path(__file__).resolve().parent.parent / "models" / "trained" / "model_registry.json"
DEFAULT_MODEL_FEATURES = [
    "latitude",
    "longitude",
    "month",
    "temperature_c",
    "humidity_pct",
    "wind_speed_kph",
    "precipitation_mm",
    "nearest_open_wildfire_km",
]

logger = logging.getLogger(__name__)

_MODEL_LOADED = False
_MODEL = None
_MODEL_FEATURES = DEFAULT_MODEL_FEATURES.copy()


def _clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_km * c


def _extract_point_from_geometry(geometry_item: dict[str, Any]) -> tuple[float, float] | None:
    coordinates = geometry_item.get("coordinates")
    if not coordinates:
        return None

    if (
        isinstance(coordinates, list)
        and len(coordinates) == 2
        and all(isinstance(v, (int, float)) for v in coordinates)
    ):
        lon, lat = coordinates
        return float(lat), float(lon)

    if isinstance(coordinates, list) and coordinates and isinstance(coordinates[0], list):
        first = coordinates[0]
        if len(first) == 2 and all(isinstance(v, (int, float)) for v in first):
            lon, lat = first
            return float(lat), float(lon)
        if first and isinstance(first[0], list):
            first_nested = first[0]
            if len(first_nested) == 2 and all(isinstance(v, (int, float)) for v in first_nested):
                lon, lat = first_nested
                return float(lat), float(lon)
    return None


def _fetch_weather(latitude: float, longitude: float) -> dict[str, float] | None:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
        "timezone": "auto",
    }
    try:
        response = requests.get(OPEN_METEO_URL, params=params, timeout=12)
        response.raise_for_status()
        current = response.json().get("current", {})
        if not current:
            return None
        return {
            "temperature_c": float(current.get("temperature_2m", 0.0)),
            "humidity_pct": float(current.get("relative_humidity_2m", 0.0)),
            "wind_speed_kph": float(current.get("wind_speed_10m", 0.0)),
            "precipitation_mm": float(current.get("precipitation", 0.0)),
        }
    except Exception:
        return None


def _deterministic_weather_fallback(latitude: float, longitude: float) -> dict[str, float]:
    lat_effect = max(0.0, 35.0 - abs(latitude) * 0.45)
    lon_variation = (abs(longitude) % 10) / 10
    temperature_c = 10 + lat_effect + lon_variation * 4
    humidity_pct = 35 + (abs(latitude) % 20)
    wind_speed_kph = 8 + (abs(longitude) % 15)
    precipitation_mm = max(0.0, 2.0 - (abs(latitude) % 5) * 0.2)
    return {
        "temperature_c": temperature_c,
        "humidity_pct": humidity_pct,
        "wind_speed_kph": wind_speed_kph,
        "precipitation_mm": precipitation_mm,
    }


def _fetch_open_wildfire_distances(latitude: float, longitude: float) -> list[float] | None:
    params = {"status": "open", "category": "wildfires", "limit": 200}
    try:
        response = requests.get(EONET_EVENTS_URL, params=params, timeout=12)
        response.raise_for_status()
        events = response.json().get("events", [])
    except Exception:
        return None

    distances: list[float] = []
    for event in events:
        geometries = event.get("geometry", [])
        for item in geometries:
            point = _extract_point_from_geometry(item)
            if point is None:
                continue
            event_lat, event_lon = point
            distances.append(_haversine_km(latitude, longitude, event_lat, event_lon))
    return distances


def _wildfire_proximity_score(min_distance_km: float | None) -> float:
    if min_distance_km is None:
        return 0.0
    if min_distance_km <= 25:
        return 1.0
    if min_distance_km <= 100:
        return 0.75
    if min_distance_km <= 300:
        return 0.5
    if min_distance_km <= 800:
        return 0.25
    return 0.1


def _risk_category(risk_level: float) -> str:
    if risk_level >= 0.7:
        return "High"
    if risk_level >= 0.4:
        return "Medium"
    return "Low"


def _load_model_if_available() -> None:
    global _MODEL_LOADED, _MODEL, _MODEL_FEATURES
    if _MODEL_LOADED:
        return
    _MODEL_LOADED = True

    if joblib is None:
        logger.warning("joblib is not installed; trained model inference disabled.")
        return
    model_path = MODEL_ARTIFACT_PATH
    metadata_path = MODEL_METADATA_PATH

    if MODEL_REGISTRY_PATH.exists():
        try:
            registry = json.loads(MODEL_REGISTRY_PATH.read_text(encoding="utf-8"))
            latest = registry.get("latest", {})
            registered_model = latest.get("model_path")
            registered_meta = latest.get("metadata_path")
            if isinstance(registered_model, str) and registered_model:
                model_path = Path(registered_model)
            if isinstance(registered_meta, str) and registered_meta:
                metadata_path = Path(registered_meta)
        except Exception as exc:
            logger.warning("Model registry read failed, using default model path: %s", exc)

    if not model_path.exists():
        return

    try:
        _MODEL = joblib.load(model_path)
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            feature_columns = metadata.get("feature_columns")
            if isinstance(feature_columns, list) and all(isinstance(col, str) for col in feature_columns):
                _MODEL_FEATURES = feature_columns
    except Exception as exc:
        logger.error("Failed to load trained model artifact: %s", exc)
        _MODEL = None


def _predict_with_trained_model(feature_map: dict[str, float]) -> float | None:
    _load_model_if_available()
    if _MODEL is None:
        return None
    try:
        values = [float(feature_map.get(name, 0.0)) for name in _MODEL_FEATURES]
        if pd is not None:
            frame = pd.DataFrame([values], columns=_MODEL_FEATURES)
            prediction = float(_MODEL.predict(frame)[0])
        else:
            prediction = float(_MODEL.predict([values])[0])
        return _clamp(prediction)
    except Exception as exc:
        logger.error("Trained model inference failed: %s", exc)
        return None


def build_global_risk_zone_payload(latitude: float, longitude: float, region_name: str | None) -> dict[str, Any]:
    weather = _fetch_weather(latitude=latitude, longitude=longitude)
    weather_source = "OpenMeteo"
    if weather is None:
        weather = _deterministic_weather_fallback(latitude=latitude, longitude=longitude)
        weather_source = "DeterministicFallback"

    distances = _fetch_open_wildfire_distances(latitude=latitude, longitude=longitude)
    wildfire_source = "EONET"
    if distances is None:
        distances = []
        wildfire_source = "Unavailable"
    min_distance_km = min(distances) if distances else None

    temp_factor = _clamp((weather["temperature_c"] - 10) / 35)
    humidity_factor = _clamp(1 - (weather["humidity_pct"] / 100))
    wind_factor = _clamp(weather["wind_speed_kph"] / 50)
    precipitation_factor = _clamp(1 - (weather["precipitation_mm"] / 10))
    wildfire_factor = _wildfire_proximity_score(min_distance_km)

    risk_level = _clamp(
        (0.30 * temp_factor)
        + (0.25 * humidity_factor)
        + (0.25 * wind_factor)
        + (0.10 * precipitation_factor)
        + (0.10 * wildfire_factor)
    )
    model_name = "GlobalRuleBasedV1"

    feature_map = {
        "latitude": latitude,
        "longitude": longitude,
        "month": float(datetime.now(timezone.utc).month),
        "temperature_c": weather["temperature_c"],
        "humidity_pct": weather["humidity_pct"],
        "wind_speed_kph": weather["wind_speed_kph"],
        "precipitation_mm": weather["precipitation_mm"],
        "nearest_open_wildfire_km": float(min_distance_km if min_distance_km is not None else 3000.0),
    }
    ml_prediction = _predict_with_trained_model(feature_map)
    if ml_prediction is not None:
        risk_level = _clamp((0.7 * ml_prediction) + (0.3 * risk_level))
        model_name = "GlobalHybridV1"

    risk_category = _risk_category(risk_level)

    confidence = 0.9
    if weather_source != "OpenMeteo":
        confidence -= 0.2
    if wildfire_source != "EONET":
        confidence -= 0.1
    if ml_prediction is not None:
        confidence += 0.05
    confidence = _clamp(confidence, 0.5, 0.95)

    return {
        "region_name": region_name or f"Region near {latitude:.2f}, {longitude:.2f}",
        "latitude": latitude,
        "longitude": longitude,
        "risk_level": risk_level,
        "risk_category": risk_category,
        "temperature": weather["temperature_c"],
        "humidity": weather["humidity_pct"],
        "wind_speed": weather["wind_speed_kph"],
        "precipitation": weather["precipitation_mm"],
        "vegetation_density": None,
        "vegetation_type": None,
        "soil_moisture": None,
        "prediction_model": model_name,
        "confidence_score": confidence,
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "weather_source": weather_source,
            "wildfire_source": wildfire_source,
            "nearest_open_wildfire_km": min_distance_km,
            "used_trained_model": ml_prediction is not None,
        },
    }
