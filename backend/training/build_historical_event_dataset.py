from __future__ import annotations

import argparse
import math
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests


EONET_WILDFIRES_URL = "https://eonet.gsfc.nasa.gov/api/v3/categories/wildfires"
OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


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
            nested = first[0]
            if len(nested) == 2 and all(isinstance(v, (int, float)) for v in nested):
                lon, lat = nested
                return float(lat), float(lon)
    return None


def _fetch_eonet_wildfires(start_date: str, end_date: str, limit: int) -> list[dict[str, Any]]:
    params = {
        "status": "all",
        "start": start_date,
        "end": end_date,
        "limit": limit,
    }
    response = requests.get(EONET_WILDFIRES_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json().get("events", [])


def _fetch_weather_for_day(latitude: float, longitude: float, date_str: str) -> dict[str, float] | None:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": date_str,
        "end_date": date_str,
        "daily": "temperature_2m_max,relative_humidity_2m_mean,wind_speed_10m_max,precipitation_sum",
        "timezone": "UTC",
    }
    response = requests.get(OPEN_METEO_ARCHIVE_URL, params=params, timeout=20)
    response.raise_for_status()
    daily = response.json().get("daily", {})
    if not daily:
        return None

    def _first(name: str) -> float | None:
        values = daily.get(name) or []
        if not values:
            return None
        value = values[0]
        return None if value is None else float(value)

    temperature_c = _first("temperature_2m_max")
    humidity_pct = _first("relative_humidity_2m_mean")
    wind_speed_kph = _first("wind_speed_10m_max")
    precipitation_mm = _first("precipitation_sum")
    if None in {temperature_c, humidity_pct, wind_speed_kph, precipitation_mm}:
        return None

    return {
        "temperature_c": temperature_c,
        "humidity_pct": humidity_pct,
        "wind_speed_kph": wind_speed_kph,
        "precipitation_mm": precipitation_mm,
    }


