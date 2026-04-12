from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def _clamp(values: np.ndarray, min_value: float = 0.0, max_value: float = 1.0) -> np.ndarray:
    return np.clip(values, min_value, max_value)


def build_bootstrap_dataset(samples: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    latitude = rng.uniform(-60, 75, size=samples)
    longitude = rng.uniform(-180, 180, size=samples)
    month = rng.integers(1, 13, size=samples)

    season_wave = np.sin((month - 1) / 12 * 2 * np.pi)
    hemisphere_sign = np.where(latitude >= 0, 1.0, -1.0)
    seasonal_adjustment = season_wave * hemisphere_sign * 8.0

    base_temp = 34 - (np.abs(latitude) * 0.45)
    temperature_c = base_temp + seasonal_adjustment + rng.normal(0, 4, size=samples)
    temperature_c = np.clip(temperature_c, -10, 48)

    humidity_pct = 65 - (temperature_c * 0.7) + rng.normal(0, 12, size=samples)
    humidity_pct = np.clip(humidity_pct, 10, 100)

    wind_speed_kph = np.abs(rng.normal(18, 10, size=samples))
    wind_speed_kph = np.clip(wind_speed_kph, 0, 90)

    precipitation_mm = rng.gamma(shape=1.5, scale=2.0, size=samples)
    precipitation_mm = np.clip(precipitation_mm, 0, 40)

    nearest_open_wildfire_km = rng.exponential(scale=500, size=samples)
    nearest_open_wildfire_km = np.clip(nearest_open_wildfire_km, 0, 4000)

    temp_factor = _clamp((temperature_c - 10) / 35)
    humidity_factor = _clamp(1 - (humidity_pct / 100))
    wind_factor = _clamp(wind_speed_kph / 50)
    precipitation_factor = _clamp(1 - (precipitation_mm / 10))

    wildfire_factor = np.select(
        [
            nearest_open_wildfire_km <= 25,
            nearest_open_wildfire_km <= 100,
            nearest_open_wildfire_km <= 300,
            nearest_open_wildfire_km <= 800,
        ],
        [1.0, 0.75, 0.5, 0.25],
        default=0.1,
    )

    dry_season_bonus = _clamp((temperature_c - 20) / 20) * _clamp(1 - precipitation_mm / 6) * 0.08
    noise = rng.normal(0, 0.03, size=samples)
    risk_level = _clamp(
        (0.30 * temp_factor)
        + (0.25 * humidity_factor)
        + (0.25 * wind_factor)
        + (0.10 * precipitation_factor)
        + (0.10 * wildfire_factor)
        + dry_season_bonus
        + noise
    )

    risk_category = np.where(risk_level >= 0.7, "High", np.where(risk_level >= 0.4, "Medium", "Low"))

    return pd.DataFrame(
        {
            "latitude": latitude,
            "longitude": longitude,
            "month": month,
            "temperature_c": temperature_c,
            "humidity_pct": humidity_pct,
            "wind_speed_kph": wind_speed_kph,
            "precipitation_mm": precipitation_mm,
            "nearest_open_wildfire_km": nearest_open_wildfire_km,
            "risk_level": risk_level,
            "risk_category": risk_category,
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a bootstrap global fire-risk dataset.")
    parser.add_argument("--samples", type=int, default=50000, help="Number of rows to generate.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument(
        "--output",
        type=str,
        default="training/data/global_bootstrap.csv",
        help="Output CSV path relative to backend/.",
    )
    args = parser.parse_args()

    output_path = Path(__file__).resolve().parent.parent / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = build_bootstrap_dataset(samples=args.samples, seed=args.seed)
    df.to_csv(output_path, index=False)
    print(f"Bootstrap dataset written to: {output_path}")
    print(f"Rows: {len(df)}")


if __name__ == "__main__":
    main()
