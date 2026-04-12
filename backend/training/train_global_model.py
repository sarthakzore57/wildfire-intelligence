from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


FEATURE_COLUMNS = [
    "latitude",
    "longitude",
    "month",
    "temperature_c",
    "humidity_pct",
    "wind_speed_kph",
    "precipitation_mm",
    "nearest_open_wildfire_km",
]
TARGET_COLUMN = "risk_level"


def _iso_compact_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _sha256_of_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_registry(
    registry_path: Path,
    model_latest: Path,
    metadata_latest: Path,
    model_versioned: Path,
    metadata_versioned: Path,
    metrics: dict[str, float],
    dataset_path: Path,
    rows_used: int,
    feature_columns: list[str],
    target_column: str,
    model_type: str,
) -> None:
    registry = {
        "latest": {
            "model_path": str(model_latest),
            "metadata_path": str(metadata_latest),
            "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        },
        "history": [],
    }
    if registry_path.exists():
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            registry.setdefault("history", [])
        except Exception:
            registry = {"latest": {}, "history": []}

    registry["latest"] = {
        "model_path": str(model_latest),
        "metadata_path": str(metadata_latest),
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    registry["history"].append(
        {
            "versioned_model_path": str(model_versioned),
            "versioned_metadata_path": str(metadata_versioned),
            "trained_at_utc": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics,
            "dataset_path": str(dataset_path),
            "dataset_sha256": _sha256_of_file(dataset_path),
            "rows_used": rows_used,
            "feature_columns": feature_columns,
            "target_column": target_column,
            "model_type": model_type,
        }
    )
    registry["history"] = registry["history"][-25:]
    registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")


def train_model(input_csv: Path, model_output: Path, metadata_output: Path, seed: int) -> tuple[dict[str, float], int]:
    df = pd.read_csv(input_csv)

    missing = [col for col in FEATURE_COLUMNS + [TARGET_COLUMN] if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in dataset: {missing}")

    model_df = df[FEATURE_COLUMNS + [TARGET_COLUMN]].dropna().copy()
    if model_df.empty:
        raise ValueError("No usable rows found after dropping missing values.")

    x = model_df[FEATURE_COLUMNS]
    y = model_df[TARGET_COLUMN].clip(0, 1)

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=seed
    )

    model = HistGradientBoostingRegressor(
        learning_rate=0.06,
        max_depth=8,
        max_iter=450,
        min_samples_leaf=40,
        random_state=seed,
    )
    model.fit(x_train, y_train)

    y_pred = np.clip(model.predict(x_test), 0, 1)
    metrics = {
        "mae": float(mean_absolute_error(y_test, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
        "r2": float(r2_score(y_test, y_pred)),
    }

    model_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, model_output)
    metadata = {
        "model_type": "HistGradientBoostingRegressor",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "feature_columns": FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
        "rows_used": int(len(model_df)),
        "metrics": metrics,
    }
    metadata_output.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"Model written to: {model_output}")
    print(f"Metadata written to: {metadata_output}")
    print(f"Metrics: {metrics}")
    return metrics, int(len(model_df))


def main() -> None:
    parser = argparse.ArgumentParser(description="Train global fire-risk model from a CSV dataset.")
    parser.add_argument(
        "--input",
        type=str,
        default="training/data/global_bootstrap.csv",
        help="Input CSV path relative to backend/.",
    )
    parser.add_argument(
        "--model-output",
        type=str,
        default="app/models/trained/global_fire_risk_model.joblib",
        help="Model artifact path relative to backend/.",
    )
    parser.add_argument(
        "--metadata-output",
        type=str,
        default="app/models/trained/global_fire_risk_model.meta.json",
        help="Metadata JSON path relative to backend/.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument(
        "--registry-output",
        type=str,
        default="app/models/trained/model_registry.json",
        help="Model registry JSON path relative to backend/.",
    )
    parser.add_argument(
        "--versioned",
        action="store_true",
        help="Also write versioned model artifacts and update model registry.",
    )
    args = parser.parse_args()

    backend_root = Path(__file__).resolve().parent.parent
    input_csv = backend_root / args.input
    model_output = backend_root / args.model_output
    metadata_output = backend_root / args.metadata_output
    metrics, rows_used = train_model(
        input_csv=input_csv,
        model_output=model_output,
        metadata_output=metadata_output,
        seed=args.seed,
    )

    if not args.versioned:
        return

    registry_output = backend_root / args.registry_output
    timestamp = _iso_compact_now()
    versioned_model_output = model_output.with_name(f"{model_output.stem}_{timestamp}{model_output.suffix}")
    versioned_metadata_output = metadata_output.with_name(
        f"{metadata_output.stem}_{timestamp}{metadata_output.suffix}"
    )
    shutil.copy2(model_output, versioned_model_output)
    shutil.copy2(metadata_output, versioned_metadata_output)

    _write_registry(
        registry_path=registry_output,
        model_latest=model_output,
        metadata_latest=metadata_output,
        model_versioned=versioned_model_output,
        metadata_versioned=versioned_metadata_output,
        metrics=metrics,
        dataset_path=input_csv,
        rows_used=rows_used,
        feature_columns=FEATURE_COLUMNS,
        target_column=TARGET_COLUMN,
        model_type="HistGradientBoostingRegressor",
    )
    print(f"Versioned model written to: {versioned_model_output}")
    print(f"Versioned metadata written to: {versioned_metadata_output}")
    print(f"Model registry updated at: {registry_output}")


if __name__ == "__main__":
    main()
