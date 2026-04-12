from __future__ import annotations

import argparse
import math
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
EONET_EVENTS_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"


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

    if isinstance(coordinates, list) and len(coordinates) == 2 and all(isinstance(v, (int, float)) for v in coordinates):
        lon, lat = coordinates
        return float(lat), float(lon)

    if isinstance(coordinates, list) and coordinates and isinstance(coordinates[0], list):
        first = coordinates[0]
        if len(first) == 2 and all(isinstance(v, (int, float)) for v in first):
            lon, lat = first
            return float(lat), float(lon)
        if first and isinstance(first[0], list):
            inner = first[0]
            if len(inner) == 2 and all(isinstance(v, (int, float)) for v in inner):
                lon, lat = inner
                return float(lat), float(lon)
    return None


def _fetch_open_wildfire_points() -> list[tuple[float, float]]:
    params = {"status": "open", "category": "wildfires", "limit": 500}
    response = requests.get(EONET_EVENTS_URL, params=params, timeout=20)
    response.raise_for_status()
    events = response.json().get("events", [])

    points: list[tuple[float, float]] = []
    for event in events:
        for geometry in event.get("geometry", []):
            point = _extract_point_from_geometry(geometry)
            if point is not None:
                points.append(point)
    return points


def _nearest_wildfire_km(latitude: float, longitude: float, wildfire_points: list[tuple[float, float]]) -> float | None:
    if not wildfire_points:
        return None
    return min(_haversine_km(latitude, longitude, lat, lon) for lat, lon in wildfire_points)


def _fetch_weather(latitude: float, longitude: float) -> dict[str, float] | None:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
        "timezone": "auto",
    }
    response = requests.get(OPEN_METEO_URL, params=params, timeout=8)
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


def _fallback_weather(latitude: float, longitude: float, month: int) -> dict[str, float]:
    seasonal_wave = math.sin((month - 1) / 12 * 2 * math.pi)
    hemispheric_adjustment = seasonal_wave * (1 if latitude >= 0 else -1) * 6
    temperature_c = max(-10.0, min(48.0, 30 - (abs(latitude) * 0.4) + hemispheric_adjustment))
    humidity_pct = max(10.0, min(100.0, 70 - (temperature_c * 0.8)))
    wind_speed_kph = max(0.0, min(80.0, 10 + (abs(longitude) % 25)))
    precipitation_mm = max(0.0, min(20.0, 3 - ((abs(latitude) % 5) * 0.3)))
    return {
        "temperature_c": temperature_c,
        "humidity_pct": humidity_pct,
        "wind_speed_kph": wind_speed_kph,
        "precipitation_mm": precipitation_mm,
    }


def _weak_supervised_risk_label(
    temperature_c: float,
    humidity_pct: float,
    wind_speed_kph: float,
    precipitation_mm: float,
    nearest_open_wildfire_km: float | None,
) -> float:
    temp_factor = _clamp((temperature_c - 10) / 35)
    humidity_factor = _clamp(1 - (humidity_pct / 100))
    wind_factor = _clamp(wind_speed_kph / 50)
    precipitation_factor = _clamp(1 - (precipitation_mm / 10))

    if nearest_open_wildfire_km is None:
        wildfire_factor = 0.1
    elif nearest_open_wildfire_km <= 25:
        wildfire_factor = 1.0
    elif nearest_open_wildfire_km <= 100:
        wildfire_factor = 0.75
    elif nearest_open_wildfire_km <= 300:
        wildfire_factor = 0.5
    elif nearest_open_wildfire_km <= 800:
        wildfire_factor = 0.25
    else:
        wildfire_factor = 0.1

    return _clamp(
        (0.30 * temp_factor)
        + (0.25 * humidity_factor)
        + (0.25 * wind_factor)
        + (0.10 * precipitation_factor)
        + (0.10 * wildfire_factor)
    )


def _sample_global_point(rng: random.Random) -> tuple[float, float]:
    lat = rng.uniform(-60, 75)
    lon = rng.uniform(-180, 180)
    return lat, lon


def build_live_dataset(samples: int, sleep_ms: int, seed: int, allow_weather_fallback: bool) -> pd.DataFrame:
    rng = random.Random(seed)
    wildfire_points: list[tuple[float, float]] = []
    try:
        wildfire_points = _fetch_open_wildfire_points()
    except Exception:
        wildfire_points = []

    rows: list[dict[str, Any]] = []
    attempts = 0
    max_attempts = samples * 8
    month = datetime.now(timezone.utc).month

    while len(rows) < samples and attempts < max_attempts:
        attempts += 1
        latitude, longitude = _sample_global_point(rng)
        try:
            weather = _fetch_weather(latitude, longitude)
        except Exception:
            weather = None

        weather_source = "open-meteo"
        if weather is None:
            if allow_weather_fallback:
                weather = _fallback_weather(latitude=latitude, longitude=longitude, month=month)
                weather_source = "deterministic-fallback"
            else:
                if sleep_ms > 0:
                    time.sleep(sleep_ms / 1000)
                continue

        nearest_km = _nearest_wildfire_km(latitude, longitude, wildfire_points)
        risk_level = _weak_supervised_risk_label(
            temperature_c=weather["temperature_c"],
            humidity_pct=weather["humidity_pct"],
            wind_speed_kph=weather["wind_speed_kph"],
            precipitation_mm=weather["precipitation_mm"],
            nearest_open_wildfire_km=nearest_km,
        )
        risk_category = "High" if risk_level >= 0.7 else "Medium" if risk_level >= 0.4 else "Low"

        rows.append(
            {
                "latitude": latitude,
                "longitude": longitude,
                "month": month,
                "temperature_c": weather["temperature_c"],
                "humidity_pct": weather["humidity_pct"],
                "wind_speed_kph": weather["wind_speed_kph"],
                "precipitation_mm": weather["precipitation_mm"],
                "nearest_open_wildfire_km": nearest_km if nearest_km is not None else 3000.0,
                "risk_level": risk_level,
                "risk_category": risk_category,
                "label_source": "weak_supervision_live_weather_eonet",
                "weather_source": weather_source,
            }
        )
        if sleep_ms > 0:
            time.sleep(sleep_ms / 1000)

    if not rows:
        raise RuntimeError("No rows collected from live sources. Try smaller sample size or rerun.")
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect live global weather/fire features into a training CSV.")
    parser.add_argument("--samples", type=int, default=1000, help="Number of rows to collect.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for global sampling.")
    parser.add_argument("--sleep-ms", type=int, default=50, help="Delay between API calls in milliseconds.")
    parser.add_argument(
        "--no-weather-fallback",
        action="store_true",
        help="Disable deterministic weather fallback when live weather calls fail.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="training/data/global_live_dataset.csv",
        help="Output CSV path relative to backend/.",
    )
    args = parser.parse_args()

    backend_root = Path(__file__).resolve().parent.parent
    output_path = backend_root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = build_live_dataset(
        samples=args.samples,
        sleep_ms=args.sleep_ms,
        seed=args.seed,
        allow_weather_fallback=not args.no_weather_fallback,
    )
    df.to_csv(output_path, index=False)
    print(f"Live dataset written to: {output_path}")
    print(f"Rows collected: {len(df)}")


if __name__ == "__main__":
    main()