def _collect_positive_rows(events: list[dict[str, Any]], sleep_ms: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event in events:
        for geometry in event.get("geometry", []):
            point = _extract_point_from_geometry(geometry)
            if point is None:
                continue
            latitude, longitude = point
            date_text = geometry.get("date")
            if not date_text:
                continue
            date_str = date_text[:10]
            try:
                weather = _fetch_weather_for_day(latitude=latitude, longitude=longitude, date_str=date_str)
            except Exception:
                weather = None
            if weather is None:
                if sleep_ms > 0:
                    time.sleep(sleep_ms / 1000)
                continue

            event_date = datetime.fromisoformat(date_text.replace("Z", "+00:00"))
            rows.append(
                {
                    "event_id": event.get("id"),
                    "event_title": event.get("title"),
                    "label": 1,
                    "latitude": latitude,
                    "longitude": longitude,
                    "month": event_date.month,
                    "date": date_str,
                    "temperature_c": weather["temperature_c"],
                    "humidity_pct": weather["humidity_pct"],
                    "wind_speed_kph": weather["wind_speed_kph"],
                    "precipitation_mm": weather["precipitation_mm"],
                }
            )
            if sleep_ms > 0:
                time.sleep(sleep_ms / 1000)
    return rows


def _nearest_event_distance_km(latitude: float, longitude: float, date_str: str, positive_rows: list[dict[str, Any]]) -> float:
    same_day = [row for row in positive_rows if row["date"] == date_str]
    pool = same_day if same_day else positive_rows
    if not pool:
        return 3000.0
    return min(_haversine_km(latitude, longitude, row["latitude"], row["longitude"]) for row in pool)


def _build_negative_rows(positive_rows: list[dict[str, Any]], sleep_ms: int, negatives_per_positive: int, seed: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []

    for positive in positive_rows:
        for _ in range(negatives_per_positive):
            latitude = max(-60.0, min(75.0, positive["latitude"] + rng.uniform(-8, 8)))
            longitude = positive["longitude"] + rng.uniform(-8, 8)
            if longitude > 180:
                longitude -= 360
            if longitude < -180:
                longitude += 360

            # Keep negatives reasonably away from known wildfire point
            if _haversine_km(latitude, longitude, positive["latitude"], positive["longitude"]) < 150:
                latitude = max(-60.0, min(75.0, positive["latitude"] + rng.choice([-1, 1]) * rng.uniform(4, 10)))
                longitude = positive["longitude"] + rng.choice([-1, 1]) * rng.uniform(4, 10)

            try:
                weather = _fetch_weather_for_day(latitude=latitude, longitude=longitude, date_str=positive["date"])
            except Exception:
                weather = None
            if weather is None:
                if sleep_ms > 0:
                    time.sleep(sleep_ms / 1000)
                continue

            rows.append(
                {
                    "event_id": None,
                    "event_title": None,
                    "label": 0,
                    "latitude": latitude,
                    "longitude": longitude,
                    "month": positive["month"],
                    "date": positive["date"],
                    "temperature_c": weather["temperature_c"],
                    "humidity_pct": weather["humidity_pct"],
                    "wind_speed_kph": weather["wind_speed_kph"],
                    "precipitation_mm": weather["precipitation_mm"],
                }
            )
            if sleep_ms > 0:
                time.sleep(sleep_ms / 1000)
    return rows


def build_dataset(
    start_date: str,
    end_date: str,
    limit: int,
    negatives_per_positive: int,
    sleep_ms: int,
    seed: int,
) -> pd.DataFrame:
    events = _fetch_eonet_wildfires(start_date=start_date, end_date=end_date, limit=limit)
    positive_rows = _collect_positive_rows(events=events, sleep_ms=sleep_ms)
    if not positive_rows:
        raise RuntimeError("No positive wildfire rows could be collected from EONET/Open-Meteo.")

    negative_rows = _build_negative_rows(
        positive_rows=positive_rows,
        sleep_ms=sleep_ms,
        negatives_per_positive=negatives_per_positive,
        seed=seed,
    )

    all_rows = positive_rows + negative_rows
    for row in all_rows:
        row["nearest_open_wildfire_km"] = _nearest_event_distance_km(
            latitude=row["latitude"],
            longitude=row["longitude"],
            date_str=row["date"],
            positive_rows=positive_rows,
        )
        row["risk_level"] = 1.0 if row["label"] == 1 else _clamp(1 - (row["nearest_open_wildfire_km"] / 2000))

    df = pd.DataFrame(all_rows)
    return df[
        [
            "event_id",
            "event_title",
            "label",
            "date",
            "latitude",
            "longitude",
            "month",
            "temperature_c",
            "humidity_pct",
            "wind_speed_kph",
            "precipitation_mm",
            "nearest_open_wildfire_km",
            "risk_level",
        ]
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a historical wildfire training dataset from EONET and Open-Meteo.")
    parser.add_argument("--start-date", type=str, required=True, help="Inclusive start date in YYYY-MM-DD format.")
    parser.add_argument("--end-date", type=str, required=True, help="Inclusive end date in YYYY-MM-DD format.")
    parser.add_argument("--limit", type=int, default=200, help="Max wildfire events to request from EONET.")
    parser.add_argument("--negatives-per-positive", type=int, default=1, help="Negative rows to generate per positive row.")
    parser.add_argument("--sleep-ms", type=int, default=0, help="Delay between weather API calls in milliseconds.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument(
        "--output",
        type=str,
        default="training/data/historical_wildfire_dataset.csv",
        help="Output CSV path relative to backend/.",
    )
    args = parser.parse_args()

    backend_root = Path(__file__).resolve().parent.parent
    output_path = backend_root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = build_dataset(
        start_date=args.start_date,
        end_date=args.end_date,
        limit=args.limit,
        negatives_per_positive=args.negatives_per_positive,
        sleep_ms=args.sleep_ms,
        seed=args.seed,
    )
    df.to_csv(output_path, index=False)
    print(f"Historical dataset written to: {output_path}")
    print(f"Rows: {len(df)}")
    print(f"Positive rows: {int(df['label'].sum())}")


if __name__ == "__main__":
    main()
