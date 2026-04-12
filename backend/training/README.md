# Global Model Training (Phase 2)

This folder contains the global-model pipeline used by the prediction API.

## Files

- `collect_live_global_dataset.py`: builds a live global dataset from Open-Meteo weather and NASA EONET wildfire proximity.
- `bootstrap_dataset.py`: builds a synthetic dataset for offline or fallback training.
- `build_historical_event_dataset.py`: builds a real labeled wildfire dataset from NASA EONET events plus Open-Meteo archive weather.
- `train_global_model.py`: trains the model and supports versioned model registry updates.

## Quick start

From `backend/`:

```bash
python -m pip install -r requirements.txt
python training/collect_live_global_dataset.py --samples 1000
python training/train_global_model.py --input training/data/global_live_dataset.csv --versioned
```

If live weather calls are unstable, the collector uses a deterministic weather fallback by default so dataset generation still completes.

## Historical real-data path

From `backend/`:

```bash
python training/build_historical_event_dataset.py --start-date 2025-01-01 --end-date 2025-12-31 --limit 200
python training/train_global_model.py --input training/data/historical_wildfire_dataset.csv --versioned
```

Or with one command:

```bash
python scripts/retrain_global_model.py --dataset-source historical --start-date 2025-01-01 --end-date 2025-12-31 --event-limit 200
```

## Artifacts

Latest runtime files:

- `app/models/trained/global_fire_risk_model.joblib`
- `app/models/trained/global_fire_risk_model.meta.json`
- `app/models/trained/model_registry.json`

Versioned files:

- `app/models/trained/global_fire_risk_model_<timestamp>.joblib`
- `app/models/trained/global_fire_risk_model.meta_<timestamp>.json`

The API loader reads `model_registry.json` first and falls back to the default latest paths if no registry is present.

## Required columns for custom CSV training

- `latitude`
- `longitude`
- `month`
- `temperature_c`
- `humidity_pct`
- `wind_speed_kph`
- `precipitation_mm`
- `nearest_open_wildfire_km`
- `risk_level`
